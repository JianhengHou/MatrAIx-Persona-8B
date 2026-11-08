"""Repo locations used by the persona-fit pipeline (all outputs are gitignored)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = Path(__file__).resolve().parent

DATA_ROOT = REPO_ROOT / "data" / "persona_fit"
RAW_ROOT = DATA_ROOT / "raw"
WORK_ROOT = DATA_ROOT / "work"
RESULTS_ROOT = DATA_ROOT / "results"

PERSONA_ROOT = REPO_ROOT / "persona" / "datasets"
APP_TASK_TEMPLATES = REPO_ROOT / "application" / "tasks"
APP_GENERATED_ROOT = REPO_ROOT / "application" / "tasks" / "_generated" / "persona-fit"
JOBS_ROOT = REPO_ROOT / "configs" / "jobs" / "persona-fit"

VERIFIER_SOURCE = PACKAGE_DIR / "verifier" / "ground_truth.py"


def raw_dir(slug: str) -> Path:
    return RAW_ROOT / slug


def work_dir(slug: str) -> Path:
    return WORK_ROOT / slug


def persona_dir(slug: str) -> Path:
    return PERSONA_ROOT / "persona-fit-{}".format(slug)


def rel(path: Path) -> str:
    """Repo-relative POSIX path (job YAMLs and task paths are repo-relative)."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()
