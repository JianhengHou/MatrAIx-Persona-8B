# Persona-fit: Hainmueller & Hopkins immigration conjoint (sheet row 07)

Template task for one persona-fit dataset. The files here hold a single
synthetic example row so the oracle and contract tests can run. Real tasks (one per
distinct task card) are generated under `application/tasks/_generated/persona-fit/immigration-conjoint`.

- Persona: stable identity of the real person (`persona/datasets/persona-fit-immigration-conjoint`).
- Task card: `input/context.md` + `input/questionnaire.yaml` (the situation they saw).
- Outcome: held out in `tests/labels.json`; the verifier rewards a match.

Decision type: `pair`. Stated preference (SP): not a market forecast.

## Run

```bash
uv run python application/scripts/run_persona_fit.py all --dataset immigration-conjoint
uv run python application/scripts/run_persona_fit.py run --dataset immigration-conjoint --mode full
uv run python application/scripts/run_persona_fit.py score --dataset immigration-conjoint
```

See `docs/application/persona-fit.md`.
