"""Adapter contract shared by every persona-fit dataset.

An adapter turns one source file into a *decision frame*: one row per
decision with these standard columns, plus whatever raw columns the persona
and card read:

- ``row_id``      unique decision id (string)
- ``person_id``   the analysis unit that becomes one persona (string)
- ``cluster_id``  the unit to sample and bootstrap on (defaults to ``person_id``)
- ``outcome``     held-out decision: an option id, or an int for ratings

Persona attributes are dataset-local. Each adapter fixes its own attribute
names and value sets (``overlay_dimensions``) and keeps the source's original
labels; schema dimensions are filled only where the mapping is one-to-one.
Numeric attributes stay numeric and go into the persona's facts.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Literal

import pandas as pd

DecisionType = Literal["binary", "multinomial", "rating", "pair"]
TaskPath = Literal["application", "experiment"]

DECISION_QID = "decision"
PROBABILITY_QID = "probability"
PROB_MIN = 1
PROB_MAX = 99


@dataclass
class PersonaSpec:
    """``dimensions``: schema dims (one-to-one mappings only). ``overlays``: this
    dataset's own categorical attributes, original labels. ``facts``: numeric
    and free-text attributes, rendered as text."""

    display_name: str
    dimensions: dict[str, str] = field(default_factory=dict)
    overlays: dict[str, str] = field(default_factory=dict)
    facts: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class OverlayDim:
    """A dataset-local categorical attribute. ``values=()`` means the value set is
    taken from the data when the persona pool is built (no recoding)."""

    id: str
    label: str
    values: tuple[str, ...] = ()


@dataclass
class Card:
    """What the person sees for one decision. ``context_md`` lands in input/context.md.

    ``instruction_md`` overrides the adapter-wide instruction when the same
    dataset was fielded in more than one language.
    """

    context_md: str
    questions: list[dict[str, Any]]
    instruction_md: str = ""


@dataclass(frozen=True)
class RawFile:
    """One source file. ``url=None`` means a manual or gated download."""

    name: str
    url: str | None = None
    note: str = ""
    unzip: bool = False


class DatasetAdapter:
    slug: ClassVar[str]
    sheet_id: ClassVar[str]
    title: ClassVar[str]
    path: ClassVar[TaskPath]
    decision_type: ClassVar[DecisionType]
    domain: ClassVar[str] = "social-science"
    stated_preference: ClassVar[bool] = False

    raw_files: ClassVar[tuple[RawFile, ...]] = ()
    persona_fields: ClassVar[tuple[str, ...]] = ()
    card_fields: ClassVar[tuple[str, ...]] = ()
    leakage_fields: ClassVar[tuple[str, ...]] = ()
    overlay_dimensions: ClassVar[tuple[OverlayDim, ...]] = ()

    options: ClassVar[tuple[tuple[str, str], ...]] = ()
    positive_option: ClassVar[str | None] = None
    rating_range: ClassVar[tuple[int, int]] = (1, 5)
    metric_key: ClassVar[str] = "decision"
    instruction_md: ClassVar[str] = ""

    default_sample_rows: ClassVar[int] = 400
    seed: ClassVar[int] = 20261104

    # -- required per dataset -------------------------------------------------

    def load(self, raw: Path) -> pd.DataFrame:
        raise NotImplementedError

    def persona(self, person_rows: pd.DataFrame, history: pd.DataFrame | None = None) -> PersonaSpec:
        raise NotImplementedError

    def card(self, row: pd.Series) -> Card:
        raise NotImplementedError

    def form(self, rows: list[pd.Series]) -> Card:
        """One card for every scored row of one person. Default is a single decision."""
        if len(rows) != 1:
            raise ValueError("{}: {} scored rows share one person but form() is not implemented".format(self.slug, len(rows)))
        return self.card(rows[0])

    def example_rows(self) -> pd.DataFrame:
        """A few synthetic rows in decision-frame shape (template task + tests)."""
        raise NotImplementedError

    # -- defaults ---------------------------------------------------------------

    @property
    def template_name(self) -> str:
        if self.path == "application":
            return "survey_persona-fit-{}".format(self.slug)
        return "survey-persona-fit-{}".format(self.slug)

    @property
    def uses_history(self) -> bool:
        return False

    def eligible(self, frame: pd.DataFrame) -> pd.Series:
        """Rows that may be scored. Other rows can only feed persona history."""
        return pd.Series(True, index=frame.index)

    def truth(self, row: pd.Series) -> Any:
        value = row["outcome"]
        if self.decision_type == "rating":
            return int(value)
        return str(value)

    def check_columns(self, frame: pd.DataFrame, required: list[str] | tuple[str, ...], source: str) -> None:
        missing = [col for col in required if col not in frame.columns]
        if missing:
            raise ValueError(
                "{}: {} is missing columns {}. Found: {}".format(
                    self.slug, source, missing, sorted(frame.columns)[:60]
                )
            )

    def require_file(self, raw: Path, name: str) -> Path:
        path = raw / name
        if not path.is_file():
            entry = next((f for f in self.raw_files if f.name == name), None)
            hint = entry.note if entry and entry.note else ""
            if entry and entry.url:
                hint = "run `download --dataset {}`".format(self.slug)
            raise FileNotFoundError(
                "{}: expected {} ({})".format(self.slug, path, hint or "see raw_files")
            )
        return path


def overlay_id(slug: str, name: str) -> str:
    """Dataset-scoped overlay id, e.g. ``lpmc_car_ownership``."""
    return re.sub(r"[^a-z0-9_]", "_", "{}_{}".format(slug.split("-")[0], name).lower())


def coded_overlay(slug: str, name: str, label: str, codes: dict[int, str]) -> OverlayDim:
    return OverlayDim(overlay_id(slug, name), label, tuple(codes.values()))


# -- questionnaire helpers ------------------------------------------------------


def probability_question(prompt: str, question_id: str = PROBABILITY_QID) -> dict[str, Any]:
    return {
        "id": question_id,
        "prompt": prompt,
        "type": "likert",
        "construct": question_id,
        "required": True,
        "minValue": PROB_MIN,
        "maxValue": PROB_MAX,
    }


def choice_question(
    prompt: str,
    options: tuple[tuple[str, str], ...] | list[tuple[str, str]],
    question_id: str = DECISION_QID,
) -> dict[str, Any]:
    return {
        "id": question_id,
        "prompt": prompt,
        "type": "single_choice",
        "construct": question_id,
        "required": True,
        "options": [{"id": oid, "label": label} for oid, label in options],
    }


def binary_questions(
    prompt: str,
    options: tuple[tuple[str, str], ...],
    probability_prompt: str,
) -> list[dict[str, Any]]:
    return [choice_question(prompt, options), probability_question(probability_prompt)]


def rating_question(prompt: str, low: int, high: int) -> dict[str, Any]:
    return {
        "id": DECISION_QID,
        "prompt": prompt,
        "type": "likert",
        "construct": "decision",
        "required": True,
        "minValue": low,
        "maxValue": high,
    }


def read_delimited(path: Path, **kwargs: Any) -> pd.DataFrame:
    """Dataverse ``.tab`` downloads are sometimes comma-separated; sniff the header."""
    with path.open("r", encoding=kwargs.get("encoding", "utf-8"), errors="replace") as handle:
        header = handle.readline()
    sep = "\t" if header.count("\t") > header.count(",") else ","
    return pd.read_csv(path, sep=sep, low_memory=False, **kwargs)


def read_table_any(adapter: "DatasetAdapter", raw: Path, stem: str) -> pd.DataFrame:
    """``<stem>.tab`` (Dataverse tab-delimited export) or ``<stem>.dta`` (original Stata file)."""
    for suffix in (".tab", ".csv", ".dta"):
        path = raw / (stem + suffix)
        if path.is_file():
            if suffix == ".dta":
                return pd.read_stata(path, convert_categoricals=False)
            return read_delimited(path)
    return read_delimited(adapter.require_file(raw, stem + ".tab"))


# -- formatting helpers ---------------------------------------------------------


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and not value.strip():
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def as_int(value: Any) -> int | None:
    if is_missing(value):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def as_float(value: Any) -> float | None:
    if is_missing(value):
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def code_label(mapping: dict[int, str], value: Any) -> str | None:
    code = as_int(value)
    if code is None:
        return None
    return mapping.get(code)






def bullet_lines(pairs: list[tuple[str, Any]]) -> str:
    """Markdown bullets, skipping missing values."""
    lines = []
    for label, value in pairs:
        if is_missing(value):
            continue
        lines.append("- **{}:** {}".format(label, value))
    return "\n".join(lines)
