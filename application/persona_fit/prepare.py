"""Load a dataset and draw the scored sample.

The scored sample is the subset of rows that gets LLM trials: whole people, in
a seeded order. Only rows the adapter marks ``eligible`` can be drawn
(MovieLens keeps each user's earlier ratings as persona history). Deterministic
in the seed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .paths import raw_dir, work_dir
from .spec import DatasetAdapter

STANDARD_COLUMNS = ("row_id", "person_id", "cluster_id", "outcome")


@dataclass
class Prepared:
    frame: pd.DataFrame
    manifest: dict

    @property
    def scored(self) -> pd.DataFrame:
        return self.frame[self.frame["scored"]]

    @property
    def history(self) -> pd.DataFrame:
        """Rows that can never be scored; persona history for adapters that use it."""
        return self.frame[~self.frame["eligible"]]


def _rank_key(seed: int, value: object) -> str:
    return hashlib.sha256("{}:sample:{}".format(seed, value).encode("utf-8")).hexdigest()


def validate_frame(adapter: DatasetAdapter, frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    if "cluster_id" not in frame.columns:
        frame["cluster_id"] = frame["person_id"]
    adapter.check_columns(frame, STANDARD_COLUMNS, "decision frame")
    for col in ("row_id", "person_id", "cluster_id"):
        frame[col] = frame[col].astype(str)
    if frame["row_id"].duplicated().any():
        raise ValueError("{}: row_id must be unique".format(adapter.slug))
    frame = frame[frame["outcome"].notna()].reset_index(drop=True)
    if adapter.decision_type != "rating":
        frame["outcome"] = frame["outcome"].astype(str)
        allowed = {oid for oid, _ in adapter.options}
        if allowed:
            bad = sorted(set(frame["outcome"]) - allowed)
            if bad:
                raise ValueError("{}: outcomes {} are not option ids {}".format(adapter.slug, bad[:5], sorted(allowed)))
    leaked = [col for col in adapter.leakage_fields if col in adapter.persona_fields or col in adapter.card_fields]
    if leaked:
        raise ValueError("{}: leakage fields declared as persona/card fields: {}".format(adapter.slug, leaked))
    return frame


def draw_sample(
    adapter: DatasetAdapter,
    frame: pd.DataFrame,
    *,
    sample_rows: int,
    max_rows_per_person: int,
    skip_people: set[str] | None = None,
) -> pd.Series:
    """Boolean mask of scored rows: whole people, in a seeded order.

    One person answers every item they actually saw, in one sitting, so
    ``sample_rows`` is the number of people, not the number of items.
    ``skip_people`` drops people already scored, so a later draw is the next
    people in the same seeded order rather than a fresh top-N.
    ``max_rows_per_person`` is accepted for the CLI but no longer truncates:
    every remaining dataset is scored on the whole person.
    """
    del max_rows_per_person
    pool = frame[frame["eligible"]]
    held_out = {str(pid) for pid in (skip_people or ())}
    ranked = sorted(pool["person_id"].unique(), key=lambda pid: _rank_key(adapter.seed, pid))
    people = [pid for pid in ranked if str(pid) not in held_out][:sample_rows]
    return frame["person_id"].isin(people) & frame["eligible"]


def prepare(
    adapter: DatasetAdapter,
    *,
    raw: Path | None = None,
    sample_rows: int | None = None,
    max_rows_per_person: int = 10,
    skip_people: set[str] | None = None,
) -> Prepared:
    loaded = adapter.load(raw or raw_dir(adapter.slug))
    attrs = dict(loaded.attrs)
    frame = validate_frame(adapter, loaded)
    frame.attrs = attrs
    frame["eligible"] = adapter.eligible(frame).astype(bool).values
    frame["scored"] = draw_sample(
        adapter,
        frame,
        sample_rows=sample_rows or adapter.default_sample_rows,
        max_rows_per_person=max_rows_per_person,
        skip_people=skip_people,
    ).values
    manifest = {
        "dataset": adapter.slug,
        "sheetId": adapter.sheet_id,
        "title": adapter.title,
        "path": adapter.path,
        "decisionType": adapter.decision_type,
        "seed": adapter.seed,
        "sampleRows": sample_rows or adapter.default_sample_rows,
        "maxRowsPerPerson": max_rows_per_person,
        "skippedPeople": sorted(skip_people or ()),
        "createdAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "counts": {
            "rows": int(len(frame)),
            "persons": int(frame["person_id"].nunique()),
            "clusters": int(frame["cluster_id"].nunique()),
            "eligibleRows": int(frame["eligible"].sum()),
            "scoredRows": int(frame["scored"].sum()),
            "scoredPersons": int(frame.loc[frame["scored"], "person_id"].nunique()),
        },
        "personaFields": list(adapter.persona_fields),
        "cardFields": list(adapter.card_fields),
        "leakageFields": list(adapter.leakage_fields),
    }
    prepared = Prepared(frame, manifest)
    save(adapter, prepared)
    return prepared


def save(adapter: DatasetAdapter, prepared: Prepared) -> Path:
    out = work_dir(adapter.slug)
    out.mkdir(parents=True, exist_ok=True)
    prepared.frame.to_pickle(out / "decisions.pkl")
    (out / "manifest.json").write_text(json.dumps(prepared.manifest, indent=2) + "\n", encoding="utf-8")
    return out


def load_prepared(adapter: DatasetAdapter) -> Prepared:
    out = work_dir(adapter.slug)
    path = out / "decisions.pkl"
    if not path.is_file():
        raise FileNotFoundError("{}: run `prepare --dataset {}` first".format(adapter.slug, adapter.slug))
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    return Prepared(pd.read_pickle(path), manifest)
