"""Persona-fit ground-truth verifier (copied into each task as tests/test_state.py).

Reads the persona's ``survey_result.json``, looks up the held-out decision for
this persona in ``tests/labels.json`` (the agent never sees ``tests/``), writes
``reward.txt`` and a ``structured_output.json`` that the offline scorer reads.

Reward: 1/0 exact match for choices; ``1 - |error| / (max - min)`` for ratings.
Standard library only: this runs inside the trial container.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

DECISION_QID = "decision"
PROBABILITY_QID = "probability"


def output_dir() -> Path:
    return Path(
        os.environ.get("HARBOR_OUTPUT_DIR")
        or os.environ.get("MATRIX_OUTPUT_DIR")
        or "/app/output"
    )


def tests_dir() -> Path:
    explicit = os.environ.get("HARBOR_TESTS_DIR")
    if explicit and (Path(explicit) / "labels.json").is_file():
        return Path(explicit)
    return Path(__file__).resolve().parent


def verifier_dir() -> Path:
    explicit = os.environ.get("HARBOR_VERIFIER_DIR")
    if explicit:
        path = Path(explicit)
        path.mkdir(parents=True, exist_ok=True)
        return path
    container_default = Path("/logs/verifier")
    try:
        container_default.mkdir(parents=True, exist_ok=True)
        return container_default
    except OSError:
        pass
    raise RuntimeError(
        "HARBOR_VERIFIER_DIR is required when running outside a Harbor trial "
        "container. Point it at jobs/<job>/<trial>/verifier for local harness runs."
    )


def persona_id_from_trial() -> str | None:
    """The persona id the agent uploaded to /app/input/persona.yaml (also in persona-free mode)."""
    candidates = [output_dir().parent / "input" / "persona.yaml", Path("/app/input/persona.yaml")]
    for path in candidates:
        if not path.is_file():
            continue
        match = re.search(r"^persona_id:\s*['\"]?([^'\"\n]+?)['\"]?\s*$", path.read_text(encoding="utf-8"), re.M)
        if match:
            return match.group(1).strip()
    return None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def facet(key: str, label: str, role: str, kind: str, value: Any) -> dict[str, Any]:
    return {"key": key, "label": label, "role": role, "kind": kind, "value": value}


def score(spec: dict[str, Any], label: dict[str, Any], answers: dict[str, Any]) -> dict[str, Any]:
    decision_type = spec["decisionType"]
    raw_prediction = answers.get(DECISION_QID)
    truth = label["outcome"]
    result: dict[str, Any] = {"prediction": raw_prediction, "truth": truth}
    if decision_type == "rating":
        low, high = spec.get("ratingRange") or [1, 5]
        predicted = _number(raw_prediction)
        if predicted is None:
            result.update(valid=False, reward=0.0)
            return result
        error = abs(predicted - float(truth))
        result.update(
            valid=True,
            prediction=predicted,
            abs_error=error,
            correct=1.0 if round(predicted) == int(truth) else 0.0,
            reward=max(0.0, 1.0 - error / float(high - low)),
        )
        return result

    options = [str(o) for o in spec.get("options") or []]
    predicted = None if raw_prediction is None else str(raw_prediction)
    if predicted is None or (options and predicted not in options):
        result.update(valid=False, reward=0.0)
        return result
    correct = 1.0 if predicted == str(truth) else 0.0
    result.update(valid=True, prediction=predicted, correct=correct, reward=correct)

    stated = _number(answers.get(PROBABILITY_QID))
    if stated is not None:
        stated = min(max(stated / 100.0, 0.0), 1.0)
        if spec.get("positiveOption") is not None:
            result["probability_positive"] = stated
        else:
            result["confidence"] = stated
    return result


def _option_index(value: str) -> int | None:
    match = re.fullmatch(r"o(\d+)", value or "")
    if match is None:
        return None
    index = int(match.group(1))
    return index if index > 0 else None


def item_credit(predicted: str | None, truth: str, n_options: int) -> float:
    """Exact match, except an ordered scale allows the neighbouring step.

    Two to four options are treated as named choices: yes/no and a short list
    have no neighbouring answer. Five or more are the Likert scales, where
    one step off is half credit.
    """
    if predicted is None or predicted == "":
        return 0.0
    if predicted == truth:
        return 1.0
    if n_options < 5:
        return 0.0
    got = _option_index(predicted)
    wanted = _option_index(truth)
    if got is None or wanted is None or abs(got - wanted) != 1:
        return 0.0
    return 0.5


def item_results(spec: dict[str, Any], label: dict[str, Any], answers: dict[str, Any]) -> list[dict[str, Any]]:
    """One result per question on a multi-item card. Empty when the card has one decision."""
    items = label.get("items")
    if not isinstance(items, dict) or not items:
        return []
    if spec.get("decisionType") == "rating":
        low, high = spec.get("ratingRange") or [1, 5]
        span = float(high - low)
        results = []
        for qid, item in items.items():
            predicted = _number(answers.get(qid))
            truth = float(item.get("outcome"))
            valid = predicted is not None and low <= predicted <= high
            error = abs(predicted - truth) if valid else None
            results.append({
                "rowId": item.get("rowId"),
                "questionId": qid,
                "valid": valid,
                "prediction": predicted,
                "truth": truth,
                "abs_error": error,
                "correct": max(0.0, 1.0 - error / span) if valid else 0.0,
            })
        return results
    options = spec.get("optionSets") or {}
    results = []
    for qid, item in items.items():
        predicted = answers.get(qid)
        predicted = None if predicted is None else str(predicted)
        allowed = [str(option) for option in options.get(qid) or []]
        valid = predicted is not None and (not allowed or predicted in allowed)
        truth = str(item.get("outcome"))
        credit = item_credit(predicted, truth, len(allowed)) if valid else 0.0
        results.append({
            "rowId": item.get("rowId"),
            "questionId": qid,
            "valid": valid,
            "prediction": predicted,
            "truth": truth,
            "correct": credit,
        })
    return results


def build_structured_output(spec: dict[str, Any], label: dict[str, Any], persona_id: str, scored: dict[str, Any]) -> dict[str, Any]:
    metric = spec.get("metricKey") or "decision"
    numeric_pred = isinstance(scored.get("prediction"), (int, float)) and not isinstance(scored.get("prediction"), bool)
    facets = [
        facet("dataset", "Dataset", "evidence", "categorical", spec.get("dataset")),
        facet("persona_id", "Persona id", "evidence", "categorical", persona_id),
        facet("row_id", "Decision row id", "evidence", "categorical", label.get("rowId")),
        facet("prediction", "Persona decision", "primary", "numerical" if numeric_pred else "categorical", scored.get("prediction")),
        facet("truth", "Observed decision", "evidence", "numerical" if numeric_pred else "categorical", scored.get("truth")),
        facet("valid_answer", "Valid answer", "score", "numerical", 1 if scored.get("valid") else 0),
        facet("reward", "Reward", "score", "numerical", scored.get("reward", 0.0)),
    ]
    if "correct" in scored:
        facets.append(facet("correct", "Matches observed decision", "score", "numerical", scored["correct"]))
    if "abs_error" in scored:
        facets.append(facet("abs_error", "Absolute rating error", "score", "numerical", scored["abs_error"]))
    if "probability_positive" in scored:
        facets.append(facet("probability_positive", "Stated P(positive)", "score", "numerical", scored["probability_positive"]))
    if "confidence" in scored:
        facets.append(facet("confidence", "Stated confidence", "score", "numerical", scored["confidence"]))
    positive = spec.get("positiveOption")
    if positive is not None and scored.get("valid"):
        facets.append(facet(metric, "Predicted {}".format(metric), "primary", "numerical", 1 if scored["prediction"] == positive else 0))
        facets.append(facet("observed_{}".format(metric), "Observed {}".format(metric), "evidence", "numerical", 1 if str(label["outcome"]) == positive else 0))
    contexts = [
        {
            "key": "persona_fit.decision",
            "label": "Persona-fit decision",
            "contextType": "decision",
            "facets": [f for f in facets if f["value"] is not None],
        }
    ]
    fields = [
        dict(f, key="persona_fit.{}".format(f["key"]), group="persona_fit")
        for f in contexts[0]["facets"]
    ]
    return {
        "schemaVersion": "1.0",
        "artifactType": "matraix.trial_evaluation",
        "taskType": "survey",
        "presenceCheck": {"passed": True, "requiredArtifacts": ["survey_result.json"], "missingArtifacts": []},
        "sourceArtifacts": {"surveyResult": "/app/output/survey_result.json"},
        "personaFit": {
            "dataset": spec.get("dataset"),
            "decisionType": spec.get("decisionType"),
            "personaId": persona_id,
            "rowId": label.get("rowId"),
            "items": scored.get("items") or [],
            **{k: v for k, v in scored.items() if k != "items"},
        },
        "contexts": contexts,
        "fields": fields,
    }


def _write(name: str, text: str) -> None:
    (verifier_dir() / name).write_text(text, encoding="utf-8")


def main() -> int:
    spec = json.loads((tests_dir() / "labels.json").read_text(encoding="utf-8"))
    result_path = output_dir() / "survey_result.json"
    if not result_path.is_file():
        _write("reward.txt", "0\n")
        print("missing {}".format(result_path), file=sys.stderr)
        return 1
    try:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _write("reward.txt", "0\n")
        print("survey_result.json is not valid JSON: {}".format(exc), file=sys.stderr)
        return 1
    answers = {
        str(a.get("questionId") or a.get("id")): a.get("value", a.get("response"))
        for a in payload.get("answers") or []
        if isinstance(a, dict)
    }
    labels: dict[str, Any] = spec.get("labels") or {}
    persona_id = persona_id_from_trial()
    label = labels.get(persona_id) if persona_id else None
    if label is None and len(labels) == 1:
        persona_id, label = next(iter(labels.items()))
    if label is None:
        _write("reward.txt", "0\n")
        print("no label for persona {!r} in this task".format(persona_id), file=sys.stderr)
        return 1
    scored = score(spec, label, answers)
    items = item_results(spec, label, answers)
    if items:
        scored["items"] = items
        scored["reward"] = round(sum(item["correct"] for item in items) / len(items), 4)
    _write("structured_output.json", json.dumps(build_structured_output(spec, label, persona_id, scored), indent=2))
    _write("reward.txt", "{}\n".format(round(float(scored.get("reward", 0.0)), 4)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
