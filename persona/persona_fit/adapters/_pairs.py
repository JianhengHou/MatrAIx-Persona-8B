"""Shared helpers for two-profile conjoint choices (immigration, asylum)."""

from __future__ import annotations

import pandas as pd

from ..spec import Card, binary_questions

PAIR_OPTIONS_TEMPLATE = (("a", "{} 1"), ("b", "{} 2"))


def pair_options(noun: str) -> tuple[tuple[str, str], ...]:
    return tuple((oid, label.format(noun)) for oid, label in PAIR_OPTIONS_TEMPLATE)


def pair_table(noun: str, attributes: list[tuple[str, str, str]]) -> str:
    """Markdown table: (attribute label, value for profile 1, value for profile 2)."""
    lines = [
        "| | {} 1 | {} 2 |".format(noun, noun),
        "| --- | --- | --- |",
    ]
    for label, a, b in attributes:
        lines.append("| **{}** | {} | {} |".format(label, a, b))
    return "\n".join(lines)


def pair_card(noun: str, heading: str, table: str, prompt: str, probability_prompt: str) -> Card:
    context = "# {}\n\n{}\n".format(heading, table)
    return Card(context, binary_questions(prompt, pair_options(noun), probability_prompt))


def to_pairs(profiles: pd.DataFrame, pair_key: list[str], order_col: str, attrs: list[str], chosen_col: str) -> pd.DataFrame:
    """Collapse two profile rows per pair into one row with ``<attr>_a`` / ``<attr>_b``.

    ``outcome`` is ``a`` when the first profile (by ``order_col``) was chosen.
    Pairs without exactly one chosen profile are dropped.
    """
    profiles = profiles.sort_values(pair_key + [order_col])
    first = profiles.groupby(pair_key, sort=False).nth(0).set_index(pair_key)
    second = profiles.groupby(pair_key, sort=False).nth(1).set_index(pair_key)
    common = first.index.intersection(second.index)
    first, second = first.loc[common], second.loc[common]
    out = first.drop(columns=attrs + [chosen_col, order_col], errors="ignore").copy()
    for attr in attrs:
        out[attr + "_a"] = first[attr].to_numpy()
        out[attr + "_b"] = second[attr].to_numpy()
    ca = pd.to_numeric(first[chosen_col], errors="coerce").to_numpy()
    cb = pd.to_numeric(second[chosen_col], errors="coerce").to_numpy()
    out["outcome"] = None
    out.loc[(ca == 1) & (cb == 0), "outcome"] = "a"
    out.loc[(ca == 0) & (cb == 1), "outcome"] = "b"
    return out[out["outcome"].notna()].reset_index()
