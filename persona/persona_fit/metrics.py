"""Metrics per decision type ("How to score" sheet) plus a person-clustered bootstrap.

numpy / pandas only.
"""

from __future__ import annotations

import math
from typing import Callable

import numpy as np
import pandas as pd

EPS = 1e-4


def _clip(p: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)


def auc(y: np.ndarray, p: np.ndarray) -> float | None:
    """Mann-Whitney AUC with average ranks for ties."""
    y = np.asarray(y, dtype=int)
    n_pos, n_neg = int(y.sum()), int(len(y) - y.sum())
    if n_pos == 0 or n_neg == 0:
        return None
    ranks = pd.Series(np.asarray(p, dtype=float)).rank(method="average").to_numpy()
    return float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def calibration_slope(y: np.ndarray, p: np.ndarray, iterations: int = 50) -> float | None:
    """Slope of a logistic regression of the outcome on logit(p) (1 = well calibrated)."""
    y = np.asarray(y, dtype=float)
    if len(y) < 20 or y.min() == y.max():
        return None
    x = np.log(_clip(p) / (1 - _clip(p)))
    if np.allclose(x, x[0]):
        return None
    beta = np.zeros(2)
    design = np.column_stack([np.ones_like(x), x])
    for _ in range(iterations):
        mu = 1 / (1 + np.exp(-design @ beta))
        w = mu * (1 - mu) + 1e-9
        step = np.linalg.solve(design.T @ (design * w[:, None]), design.T @ (y - mu))
        beta += step
        if np.max(np.abs(step)) < 1e-8:
            break
    return float(beta[1])


def binary_metrics(y: np.ndarray, p: np.ndarray, pred_positive: np.ndarray) -> dict:
    y = np.asarray(y, dtype=int)
    p = _clip(p)
    return {
        "n": int(len(y)),
        "accuracy": float(np.mean(np.asarray(pred_positive, dtype=int) == y)),
        "auc": auc(y, p),
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
        "calibration_slope": calibration_slope(y, p),
        "observed_rate": float(y.mean()),
        "predicted_rate": float(p.mean()),
        "rate_error_pp": float((p.mean() - y.mean()) * 100),
    }


def multinomial_metrics(y: list[str], proba: list[dict[str, float]], pred: list[str], weights: np.ndarray | None = None) -> dict:
    y_arr = np.asarray(y, dtype=object)
    pred_arr = np.asarray(pred, dtype=object)
    w = np.ones(len(y_arr)) if weights is None else np.asarray(weights, dtype=float)
    losses = np.array([-math.log(max(EPS, (pr or {}).get(t, 0.0))) for t, pr in zip(y, proba)])
    classes = sorted(set(y_arr) | set(c for c in pred_arr if c is not None))
    share_err = {
        str(c): float(
            np.average([(pr or {}).get(c, 0.0) for pr in proba], weights=w) - np.average(y_arr == c, weights=w)
        ) * 100
        for c in classes
    }
    return {
        "n": int(len(y_arr)),
        "weighted": weights is not None,
        "accuracy": float(np.average(pred_arr == y_arr, weights=w)),
        "log_loss": float(np.average(losses, weights=w)),
        "share_error_pp": share_err,
        "mean_abs_share_error_pp": float(np.mean([abs(v) for v in share_err.values()])) if share_err else None,
    }


def rating_metrics(y: np.ndarray, pred: np.ndarray, person: np.ndarray) -> dict:
    y = np.asarray(y, dtype=float)
    pred = np.asarray(pred, dtype=float)
    corrs = []
    frame = pd.DataFrame({"y": y, "p": pred, "person": person})
    for _, grp in frame.groupby("person"):
        if len(grp) >= 3 and grp["y"].std() > 0 and grp["p"].std() > 0:
            corrs.append(float(np.corrcoef(grp["y"], grp["p"])[0, 1]))
    return {
        "n": int(len(y)),
        "rmse": float(np.sqrt(np.mean((pred - y) ** 2))),
        "mae": float(np.mean(np.abs(pred - y))),
        "within_person_corr": float(np.mean(corrs)) if corrs else None,
        "persons_with_corr": len(corrs),
    }


def cluster_bootstrap(
    clusters: np.ndarray,
    stat: Callable[[np.ndarray], float | None],
    *,
    n_boot: int = 500,
    seed: int = 0,
) -> dict | None:
    """Percentile CI of ``stat(row_index_array)`` resampling whole clusters."""
    clusters = np.asarray(clusters)
    uniq, inverse = np.unique(clusters, return_inverse=True)
    members = [np.flatnonzero(inverse == k) for k in range(len(uniq))]
    rng = np.random.default_rng(seed)
    point = stat(np.arange(len(clusters)))
    if point is None:
        return None
    draws = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(uniq), len(uniq))
        value = stat(np.concatenate([members[k] for k in pick]))
        if value is not None and not math.isnan(value):
            draws.append(value)
    if len(draws) < n_boot // 2:
        return {"estimate": float(point), "ci95": None, "n_boot": len(draws)}
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {"estimate": float(point), "ci95": [float(lo), float(hi)], "n_boot": len(draws)}
