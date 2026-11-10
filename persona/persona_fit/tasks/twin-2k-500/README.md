# Persona-fit: Twin-2K-500 held-out survey items (sheet row 06)

Template task for one persona-fit dataset. The files here hold a single
synthetic example row so the oracle and contract tests can run. Real tasks (one per
distinct task card) are generated under `data/persona_fit/tasks/twin-2k-500`.

- Persona: stable identity of the real person (`persona/datasets/persona-fit-twin-2k-500`).
- Task card: `input/context.md` + `input/questionnaire.yaml` (the situation they saw).
- Outcome: held out in `tests/labels.json`; the verifier rewards a match.

Decision type: `multinomial`.

## Run

```bash
uv run python -m persona.persona_fit all --dataset twin-2k-500
uv run python -m persona.persona_fit run --dataset twin-2k-500 --mode full
uv run python -m persona.persona_fit score --dataset twin-2k-500
```

See `docs/persona/persona-fit.md`.
