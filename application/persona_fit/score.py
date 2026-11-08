"""Score persona runs against the held-out decisions.

Reads ``jobs/pf-<dataset>-<mode>-*/<trial>/verifier/structured_output.json``
for ``mode`` in ``full`` (persona rendered) and ``none`` (persona-free
control), reports metrics per run against the observed decisions, and the
full-minus-none difference on the rows both runs answered, with a bootstrap
over persons (households for Gerber).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from . import metrics as M
from .paths import REPO_ROOT, RESULTS_ROOT
from .prepare import load_prepared
from .spec import DECISION_QID, DatasetAdapter

MODES = ("full", "none")
HIGHER_IS_BETTER = {"auc": True, "accuracy": True, "rmse": False}


def job_glob(adapter: DatasetAdapter, mode: str) -> str:
    return "pf-{}-{}-*".format(adapter.slug, mode)


def _realign_form(trial_dir: Path, block: dict[str, Any], frame: pd.DataFrame) -> list[dict[str, Any]] | None:
    """Pair each submitted answer with the question shown, not the stored key.

    A form can be sorted for display while its stored item results keep the
    frame's original order. The submitted survey is the source of what the
    model answered; the decision frame is the source of the right answer.
    """
    items = block.get("items") or []
    if not items or "person_id" not in frame.columns:
        return None
    survey = trial_dir / "artifacts" / "app" / "output" / "survey_result.json"
    if not survey.is_file():
        return None
    try:
        answers = json.loads(survey.read_text(encoding="utf-8")).get("answers") or []
    except (OSError, json.JSONDecodeError):
        return None
    answers = [a for a in answers if isinstance(a, dict) and a.get("questionId")]
    answers.sort(key=lambda a: str(a["questionId"]))
    pid = str(items[0].get("rowId") or "").split("-", 1)[0]
    rows = frame[frame["person_id"].astype(str) == pid].sort_values("item_id")
    if len(answers) != len(rows):
        return None
    from .verifier.ground_truth import item_credit

    aligned = []
    for answer, (_, row) in zip(answers, rows.iterrows()):
        options = row.get("item_options")
        n_options = len(options) if isinstance(options, (list, tuple)) else 0
        predicted = answer.get("value", answer.get("response"))
        predicted = None if predicted is None else str(predicted)
        aligned.append({
            "rowId": str(row["row_id"]),
            "valid": predicted is not None,
            "prediction": predicted,
            "truth": str(row["outcome"]),
            "correct": item_credit(predicted, str(row["outcome"]), n_options),
        })
    return aligned


def collect_trials(adapter: DatasetAdapter, mode: str, jobs_dir: Path | None = None) -> pd.DataFrame:
    root = jobs_dir or (REPO_ROOT / "jobs")
    frame = pd.DataFrame()
    if adapter.decision_type == "multinomial":
        try:
            frame = load_prepared(adapter).frame
        except (FileNotFoundError, OSError):
            frame = pd.DataFrame()
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("{}/*/verifier/structured_output.json".format(job_glob(adapter, mode)))):
        try:
            block = json.loads(path.read_text(encoding="utf-8")).get("personaFit") or {}
        except (OSError, json.JSONDecodeError):
            continue
        trial = str(path.parent.parent.relative_to(root))
        mtime = path.stat().st_mtime
        blocks = []
        aligned = _realign_form(path.parent.parent, block, frame)
        for item in aligned if aligned is not None else (block.get("items") or []):
            if not item.get("rowId"):
                continue
            blocks.append({
                "rowId": item["rowId"],
                "valid": item.get("valid"),
                "prediction": item.get("prediction"),
                "truth": item.get("truth"),
                "correct": item.get("correct"),
            })
        if not blocks and block.get("rowId") is not None:
            blocks.append(block)
        for one in blocks:
            one["_mtime"] = mtime
            one["_trial"] = trial
            previous = records.get(str(one["rowId"]))
            if previous is None or previous["_mtime"] < mtime:
                records[str(one["rowId"])] = one
    if not records:
        return pd.DataFrame()
    return pd.DataFrame.from_dict(records, orient="index").rename_axis("row_id").reset_index()


def _options_for_row(adapter: DatasetAdapter, row: pd.Series) -> list[str]:
    if adapter.options:
        return [oid for oid, _ in adapter.options]
    options = row.get("item_options")
    if isinstance(options, (list, tuple)) and options:
        return ["o{}".format(i + 1) for i in range(len(options))]
    question = next(q for q in adapter.card(row).questions if q["id"] == DECISION_QID)
    return [o["id"] for o in question.get("options") or []]


def persona_predictions(adapter: DatasetAdapter, scored: pd.DataFrame, trials: pd.DataFrame) -> pd.DataFrame:
    """Normalize verifier output: ``p_positive`` / ``proba`` / ``pred`` per row_id."""
    merged = scored.merge(trials, on="row_id", how="inner", suffixes=("", "_trial"))
    merged = merged[merged["valid"].fillna(False).astype(bool)]
    out = pd.DataFrame(index=merged["row_id"].to_numpy())
    if adapter.decision_type in {"binary", "pair"}:
        positive = str(adapter.positive_option)
        hard = (merged["prediction"].astype(str) == positive).astype(float).to_numpy()
        stated_col = (
            merged["probability_positive"]
            if "probability_positive" in merged.columns
            else pd.Series(float("nan"), index=merged.index)
        )
        stated = pd.to_numeric(stated_col, errors="coerce").to_numpy(dtype=float)
        out["p_positive"] = np.where(np.isnan(stated), np.where(hard == 1, 0.9, 0.1), stated)
        out["pred"] = merged["prediction"].astype(str).to_numpy()
    elif adapter.decision_type == "multinomial":
        probas = []
        if "confidence" in merged.columns:
            conf = pd.to_numeric(merged["confidence"], errors="coerce")
        else:
            conf = pd.Series(float("nan"), index=merged.index)
        for (_, row), c in zip(merged.iterrows(), conf):
            opts = _options_for_row(adapter, row)
            k = max(2, len(opts))
            c = (1 + 1 / k) / 2 if pd.isna(c) else float(c)
            rest = (1 - c) / (k - 1)
            probas.append({o: (c if o == str(row["prediction"]) else rest) for o in opts})
        out["proba"] = probas
        out["pred"] = merged["prediction"].astype(str).to_numpy()
        if "correct" in merged.columns:
            out["correct"] = pd.to_numeric(merged["correct"], errors="coerce").to_numpy(dtype=float)
    else:
        out["pred"] = pd.to_numeric(merged["prediction"], errors="coerce").to_numpy(dtype=float)
    return out


def _metrics_for(adapter: DatasetAdapter, rows: pd.DataFrame, preds: pd.DataFrame) -> dict:
    preds = preds.loc[rows["row_id"]]
    if adapter.decision_type in {"binary", "pair"}:
        y = (rows["outcome"].astype(str) == str(adapter.positive_option)).astype(int).to_numpy()
        pred_pos = (preds["pred"].astype(str) == str(adapter.positive_option)).astype(int).to_numpy()
        return M.binary_metrics(y, preds["p_positive"].to_numpy(dtype=float), pred_pos)
    if adapter.decision_type == "multinomial":
        y, proba, pred = list(rows["outcome"].astype(str)), list(preds["proba"]), list(preds["pred"])
        result = M.multinomial_metrics(y, proba, pred)
        if "correct" in preds.columns:
            credit = pd.to_numeric(preds["correct"], errors="coerce")
            if credit.notna().any():
                result["exact_accuracy"] = result["accuracy"]
                result["accuracy"] = float(credit.fillna(0).mean())
        return result
    low, high = adapter.rating_range
    y = rows["outcome"].astype(float).to_numpy()
    return M.rating_metrics(y, np.clip(preds["pred"].to_numpy(dtype=float), low, high), rows["person_id"].to_numpy())


def _primary(adapter: DatasetAdapter) -> str:
    return {"binary": "auc", "pair": "auc", "multinomial": "accuracy", "rating": "rmse"}[adapter.decision_type]


def _delta_bootstrap(adapter: DatasetAdapter, rows: pd.DataFrame, a: pd.DataFrame, b: pd.DataFrame, n_boot: int) -> dict | None:
    key = _primary(adapter)
    rows = rows.reset_index(drop=True)

    def stat(idx: np.ndarray) -> float | None:
        sub = rows.iloc[idx]
        ma, mb = _metrics_for(adapter, sub, a), _metrics_for(adapter, sub, b)
        if ma.get(key) is None or mb.get(key) is None:
            return None
        return float(ma[key] - mb[key])

    result = M.cluster_bootstrap(rows["cluster_id"].to_numpy(), stat, n_boot=n_boot, seed=adapter.seed)
    if result is not None:
        result["metric"] = key
        result["higher_is_better"] = HIGHER_IS_BETTER[key]
    return result


def score_dataset(adapter: DatasetAdapter, *, n_boot: int = 500, jobs_dir: Path | None = None) -> dict:
    prepared = load_prepared(adapter)
    scored = prepared.scored.reset_index(drop=True)
    report: dict[str, Any] = {
        "dataset": adapter.slug,
        "title": adapter.title,
        "decisionType": adapter.decision_type,
        "statedPreference": adapter.stated_preference,
        "primaryMetric": _primary(adapter),
        "counts": prepared.manifest["counts"],
        "runs": {},
    }
    preds_by_mode: dict[str, pd.DataFrame] = {}
    for mode in MODES:
        trials = collect_trials(adapter, mode, jobs_dir)
        if trials.empty:
            report["runs"][mode] = {"trials": 0}
            continue
        preds = persona_predictions(adapter, scored, trials)
        preds_by_mode[mode] = preds
        rows = scored[scored["row_id"].isin(preds.index)]
        run: dict[str, Any] = {
            "trials": int(len(trials)),
            "validAnswers": int(len(preds)),
            "coverage": float(len(preds) / max(1, len(scored))),
            "metrics": _metrics_for(adapter, rows, preds) if len(rows) else {},
        }
        report["runs"][mode] = run
    if "full" in preds_by_mode and "none" in preds_by_mode:
        common = scored[scored["row_id"].isin(preds_by_mode["full"].index) & scored["row_id"].isin(preds_by_mode["none"].index)]
        if len(common) >= 10:
            report["fullMinusPersonaFree"] = _delta_bootstrap(adapter, common, preds_by_mode["full"], preds_by_mode["none"], n_boot)
    report["verdict"] = verdict(report)
    write_report(adapter, report, scored, preds_by_mode)
    return report


def verdict(report: dict) -> str:
    if not (report["runs"].get("full") or {}).get("validAnswers"):
        return "no persona trials yet"
    if not (report["runs"].get("none") or {}).get("validAnswers"):
        return "scored against the observed decisions (no persona-free run to compare)"
    delta = report.get("fullMinusPersonaFree") or {}
    ci = delta.get("ci95")
    if not ci:
        return "too few rows shared with the persona-free run to compare"
    lo, hi = ci if delta.get("higher_is_better") else (-ci[1], -ci[0])
    if lo > 0:
        return "full persona beats the persona-free control (95% CI)"
    if hi < 0:
        return "full persona is worse than the persona-free control (95% CI)"
    return "no detectable difference from the persona-free control (CI includes 0)"


def write_report(adapter: DatasetAdapter, report: dict, scored: pd.DataFrame, preds_by_mode: dict[str, pd.DataFrame]) -> Path:
    out = RESULTS_ROOT / adapter.slug
    out.mkdir(parents=True, exist_ok=True)
    (out / "score.json").write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    table = scored[["row_id", "person_id", "cluster_id", "outcome"]].set_index("row_id")
    for mode, preds in preds_by_mode.items():
        cols = [c for c in ("pred", "p_positive") if c in preds.columns]
        table = table.join(preds[cols].add_prefix("persona_{}.".format(mode)), how="left")
    table.to_csv(out / "predictions.csv")
    (out / "score.md").write_text(render_markdown(report), encoding="utf-8")
    return out


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return "{:.4f}".format(value)
    return str(value)


def render_markdown(report: dict) -> str:
    key = report["primaryMetric"]
    lines = [
        "# {} ({})".format(report["title"], report["dataset"]),
        "",
        "Verdict: **{}**".format(report["verdict"]),
        "",
        "Primary metric: `{}`.{}".format(key, " Stated preference (SP)." if report["statedPreference"] else ""),
        "",
        "| Run | Valid answers | {} |".format(key),
        "| --- | --- | --- |",
    ]
    for mode, run in report["runs"].items():
        lines.append("| {} | {} | {} |".format(mode, run.get("validAnswers", 0), _fmt((run.get("metrics") or {}).get(key))))
    delta = report.get("fullMinusPersonaFree")
    if delta:
        ci = delta.get("ci95")
        lines += ["", "Full persona minus persona-free on shared rows: {} {}".format(
            _fmt(delta.get("estimate")), "[{:.4f}, {:.4f}]".format(*ci) if ci else "")]
    lines.append("")
    return "\n".join(lines)
