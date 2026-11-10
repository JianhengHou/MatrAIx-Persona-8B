# Persona-fit: EB-NeRD news clicks (sheet row ebnerd)

Template task for one persona-fit dataset. The files here hold a single
synthetic example row so the oracle and contract tests can run. Real tasks (one per
distinct task card) are generated under `application/tasks/_generated/persona-fit/eb-nerd`.

- Persona: stable identity of the real person (`persona/datasets/persona-fit-eb-nerd`).
- Task card: `input/context.md` + `input/questionnaire.yaml` (the situation they saw).
- Outcome: held out in `tests/labels.json`; the verifier rewards a match.

Decision type: `binary`.

## Run

```bash
uv run python application/scripts/run_persona_fit.py all --dataset eb-nerd
uv run python application/scripts/run_persona_fit.py run --dataset eb-nerd --mode full
uv run python application/scripts/run_persona_fit.py score --dataset eb-nerd
```

See `docs/application/persona-fit.md`.
