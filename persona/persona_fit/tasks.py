"""Checked-in template tasks and generated per-decision tasks.

Template: ``persona/persona_fit/tasks/<slug>/``, filled with one
synthetic example row so the oracle and the contract tests can run.

Generated: one task folder per distinct task card under
``data/persona_fit/tasks/<slug>/`` (gitignored). ``tests/labels.json``
holds each persona's held-out decision keyed by persona id. The agent never
sees ``tests/``.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .paths import (
    GENERATED_TASKS,
    TASK_TEMPLATES,
    VERIFIER_SOURCE,
    persona_dir,
    rel,
    work_dir,
)
from .personas import example_persona, persona_file_id
from .prepare import Prepared
from .spec import DECISION_QID, Card, DatasetAdapter

TEST_SH = """#!/usr/bin/env bash
# Persona-fit ground-truth verifier: test_state.py writes reward.txt itself.
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/verifier_env.sh"

python3 "${TESTS_DIR}/test_state.py"
"""

VERIFIER_ENV_SH = """# Canonical verifier + tests path resolution (survey/chatbot/web test.sh).
#
# Production paths:
#   - Harbor / Playground trial: HARBOR_VERIFIER_DIR -> jobs/.../trial/verifier/
#   - Docker sandbox: default /logs/verifier (mounted, then collected to trial/)
#
# Do not fall back to <task-root>/verifier — that is local-dev leakage.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="${HARBOR_TESTS_DIR:-/tests}"
if [ ! -f "${TESTS_DIR}/test_state.py" ] && [ -f "${SCRIPT_DIR}/test_state.py" ]; then
  TESTS_DIR="${SCRIPT_DIR}"
fi
VERIFIER_DIR="${HARBOR_VERIFIER_DIR:-/logs/verifier}"
if ! mkdir -p "${VERIFIER_DIR}" 2>/dev/null; then
  echo "error: cannot create verifier directory: ${VERIFIER_DIR}" >&2
  echo "Set HARBOR_VERIFIER_DIR to jobs/<job>/<trial>/verifier for local harness runs." >&2
  exit 1
fi
mkdir -p "${VERIFIER_DIR}"
"""

SOLVE_SH = """#!/bin/bash
# Harness check only (no persona): first option / scale midpoint for every question.
set -euo pipefail
mkdir -p /app/output
cat > /app/output/survey_result.json <<'JSON'
{payload}
JSON
"""


def oracle_result(questionnaire: dict[str, Any]) -> dict[str, Any]:
    stamp = "2026-01-01T00:00:00Z"
    qid = questionnaire["id"]
    answers: list[dict[str, Any]] = []
    trajectory: list[dict[str, Any]] = [
        {"timestamp": stamp, "actor": "system", "action": "survey_started",
         "context": {"instrumentId": qid}, "outcome": {"status": "started"}}
    ]
    for q in questionnaire["questions"]:
        if q["type"] == "likert":
            value: Any = int((q.get("minValue", 1) + q.get("maxValue", 5)) // 2)
        else:
            value = q["options"][0]["id"]
        answers.append({"questionId": q["id"], "prompt": q["prompt"], "value": value})
        ctx = {"instrumentId": qid, "questionId": q["id"], "questionType": q["type"]}
        trajectory.append({"timestamp": stamp, "actor": "assistant", "action": "ask_question", "context": ctx, "outcome": {}})
        trajectory.append({"timestamp": stamp, "actor": "user", "action": "answer_question", "context": ctx,
                           "outcome": {"questionId": q["id"], "value": value}})
    trajectory.append({"timestamp": stamp, "actor": "system", "action": "survey_completed",
                       "context": {"instrumentId": qid}, "outcome": {"valid": True}})
    return {"instrument": {"id": qid, "title": questionnaire["title"]}, "answers": answers, "trajectory": trajectory}


def template_dir(adapter: DatasetAdapter) -> Path:
    return TASK_TEMPLATES / adapter.slug


def generated_root(adapter: DatasetAdapter) -> Path:
    return GENERATED_TASKS / adapter.slug


def instrument_id(adapter: DatasetAdapter, task_id: str | None = None) -> str:
    base = "persona_fit_{}".format(adapter.slug.replace("-", "_"))
    return base if task_id is None else "{}__{}".format(base, task_id)


def questionnaire_payload(adapter: DatasetAdapter, card: Card, task_id: str | None = None) -> dict[str, Any]:
    return {
        "schemaVersion": "1.0",
        "id": instrument_id(adapter, task_id),
        "title": adapter.title,
        "description": "Persona-fit decision task ({}). Answer as yourself.".format(adapter.title),
        "questions": card.questions,
    }


def task_toml(adapter: DatasetAdapter, task_id: str | None = None) -> str:
    name = "application/persona-fit-{}".format(adapter.slug)
    if task_id:
        name += "-" + task_id
    tags = ["persona-fit", "real-person", adapter.slug, "fit-a"]
    if adapter.stated_preference:
        tags.append("stated-preference")
    return "\n".join(
        [
            'version = "1.0"',
            'artifacts = [ "/app/output",]',
            "",
            "[task]",
            'name = "{}"'.format(name),
            "",
            "[metadata]",
            'difficulty = "easy"',
            'type = "survey"',
            'domain = "{}"'.format(adapter.domain),
            "tags = [ {} ]".format(", ".join('"{}"'.format(t) for t in tags)),
            "",
            "[verifier]",
            "timeout_sec = 120.0",
            "",
            "[agent]",
            "timeout_sec = 1800.0",
            "",
            "[environment]",
            'definition = "application/shared-survey-form"',
            "build_timeout_sec = 600.0",
            "cpus = 1",
            "memory_mb = 2048",
            "storage_mb = 10240",
            "gpus = 0",
            "",
        ]
    )


def card_options(card: Card) -> list[str]:
    question = next((q for q in card.questions if q["id"] == DECISION_QID), card.questions[0])
    return [str(o["id"]) for o in question.get("options") or []]


def question_options(question: dict[str, Any]) -> list[str]:
    return [str(option["id"]) for option in question.get("options") or []]


def label_spec(adapter: DatasetAdapter, card: Card) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "dataset": adapter.slug,
        "decisionType": adapter.decision_type,
        "metricKey": adapter.metric_key,
        "positiveOption": adapter.positive_option,
        "options": card_options(card),
    }
    items = [question for question in card.questions if question["id"] != DECISION_QID]
    if items and len(card.questions) == len(items):
        spec["options"] = []
        spec["optionSets"] = {question["id"]: question_options(question) for question in items}
    if adapter.decision_type == "rating":
        spec["ratingRange"] = list(adapter.rating_range)
    return spec


def item_entry(adapter: DatasetAdapter, row: pd.Series) -> dict[str, Any]:
    return {"rowId": str(row["row_id"]), "outcome": adapter.truth(row)}


def label_entry(adapter: DatasetAdapter, row: pd.Series) -> dict[str, Any]:
    return {"rowId": str(row["row_id"]), "outcome": adapter.truth(row)}


def persona_strategy(adapter: DatasetAdapter) -> dict[str, Any]:
    """The cohort is the dataset's own real people; jobs pair each with its own decisions."""
    sampling: dict[str, Any] = {"mode": "random"}
    if adapter.default_sample_rows is not None:
        sampling["sampleSize"] = adapter.default_sample_rows
    return {
        "schemaVersion": "1.0",
        "pool": rel(persona_dir(adapter.slug)),
        "cohortId": "persona-fit-{}".format(adapter.slug),
        "sources": ["persona-fit/{}".format(adapter.slug)],
        "dimensionFilters": {},
        "sampling": sampling,
    }


def write_task(
    adapter: DatasetAdapter,
    dest: Path,
    card: Card,
    labels: dict[str, dict[str, Any]],
    *,
    task_id: str | None,
    with_docs: bool,
) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "input").mkdir(exist_ok=True)
    (dest / "tests").mkdir(exist_ok=True)
    (dest / "task.toml").write_text(task_toml(adapter, task_id), encoding="utf-8")
    instruction = card.instruction_md.strip() or adapter.instruction_md.strip()
    (dest / "instruction.md").write_text(instruction + "\n", encoding="utf-8")
    context = card.context_md.strip()
    context_path = dest / "input" / "context.md"
    if context:
        context_path.write_text(context + "\n", encoding="utf-8")
    elif context_path.exists():
        context_path.unlink()
    questionnaire = questionnaire_payload(adapter, card, task_id)
    (dest / "input" / "questionnaire.yaml").write_text(
        yaml.safe_dump(questionnaire, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (dest / "persona_strategy.json").write_text(json.dumps(persona_strategy(adapter), indent=2) + "\n", encoding="utf-8")
    (dest / "reporting.json").write_text(json.dumps({"schemaVersion": "1.0", "contextRules": []}, indent=2) + "\n", encoding="utf-8")
    tests = dest / "tests"
    (tests / "test.sh").write_text(TEST_SH, encoding="utf-8")
    (tests / "test.sh").chmod(0o755)
    (tests / "verifier_env.sh").write_text(VERIFIER_ENV_SH, encoding="utf-8")
    shutil.copyfile(VERIFIER_SOURCE, tests / "test_state.py")
    payload = dict(label_spec(adapter, card), labels=labels)
    (tests / "labels.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    solution = dest / "solution"
    solution.mkdir(exist_ok=True)
    (solution / "solve.sh").write_text(
        SOLVE_SH.replace("{payload}", json.dumps(oracle_result(questionnaire), indent=2)), encoding="utf-8"
    )
    (solution / "solve.sh").chmod(0o755)
    if with_docs:
        (dest / "README.md").write_text(template_readme(adapter), encoding="utf-8")
    return dest


def template_readme(adapter: DatasetAdapter) -> str:
    lines = [
        "# Persona-fit: {} (sheet row {})".format(adapter.title, adapter.sheet_id),
        "",
        "Template task for one persona-fit dataset. The files here hold a single",
        "synthetic example row so the oracle and contract tests can run. Real tasks (one per",
        "distinct task card) are generated under `{}`.".format(rel(generated_root(adapter))),
        "",
        "- Persona: stable identity of the real person (`persona/datasets/persona-fit-{}`).".format(adapter.slug),
        "- Task card: `input/context.md` + `input/questionnaire.yaml` (the situation they saw).",
        "- Outcome: held out in `tests/labels.json`; the verifier rewards a match.",
        "",
        "Decision type: `{}`.{}".format(
            adapter.decision_type, " Stated preference (SP): not a market forecast." if adapter.stated_preference else ""
        ),
        "",
        "## Run",
        "",
        "```bash",
        "uv run python -m persona.persona_fit all --dataset {}".format(adapter.slug),
        "uv run python -m persona.persona_fit run --dataset {} --mode full".format(adapter.slug),
        "uv run python -m persona.persona_fit score --dataset {}".format(adapter.slug),
        "```",
        "",
        "See `docs/persona/persona-fit.md`.",
        "",
    ]
    return "\n".join(lines)


def build_template(adapter: DatasetAdapter) -> Path:
    examples = adapter.example_rows()
    row = examples.iloc[0]
    card = adapter.card(row)
    persona = example_persona(adapter, examples)
    labels = {persona["persona_id"]: label_entry(adapter, row)}
    dest = template_dir(adapter)
    write_task(adapter, dest, card, labels, task_id=None, with_docs=True)
    return dest


def card_key(adapter: DatasetAdapter, card: Card, row: pd.Series) -> str:
    blob = json.dumps(
        {"context": card.context_md, "instruction": card.instruction_md, "questions": card.questions},
        sort_keys=True,
    )
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]


def build_tasks(adapter: DatasetAdapter, prepared: Prepared, *, clean: bool = True) -> dict[str, Any]:
    """One task per distinct card among scored rows. Writes work/<slug>/tasks.json.

    Each person's task is written as soon as it is built, so memory holds one
    person at a time; a full dataset has hundreds of thousands of scored rows.
    """
    root = generated_root(adapter)
    if clean and root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    index: dict[str, Any] = {}
    for person_id, frame in prepared.scored.groupby("person_id", sort=False):
        person_id = str(person_id)
        rows = [row for _, row in frame.iterrows()]
        card = adapter.card(rows[0]) if len(rows) == 1 else adapter.form(rows)
        key = card_key(adapter, card, rows[0])
        pid = persona_file_id(adapter, person_id)
        if len(rows) == 1:
            label = label_entry(adapter, rows[0])
        else:
            label = {
                "rowId": str(rows[0]["row_id"]),
                "outcome": adapter.truth(rows[0]),
                "items": {question["id"]: item_entry(adapter, row) for question, row in zip(card.questions, rows)},
            }
        row_ids = [str(row["row_id"]) for row in rows]
        entry = index.get(key)
        if entry is None:
            dest = write_task(adapter, root / key, card, {pid: label}, task_id=key, with_docs=False)
            index[key] = {"path": rel(dest), "rows": row_ids, "persons": [person_id], "arm": label.get("arm")}
            continue
        labels_path = root / key / "tests" / "labels.json"
        payload = json.loads(labels_path.read_text(encoding="utf-8"))
        if pid in payload["labels"]:
            raise ValueError(
                "{}: person {} has two scored rows with an identical card; make the card distinct".format(
                    adapter.slug, person_id
                )
            )
        payload["labels"][pid] = label
        labels_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        entry["rows"].extend(row_ids)
        if person_id not in entry["persons"]:
            entry["persons"].append(person_id)
        entry["arm"] = entry["arm"] or label.get("arm")
    summary = {"dataset": adapter.slug, "taskCount": len(index), "tasks": index}
    out = work_dir(adapter.slug)
    out.mkdir(parents=True, exist_ok=True)
    (out / "tasks.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def load_task_index(adapter: DatasetAdapter) -> dict[str, Any]:
    path = work_dir(adapter.slug) / "tasks.json"
    if not path.is_file():
        raise FileNotFoundError("{}: run `tasks --dataset {}` first".format(adapter.slug, adapter.slug))
    return json.loads(path.read_text(encoding="utf-8"))
