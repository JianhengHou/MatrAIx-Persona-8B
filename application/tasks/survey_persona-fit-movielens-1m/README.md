# Persona-fit: MovieLens 1M ratings (sheet row 08)

Template task for one persona-fit dataset. The files here hold a single
synthetic example row so the oracle and contract tests can run. Real tasks (one per
distinct task card) are generated under `application/tasks/_generated/persona-fit/movielens-1m`.

- Persona: stable identity of the real person (`persona/datasets/persona-fit-movielens-1m`).
- Task card: `input/context.md` + `input/questionnaire.yaml` (the situation they saw).
- Outcome: held out in `tests/labels.json`; the verifier rewards a match.

Decision type: `rating`.

## Run

```bash
uv run python application/scripts/run_persona_fit.py all --dataset movielens-1m
uv run python application/scripts/run_persona_fit.py run --dataset movielens-1m --mode full
uv run python application/scripts/run_persona_fit.py score --dataset movielens-1m
```

See `docs/application/persona-fit.md`.
