# Persona-fit: Hainmueller & Hopkins immigration conjoint (sheet row 07)

Template task for one persona-fit dataset. The files here hold a single
synthetic example row so the oracle and contract tests can run. Real tasks (one per
distinct task card) are generated under `data/persona_fit/tasks/immigration-conjoint`.

- Persona: stable identity of the real person (`persona/datasets/persona-fit-immigration-conjoint`).
- Task card: `input/context.md` + `input/questionnaire.yaml` (the situation they saw).
- Outcome: held out in `tests/labels.json`; the verifier rewards a match.

Decision type: `pair`. Stated preference (SP): not a market forecast.

## Run

```bash
uv run python -m persona.persona_fit all --dataset immigration-conjoint
uv run python -m persona.persona_fit run --dataset immigration-conjoint --mode full
uv run python -m persona.persona_fit score --dataset immigration-conjoint
```

See `docs/persona/persona-fit.md`.
