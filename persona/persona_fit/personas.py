"""Write one persona YAML per scored person, plus the pool ``manifest.json``.

``dimensions`` holds schema dims (one-to-one mappings only) and the dataset's
own overlay attributes with their original labels. Numeric and free-text
attributes go into ``system_prompt``, which the persona template appends after
the dimension narrative. Unobserved attributes stay unset (no imputation).

The manifest declares the overlays (``overlay_dimensions``), which gives them
display labels when the persona is rendered and makes them filterable in
Playground.
"""

from __future__ import annotations

import json
import re
import shutil
from functools import lru_cache

import pandas as pd
import yaml

from .paths import REPO_ROOT, persona_dir, rel
from .prepare import Prepared
from .spec import DatasetAdapter, PersonaSpec

SCHEMA_PATH = REPO_ROOT / "persona" / "schema" / "dimensions.json"


@lru_cache(maxsize=1)
def schema_values() -> dict[str, tuple[str, ...]]:
    raw = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return {d["id"]: tuple(d.get("values") or ()) for d in raw["dimensions"]}


def persona_file_id(adapter: DatasetAdapter, person_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(person_id)).strip("-")
    return "{}-{}".format(adapter.slug, safe)


def validate_dimensions(adapter: DatasetAdapter, dims: dict[str, str]) -> dict[str, str]:
    values = schema_values()
    clean: dict[str, str] = {}
    for key, value in dims.items():
        if value is None:
            continue
        if key not in values:
            raise ValueError("{}: unknown schema dimension {!r}".format(adapter.slug, key))
        if values[key] and value not in values[key]:
            raise ValueError(
                "{}: {!r} is not a value of {} ({})".format(adapter.slug, value, key, list(values[key]))
            )
        clean[key] = value
    return clean


def validate_overlays(adapter: DatasetAdapter, overlays: dict[str, str]) -> dict[str, str]:
    declared = {o.id: o for o in adapter.overlay_dimensions}
    clean: dict[str, str] = {}
    for key, value in overlays.items():
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        if key not in declared:
            raise ValueError("{}: overlay {!r} is not declared in overlay_dimensions".format(adapter.slug, key))
        if key in schema_values():
            raise ValueError("{}: overlay {!r} collides with a schema dimension".format(adapter.slug, key))
        text = str(value)
        allowed = declared[key].values
        if allowed and text not in allowed:
            raise ValueError("{}: {!r} is not a declared value of overlay {} ({})".format(adapter.slug, text, key, list(allowed)))
        clean[key] = text
    return clean


def render_persona_yaml(adapter: DatasetAdapter, person_id: str, spec: PersonaSpec) -> dict:
    payload: dict = {
        "persona_id": persona_file_id(adapter, person_id),
        "version": "1.0",
        "source": "persona-fit/{}".format(adapter.slug),
        "display_name": spec.display_name,
    }
    dims = {**validate_dimensions(adapter, spec.dimensions), **validate_overlays(adapter, spec.overlays)}
    if dims:
        payload["dimensions"] = dims
    if spec.facts:
        payload["system_prompt"] = "More about you:\n" + "\n".join("- {}".format(f) for f in spec.facts)
    payload["provenance"] = {
        "dataset": adapter.slug,
        "sheet_id": adapter.sheet_id,
        "source_person_id": str(person_id),
        "persona_fields": list(adapter.persona_fields),
        "note": "Real-person record. Unobserved attributes are intentionally unset.",
    }
    return payload


class _BlockDumper(yaml.SafeDumper):
    pass


def _str_representer(dumper: yaml.SafeDumper, value: str) -> yaml.Node:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_BlockDumper.add_representer(str, _str_representer)


def dump_yaml(payload: dict) -> str:
    return yaml.dump(payload, Dumper=_BlockDumper, sort_keys=False, allow_unicode=True, width=1000)


def pool_manifest(adapter: DatasetAdapter, payloads: list[dict], filenames: list[str]) -> dict:
    """Playground pool manifest: persona files, counts, and the dataset's overlays."""
    observed: dict[str, set[str]] = {o.id: set() for o in adapter.overlay_dimensions}
    for payload in payloads:
        for key, value in (payload.get("dimensions") or {}).items():
            if key in observed:
                observed[key].add(value)
    overlays = [
        {
            "id": o.id,
            "label": o.label,
            "values": list(o.values) if o.values else sorted(observed[o.id]),
        }
        for o in adapter.overlay_dimensions
    ]
    return {
        "kind": "persona-fit",
        "dataset": adapter.slug,
        "schema_version": "1.0",
        "count": len(filenames),
        "source_counts": {"persona-fit/{}".format(adapter.slug): len(filenames)},
        "overlay_dimensions": overlays,
        "personas": filenames,
    }


def build_personas(adapter: DatasetAdapter, prepared: Prepared, *, clean: bool = True) -> dict[str, str]:
    """Personas for every scored person. Returns person_id -> repo-relative YAML path."""
    out_dir = persona_dir(adapter.slug)
    if clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame = prepared.frame
    scored_people = frame.loc[frame["scored"], "person_id"].unique()
    history_by_person = {pid: grp for pid, grp in prepared.history.groupby("person_id")} if adapter.uses_history else {}
    source = frame.attrs.get("prior_source")
    prior = None
    if source:
        people = set(scored_people)
        catalog, wave13, exam_columns = source
        wave13 = wave13[wave13["pid"].astype(str).isin(people)]
        prior = adapter._prior_answers(catalog, wave13, exam_columns).loc[list(scored_people)]
    by_person = {pid: grp for pid, grp in frame[frame["person_id"].isin(scored_people)].groupby("person_id")}
    if prior is not None:
        for pid, grp in by_person.items():
            grp.attrs["prior_answers"] = prior
    paths: dict[str, str] = {}
    payloads: list[dict] = []
    filenames: list[str] = []
    for person_id in scored_people:
        spec = adapter.persona(by_person[person_id], history=history_by_person.get(person_id))
        payload = render_persona_yaml(adapter, person_id, spec)
        filename = "persona_{}.yaml".format(payload["persona_id"])
        (out_dir / filename).write_text(dump_yaml(payload), encoding="utf-8")
        paths[str(person_id)] = rel(out_dir / filename)
        payloads.append(payload)
        filenames.append(filename)
    (out_dir / "manifest.json").write_text(
        json.dumps(pool_manifest(adapter, payloads, filenames), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out_dir / "index.json").write_text(
        json.dumps({"dataset": adapter.slug, "count": len(paths), "personas": paths}, indent=2) + "\n", encoding="utf-8"
    )
    return paths


def load_persona_index(adapter: DatasetAdapter) -> dict[str, str]:
    path = persona_dir(adapter.slug) / "index.json"
    if not path.is_file():
        raise FileNotFoundError("{}: run `personas --dataset {}` first".format(adapter.slug, adapter.slug))
    return json.loads(path.read_text(encoding="utf-8"))["personas"]


def example_persona(adapter: DatasetAdapter, rows: pd.DataFrame) -> dict:
    person_id = str(rows.iloc[0]["person_id"])
    return render_persona_yaml(adapter, person_id, adapter.persona(rows[rows["person_id"] == person_id]))
