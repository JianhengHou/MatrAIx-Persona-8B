# Persona-fit: Bansak, Hainmueller & Hangartner asylum conjoint (sheet row 35)

Template task for one persona-fit dataset. The files here hold a single
synthetic example row so the oracle and contract tests can run. Real tasks (one per
distinct task card) are generated under `application/tasks/_generated/persona-fit/bansak-asylum`.

- Persona: stable identity of the real person (`persona/datasets/persona-fit-bansak-asylum`).
- Task card: `input/context.md` + `input/questionnaire.yaml` (the situation they saw).
- Outcome: held out in `tests/labels.json`; the verifier rewards a match.

Decision type: `pair`. Stated preference (SP): not a market forecast.

## Run

```bash
uv run python application/scripts/run_persona_fit.py all --dataset bansak-asylum
uv run python application/scripts/run_persona_fit.py run --dataset bansak-asylum --mode full
uv run python application/scripts/run_persona_fit.py score --dataset bansak-asylum
```

See `docs/application/persona-fit.md`.
