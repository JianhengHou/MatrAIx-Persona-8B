"""Persona-fit pipeline: real-person decision datasets as MatrAIx survey tasks.

    uv run python -m persona.persona_fit list
    uv run python -m persona.persona_fit all --dataset eb-nerd

See docs/persona/persona-fit.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# Harbor, the Playground backend and the playground package are imported from
# the source tree when a job runs, the same paths application/scripts sets up.
for path in (
    REPO_ROOT / "application" / "playground",
    REPO_ROOT / "packages" / "playground" / "src",
    REPO_ROOT / "environment" / "runtime",
    REPO_ROOT,
):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from persona.persona_fit.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
