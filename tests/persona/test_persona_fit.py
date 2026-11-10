"""Persona-fit pipeline: leakage locks, templates, verifier, job pairing, splits."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")

REPO_ROOT = Path(__file__).resolve().parents[2]

from persona.persona_fit import tasks as pf_tasks  # noqa: E402
from persona.persona_fit.jobs import plan_blocks, prepare_shard, shard_needs_rerun, trial_needs_rerun  # noqa: E402
from persona.persona_fit.paths import VERIFIER_SOURCE  # noqa: E402
from persona.persona_fit.personas import pool_manifest, render_persona_yaml, schema_values  # noqa: E402
from persona.persona_fit.prepare import draw_sample, validate_frame  # noqa: E402
from persona.persona_fit.registry import ADAPTERS, all_adapters, get_adapter  # noqa: E402
from persona.persona_fit.adapters.ebnerd import _article_note, _engagement  # noqa: E402
from persona.persona_fit.spec import DECISION_QID, PROBABILITY_QID  # noqa: E402

SENTINEL = "ZZ_LEAK_SENTINEL_ZZ"
ADAPTER_IDS = list(ADAPTERS)


def _adapter(slug: str):
    return get_adapter(slug)


def test_registry_covers_the_five_datasets() -> None:
    adapters = all_adapters()
    assert len(adapters) == 5
    assert {a.slug for a in adapters} == set(ADAPTERS)
    assert {a.path for a in adapters} == {"application"}


@pytest.mark.parametrize("slug", ADAPTER_IDS)
def test_leakage_fields_are_not_persona_or_card_fields(slug: str) -> None:
    adapter = _adapter(slug)
    leaks = set(adapter.leakage_fields)
    assert leaks, "every adapter must declare its outcome-side columns"
    assert not leaks & set(adapter.persona_fields)
    assert not leaks & set(adapter.card_fields)


@pytest.mark.parametrize("slug", ADAPTER_IDS)
def test_overlays_are_dataset_scoped_and_render_original_labels(slug: str) -> None:
    adapter = _adapter(slug)
    ids = [o.id for o in adapter.overlay_dimensions]
    assert len(ids) == len(set(ids))
    assert not set(ids) & set(schema_values()), "overlay ids must not shadow schema dimensions"
    prefix = slug.split("-")[0].replace("-", "_") + "_"
    assert all(i.startswith(prefix) for i in ids)
    rows = adapter.example_rows()
    payload = render_persona_yaml(adapter, str(rows.iloc[0]["person_id"]), adapter.persona(rows.iloc[[0]]))
    manifest = pool_manifest(adapter, [payload], ["persona_x.yaml"])
    declared = {o["id"]: o for o in manifest["overlay_dimensions"]}
    for key, value in (payload.get("dimensions") or {}).items():
        if key in declared:
            assert value in declared[key]["values"]
        else:
            assert key in schema_values()


@pytest.mark.parametrize("slug", ADAPTER_IDS)
def test_leakage_values_do_not_reach_rendered_persona_or_card(slug: str) -> None:
    adapter = _adapter(slug)
    rows = adapter.example_rows().copy()
    for col in adapter.leakage_fields:
        rows[col] = SENTINEL
    persona = render_persona_yaml(adapter, str(rows.iloc[0]["person_id"]), adapter.persona(rows.iloc[[0]]))
    assert SENTINEL not in json.dumps(persona, default=str)
    for _, row in rows.iterrows():
        card = adapter.card(row)
        assert SENTINEL not in card.context_md
        assert SENTINEL not in json.dumps(card.questions)


@pytest.mark.parametrize("slug", ADAPTER_IDS)
def test_examples_validate_and_cards_have_the_decision(slug: str) -> None:
    adapter = _adapter(slug)
    rows = validate_frame(adapter, adapter.example_rows())
    for _, row in rows.iterrows():
        card = adapter.card(row)
        ids = [q["id"] for q in card.questions]
        if adapter.slug not in {"twin-2k-500", "immigration-conjoint", "bansak-asylum", "movielens-1m", "eb-nerd"}:
            assert ids[0] == DECISION_QID
        if adapter.decision_type in {"binary", "pair"} or (
            adapter.decision_type == "multinomial" and adapter.slug != "twin-2k-500"
        ):
            if adapter.slug not in {"immigration-conjoint", "bansak-asylum", "eb-nerd"}:
                assert PROBABILITY_QID in ids
        if adapter.slug == "twin-2k-500":
            assert ids == ["q001"]
            if adapter.slug in {"immigration-conjoint", "bansak-asylum", "movielens-1m"}:
                assert ids == ["q001"]
                assert PROBABILITY_QID not in ids
            if adapter.slug in {"immigration-conjoint", "bansak-asylum"}:
                options = pf_tasks.card_options(card)
                assert str(adapter.truth(row)) in options
                if adapter.options:
                    assert options == [oid for oid, _ in adapter.options]


@pytest.mark.parametrize("slug", ADAPTER_IDS)
def test_checked_in_template_is_in_sync(slug: str) -> None:
    adapter = _adapter(slug)
    task = pf_tasks.template_dir(adapter)
    assert task.is_dir(), f"run `run_persona_fit.py templates --dataset {slug}`"
    assert (task / "tests" / "test_state.py").read_text() == VERIFIER_SOURCE.read_text()
    labels = json.loads((task / "tests" / "labels.json").read_text())
    assert labels["dataset"] == slug and labels["labels"]
    assert (task / "input" / "questionnaire.yaml").is_file()


# -- verifier ---------------------------------------------------------------------


def _run_verifier(tmp_path: Path, labels: dict, answers: list[dict], persona_id: str | None) -> tuple[int, Path]:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_state.py").write_text(VERIFIER_SOURCE.read_text())
    (tests / "labels.json").write_text(json.dumps(labels))
    out = tmp_path / "app" / "output"
    out.mkdir(parents=True)
    (out / "survey_result.json").write_text(json.dumps({"answers": answers, "trajectory": []}))
    if persona_id:
        (tmp_path / "app" / "input").mkdir()
        (tmp_path / "app" / "input" / "persona.yaml").write_text(f"persona_id: '{persona_id}'\nversion: '1.0'\n")
    verifier = tmp_path / "verifier"
    env = {"MATRIX_OUTPUT_DIR": str(out), "HARBOR_VERIFIER_DIR": str(verifier), "HARBOR_TESTS_DIR": str(tests), "PATH": "/usr/bin:/bin"}
    code = subprocess.call([sys.executable, str(tests / "test_state.py")], env=env)
    return code, verifier


BINARY = {
    "dataset": "x", "decisionType": "binary", "metricKey": "visit", "positiveOption": "yes", "options": ["yes", "no"],
    "labels": {"x-1": {"rowId": "r1", "outcome": "yes", "arm": "sms"}, "x-2": {"rowId": "r2", "outcome": "no", "arm": "sms"}},
}


def test_verifier_rewards_a_match_and_reports_probability(tmp_path: Path) -> None:
    answers = [{"questionId": "decision", "value": "yes"}, {"questionId": "probability", "value": 80}]
    code, verifier = _run_verifier(tmp_path, BINARY, answers, "x-1")
    assert code == 0
    assert (verifier / "reward.txt").read_text().strip() == "1.0"
    block = json.loads((verifier / "structured_output.json").read_text())["personaFit"]
    assert block["rowId"] == "r1" and block["probability_positive"] == pytest.approx(0.8)


def test_verifier_uses_persona_id_to_pick_the_label(tmp_path: Path) -> None:
    answers = [{"questionId": "decision", "value": "yes"}, {"questionId": "probability", "value": 60}]
    code, verifier = _run_verifier(tmp_path, BINARY, answers, "x-2")
    assert code == 0
    assert (verifier / "reward.txt").read_text().strip() == "0.0"


def test_verifier_fails_without_a_label_for_this_persona(tmp_path: Path) -> None:
    code, verifier = _run_verifier(tmp_path, BINARY, [{"questionId": "decision", "value": "yes"}], "someone-else")
    assert code == 1
    assert (verifier / "reward.txt").read_text().strip() == "0"


def test_scale_item_allows_one_neighbouring_step() -> None:
    from persona.persona_fit.verifier.ground_truth import item_credit

    assert item_credit("o3", "o4", 5) == 0.5
    assert item_credit("o4", "o4", 5) == 1.0
    assert item_credit("o1", "o4", 5) == 0.0
    assert item_credit("o1", "o2", 2) == 0.0
    assert item_credit(None, "o4", 7) == 0.0


def test_bansak_form_is_one_person_five_pairs() -> None:
    adapter = _adapter("bansak-asylum")
    rows = adapter.example_rows().copy()
    base = rows.iloc[0].to_dict()
    five = pd.DataFrame([{**base, "pair_no": i, "row_id": "R_example-{}".format(i), "outcome": "a" if i % 2 else "b"} for i in range(1, 6)])
    as_rows = [row for _, row in five.iterrows()]
    card = adapter.form(as_rows)
    assert [q["id"] for q in card.questions] == ["q001", "q002", "q003", "q004", "q005"]
    assert card.context_md.count("## Paar ") == 5
    assert "1-99" not in card.context_md and "1-99" not in json.dumps(card.questions)
    assert "fließend Deutsch" in card.context_md
    assert card.instruction_md.startswith("# Entscheidung über einen Asylantrag")
    assert [option["id"] for option in card.questions[0]["options"]] == ["a", "b"]
    danish = five.copy()
    danish["cty"] = "Denmark"
    danish_card = adapter.form([row for _, row in danish.iterrows()])
    assert "Taler flydende dansk" in danish_card.context_md
    swiss = five.copy()
    swiss["cty"] = "Switzerland"
    swiss_card = adapter.form([row for _, row in swiss.iterrows()])
    assert swiss_card.instruction_md.startswith("# Asylum application choice")
    assert "the local language" in swiss_card.context_md
    frame = validate_frame(adapter, five)
    frame["eligible"] = True
    mask = draw_sample(adapter, frame, sample_rows=1, max_rows_per_person=1)
    assert int(mask.sum()) == 5
    spec = adapter.persona(five)
    text = " ".join(spec.facts)
    assert spec.display_name == "eine wahlberechtigte Person"
    assert "Sie sind in Germany geboren." in text
    assert "Wie viele Asylsuchende Ihr Land aufnehmen sollte" in text
    assert "Bündnis 90 / Die Grünen (Grüne)" in text
    assert "kodiert" not in text
    assert "Empathiefrage 1, von -6 bis 6: 2" in text and "Empathiefrage 2, von -6 bis 6: -1" in text
    assert "Tertiärbereich, Bachelor" in text and "Angestellt" in text
    # Schema values stay English so the shared catalog still validates.
    assert spec.dimensions["gender_identity"] == "Woman"
    assert spec.overlays["bansak_education"] == "Lower tertiary (bachelor's level)"


def test_immigration_form_is_one_person_five_pairs() -> None:
    adapter = _adapter("immigration-conjoint")
    rows = adapter.example_rows().copy()
    base = rows.iloc[0].to_dict()
    five = pd.DataFrame([{**base, "contest_no": i, "row_id": "99001-{}".format(i), "outcome": "a" if i % 2 else "b"} for i in range(1, 6)])
    as_rows = [row for _, row in five.iterrows()]
    card = adapter.form(as_rows)
    assert [q["id"] for q in card.questions] == ["q001", "q002", "q003", "q004", "q005"]
    assert card.context_md.count("## Pair ") == 5
    assert "1-99" not in card.context_md and "1-99" not in json.dumps(card.questions)
    frame = validate_frame(adapter, five)
    frame["eligible"] = True
    mask = draw_sample(adapter, frame, sample_rows=1, max_rows_per_person=1)
    assert int(mask.sum()) == 5
    skipped = draw_sample(adapter, frame, sample_rows=1, max_rows_per_person=1, skip_people={"99001"})
    assert int(skipped.sum()) == 0
    spec = adapter.persona(five)
    assert spec.overlays["immigration_state"] == "Illinois"
    assert spec.overlays["immigration_census_division"] == "East North Central"
    text = " ".join(spec.facts)
    assert "put on a show" in text and "You answered 2" in text
    assert "remain the same as it is" in text
    assert "Your occupation: teacher." in text


def test_verifier_scores_each_item_on_one_form(tmp_path: Path) -> None:
    labels = {
        "dataset": "twin-2k-500", "decisionType": "multinomial", "options": [],
        "optionSets": {"q001": ["o1", "o2"], "q002": ["o1", "o2", "o3", "o4", "o5"]},
        "labels": {"twin-2k-500-1": {
            "rowId": "1-a", "outcome": "o1",
            "items": {"q001": {"rowId": "1-a", "outcome": "o2"}, "q002": {"rowId": "1-b", "outcome": "o3"}},
        }},
    }
    answers = [{"questionId": "q001", "value": "o2"}, {"questionId": "q002", "value": "o4"}]
    code, verifier = _run_verifier(tmp_path, labels, answers, "twin-2k-500-1")
    assert code == 0
    assert float((verifier / "reward.txt").read_text()) == pytest.approx(0.75)
    items = json.loads((verifier / "structured_output.json").read_text())["personaFit"]["items"]
    assert [item["rowId"] for item in items] == ["1-a", "1-b"]
    assert [item["correct"] for item in items] == [1.0, 0.5]


def test_verifier_partial_credit_for_ratings(tmp_path: Path) -> None:
    labels = {"dataset": "m", "decisionType": "rating", "ratingRange": [1, 5], "options": [], "positiveOption": None,
              "labels": {"m-1": {"rowId": "r", "outcome": 4}}}
    code, verifier = _run_verifier(tmp_path, labels, [{"questionId": "decision", "value": 2}], None)
    assert code == 0
    assert float((verifier / "reward.txt").read_text()) == pytest.approx(0.5)


# -- jobs, splits, sampling ---------------------------------------------------------


def _trial(root: Path, name: str, *, exception: str | None, reward: float | None = 1.0) -> None:
    trial = root / name
    trial.mkdir()
    payload = {"trial_name": name, "exception_info": None}
    if exception is not None:
        payload["exception_info"] = {"exception_type": exception, "exception_message": "boom"}
    if reward is not None:
        payload["verifier_result"] = {"rewards": {"reward": reward}}
    (trial / "result.json").write_text(json.dumps(payload), encoding="utf-8")


def test_rerun_replaces_only_failed_trials(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from persona.persona_fit import jobs as pf_jobs

    shard = tmp_path / "pf-demo-full-0001"
    shard.mkdir()
    (shard / "config.json").write_text("{}", encoding="utf-8")
    (shard / "result.json").write_text(json.dumps({"n_total_trials": 4}), encoding="utf-8")
    _trial(shard, "ok", exception=None, reward=0.0)
    _trial(shard, "failed", exception="APIError")
    (shard / "incomplete").mkdir()
    monkeypatch.setattr(pf_jobs, "job_dir", lambda name: shard)

    needs, reason = shard_needs_rerun("pf-demo-full-0001")
    assert needs
    assert "failed" in reason and "incomplete" in reason and "1 missing" in reason
    assert trial_needs_rerun(shard / "ok") is False
    assert trial_needs_rerun(shard / "incomplete") is True

    assert prepare_shard("pf-demo-full-0001") == "resume"
    assert (shard / "ok" / "result.json").is_file()
    assert not (shard / "failed").exists()
    # No result.json yet: Harbor drops this itself on resume.
    assert (shard / "incomplete").is_dir()
    assert (shard / "config.json").is_file()
    assert shard_needs_rerun("pf-demo-full-0001")[0] is True

    (shard / "incomplete").rmdir()
    (shard / "result.json").write_text(json.dumps({"n_total_trials": 1}), encoding="utf-8")
    assert shard_needs_rerun("pf-demo-full-0001") == (False, "complete")


def test_plan_blocks_pairs_each_person_only_with_their_own_decisions() -> None:
    index = {"tasks": {
        "arm_a": {"path": "t/arm_a", "persons": ["p1", "p2", "p3"], "rows": ["r1", "r2", "r3"]},
        "d1": {"path": "t/d1", "persons": ["p4"], "rows": ["r4"]},
        "d2": {"path": "t/d2", "persons": ["p4"], "rows": ["r5"]},
        "d3": {"path": "t/d3", "persons": ["p5"], "rows": ["r6"]},
    }}
    blocks = plan_blocks(index, max_agents=2)
    real = {(p, e["path"]) for e in index["tasks"].values() for p in e["persons"]}
    produced = [(p, t) for persons, paths in blocks for p in persons for t in paths]
    assert sorted(produced) == sorted(real)
    assert max(len(persons) for persons, _ in blocks) <= 2


def test_sample_draws_whole_people_in_a_stable_order() -> None:
    adapter = _adapter("twin-2k-500")
    frame = pd.DataFrame({
        "row_id": [f"r{i}" for i in range(20)],
        "person_id": [f"p{i // 2}" for i in range(20)],
        "cluster_id": [f"p{i // 2}" for i in range(20)],
        "outcome": ["yes", "no"] * 10,
    })
    frame["eligible"] = True
    first = draw_sample(adapter, frame, sample_rows=3, max_rows_per_person=1)
    assert frame.loc[first, "person_id"].nunique() == 3
    assert int(first.sum()) == 6
    assert first.equals(draw_sample(adapter, frame, sample_rows=3, max_rows_per_person=1))
    held = set(frame.loc[first, "person_id"])
    nxt = draw_sample(adapter, frame, sample_rows=3, max_rows_per_person=1, skip_people=held)
    assert not set(frame.loc[nxt, "person_id"]) & held


def test_movielens_form_is_one_person_every_held_out_movie() -> None:
    adapter = _adapter("movielens-1m")
    rows = adapter.example_rows().copy()
    base = rows.iloc[0].to_dict()
    held = pd.DataFrame([
        {**base, "movie_id": 3, "movie_title": "Third", "timestamp": 30, "rating": 5, "outcome": 5},
        {**base, "movie_id": 1, "movie_title": "First", "timestamp": 10, "rating": 2, "outcome": 2},
    ])
    held["row_id"] = held["user_id"].astype(str) + "-" + held["movie_id"].astype(str)
    as_rows = [row for _, row in held.iterrows()]
    card = adapter.form(as_rows)
    assert [q["id"] for q in card.questions] == ["q001", "q002"]
    assert card.context_md.index("First") < card.context_md.index("Third")
    assert card.questions[0]["minValue"] == 1 and card.questions[0]["maxValue"] == 5
    frame = validate_frame(adapter, held)
    frame["eligible"] = True
    mask = draw_sample(adapter, frame, sample_rows=1, max_rows_per_person=1)
    assert int(mask.sum()) == 2


def test_verifier_scores_each_rating_on_one_form(tmp_path: Path) -> None:
    labels = {
        "dataset": "movielens-1m", "decisionType": "rating", "ratingRange": [1, 5], "options": [],
        "labels": {"movielens-1m-1": {
            "rowId": "1-a", "outcome": 4,
            "items": {"q001": {"rowId": "1-a", "outcome": 4}, "q002": {"rowId": "1-b", "outcome": 2}},
        }},
    }
    answers = [{"questionId": "q001", "value": 3}, {"questionId": "q002", "value": 2}]
    code, verifier = _run_verifier(tmp_path, labels, answers, "movielens-1m-1")
    assert code == 0
    assert float((verifier / "reward.txt").read_text()) == pytest.approx(0.875)
    items = json.loads((verifier / "structured_output.json").read_text())["personaFit"]["items"]
    assert [item["rowId"] for item in items] == ["1-a", "1-b"]
    assert items[0]["abs_error"] == pytest.approx(1)
    assert items[1]["correct"] == pytest.approx(1)


def test_movielens_persona_keeps_every_earlier_rating() -> None:
    adapter = _adapter("movielens-1m")
    rows = adapter.example_rows()
    history = pd.DataFrame([
        {"movie_title": "Old", "year": 1990, "outcome": 2, "timestamp": 1, "movie_id": 1},
        {"movie_title": "Middle", "year": 1992, "outcome": 5, "timestamp": 2, "movie_id": 2},
        {"movie_title": "New", "year": 1994, "outcome": 3, "timestamp": 3, "movie_id": 3},
    ])
    spec = adapter.persona(rows, history=history)
    line = next(fact for fact in spec.facts if fact.startswith("Movies you have rated"))
    assert line.index("Old") < line.index("Middle") < line.index("New")
    assert "2*" in line and "5*" in line and "3*" in line
    assert "You live in New York, New York County, New York." in spec.facts


def test_movielens_scores_only_the_latest_ratings() -> None:
    adapter = _adapter("movielens-1m")
    frame = pd.DataFrame({"person_id": ["u1"] * 10 + ["u2"] * 3, "timestamp": list(range(10)) + [5, 1, 9]})
    eligible = adapter.eligible(frame)
    assert eligible[:10].tolist() == [False] * 8 + [True] * 2
    assert eligible[10:].tolist() == [False, False, True]


def test_ebnerd_form_is_one_screen_and_labels_match_the_clicks() -> None:
    adapter = _adapter("eb-nerd")
    rows = adapter.example_rows().copy()
    first, second = (row.to_dict() for _, row in rows.iterrows())
    screen = pd.DataFrame([
        {**second, "position": 2, "title": "Second"},
        {**first, "position": 1, "title": "First"},
    ])
    screen["row_id"] = screen["impression_id"].astype(str) + "-" + screen["article_id"].astype(str)
    screen["outcome"] = screen["clicked"].map({True: "yes", False: "no"})
    as_rows = [row for _, row in screen.iterrows()]
    card = adapter.form(as_rows)
    as_rows.sort(key=lambda row: int(row["position"]))
    assert [q["id"] for q in card.questions] == ["q001", "q002"]
    prompts = [q["prompt"] for q in card.questions]
    assert "First" in prompts[0] and "Second" in prompts[1]
    assert "sektion sport" in prompts[0] and "Sen aften" in prompts[0]
    assert "Ville du åbne den?" in prompts[0]
    assert "kræver abonnement" in prompts[1] and "en video" in prompts[1]
    assert "udgivet 15 dage tidligere" in prompts[1]
    assert "Tekst:" not in prompts[0] and "billede" not in prompts[0]
    assert "kræver abonnement" not in prompts[0]
    assert card.context_md.strip() == "Skærmen er forsiden."
    assert PROBABILITY_QID not in [q["id"] for q in card.questions]
    assert [adapter.truth(row) for row in as_rows] == ["yes", "no"]
    frame = validate_frame(adapter, screen)
    frame["eligible"] = True
    assert int(draw_sample(adapter, frame, sample_rows=1, max_rows_per_person=1).sum()) == 2
    persona = adapter.persona(screen)
    text = " ".join(persona.facts)
    assert "sport: Danmark vinder" in text
    assert "på en telefon" in text
    assert "Det er maj 2023" in text and "Det er aften" not in text
    assert "Gammel sag" in text and "uden at åbne" in text
    assert "3 af de 40 artikler" in text and "På hver af skærmene åbnede du én artikel" in text
    assert "clicked" not in json.dumps(render_persona_yaml(adapter, "7", persona), default=str)
    assert _engagement(24, 72) == " (læst 24 sek, rullet 72%)"
    assert _engagement(0, None) == " (læst 0 sek)"
    assert _engagement(None, None) == ""
    locked = as_rows[0].copy()
    locked["premium"] = True
    locked["is_subscriber"] = False
    assert "som du ikke har" in _article_note(locked)
    locked["published_time"] = "2023-05-25 20:00:00"
    assert "dage tidligere" not in _article_note(locked)


def test_json_survey_reads_the_trial_task(tmp_path: Path) -> None:
    pytest.importorskip("harbor")
    pytest.importorskip("backend")
    from matraix.agents.persona.json_survey import _trial_task_path

    template = pf_tasks.template_dir(_adapter("twin-2k-500"))
    trial = tmp_path / "trial"
    trial.mkdir()
    (trial / "config.json").write_text(json.dumps({"task": {"path": str(template)}}))
    assert _trial_task_path(trial) == str(template)
    (trial / "config.json").write_text(json.dumps({"task": {"path": str(tmp_path)}}))
    assert _trial_task_path(trial) is None
    assert _trial_task_path(None) is None
