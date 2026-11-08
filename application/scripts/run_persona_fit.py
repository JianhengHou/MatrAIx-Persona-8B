#!/usr/bin/env python3
"""Persona-fit pipeline: real-person decision datasets as MatrAIx survey tasks.

    uv run python application/scripts/run_persona_fit.py list
    uv run python application/scripts/run_persona_fit.py all --dataset eb-nerd

See docs/application/persona-fit.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

_APPLICATION_DIR = Path(__file__).resolve().parents[1]
if str(_APPLICATION_DIR) not in sys.path:
    sys.path.insert(0, str(_APPLICATION_DIR))

from _repo_imports import ensure_application_script_imports  # noqa: E402

ensure_application_script_imports()

from persona_fit.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
