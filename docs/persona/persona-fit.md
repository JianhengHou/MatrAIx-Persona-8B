# Persona-fit: real-person decision datasets

The Fit A rows of `persona_fit_datasets.xlsx` are public datasets in which a
real person made a recorded decision. Each one is converted into MatrAIx survey
tasks with the same three locks:

- **Persona**: the person's stable identity, built once per person
  (`persona/datasets/persona-fit-<dataset>/`). See "Persona attributes" below.
- **Task card**: what the person saw for that decision (partner profile, trip
  options, the e-mail or letter, the movie, the survey item), in
  `input/context.md` and `input/questionnaire.yaml`.
- **Outcome**: the held-out decision, only in `tests/labels.json`. The agent
  never sees `tests/`.

Each trial's answer is scored against the person's real decision. Optionally
the same trials can also be run with no persona (`none`, the persona-free
control) to see how much of the result comes from the persona itself.

Notes on datasets still under review, including what each one actually
measures, are in [persona-fit-candidates.md](persona-fit-candidates.md).

## Persona attributes

Attributes are fixed per dataset, not unified across datasets, so no source
value is recoded to fit a shared vocabulary:

- **Overlays** (in `dimensions`): the dataset's categorical attributes with
  their original labels, under dataset-scoped ids such as
  `twin_qid14`. Each adapter declares them in
  `overlay_dimensions`; the pool's `manifest.json` lists them with display
  labels, so they render under "Other attributes" and can be filtered in
  Playground.
- **Schema dimensions** (in `dimensions`): only where the mapping is
  one-to-one, e.g. gender, region, life stage.
- **Facts** (in `system_prompt`): numeric and free-text attributes kept as
  values with units and scale anchors (age, spend, months since last purchase,
  preference weights, Big Five scores, rating history).

Anything not observed for a person is left out; nothing is imputed.

## The five datasets

All five are application tasks: each person faces the decision they actually
saw, and nobody is assigned a treatment arm. The two conjoints are stated
preference (SP): the randomized profiles are the choice set shown, not a
treatment.

| Dataset | Task template |
|---------|---------------|
| Twin-2K-500 | `persona/persona_fit/tasks/twin-2k-500/` |
| Immigration conjoint | `persona/persona_fit/tasks/immigration-conjoint/` |
| MovieLens 1M | `persona/persona_fit/tasks/movielens-1m/` |
| EB-NeRD | `persona/persona_fit/tasks/eb-nerd/` |
| Bansak asylum conjoint | `persona/persona_fit/tasks/bansak-asylum/` |

The checked-in task folders are **templates** holding one synthetic example
row. Real tasks are generated, one per distinct task card, under
`data/persona_fit/tasks/<dataset>/` (gitignored, as are the
personas, job shards, and `data/persona_fit/`).

## Run one dataset

```bash
pf() { uv run python -m persona.persona_fit "$@"; }
pf list                                   # datasets, path, raw files
pf download --dataset eb-nerd             # direct links; prints steps for gated files
pf all --dataset eb-nerd                  # prepare + personas + tasks + jobs
pf run --dataset eb-nerd --mode full --parallel 20
pf score --dataset eb-nerd

# optional persona-free control on the same trials
pf jobs --dataset eb-nerd --with-control
pf run --dataset eb-nerd --mode none --parallel 20
```

Running with another model, sizes and parallelism: [`handover.md`](../../handover.md).
Results so far: [persona-fit-results.md](persona-fit-results.md).

`all` accepts `--sample-rows` (people that get trials, drawn from the whole
dataset by person), `--max-rows-per-person`, and
`--model`. MovieLens is the one exception to "the whole dataset": only each
user's latest 20% of ratings can be drawn, and the earlier ratings are that
user's rating history in the persona. `run` skips a shard only when every
trial finished without an exception. A wrong answer is a real decision and is
kept. A shard that never finished is started again; a finished shard with a
failed, incomplete, or missing trial has those trial directories deleted and
is resumed in the same `jobs/<shard>/`, so successful trials stay and the
shard `result.json` is overwritten. `--limit` and `--parallel` control how
many of those pending shards run.

Outputs:

| What | Where |
|------|-------|
| Decision frame, scored sample | `data/persona_fit/work/<dataset>/` |
| Personas | `persona/datasets/persona-fit-<dataset>/` |
| Generated tasks | `data/persona_fit/tasks/<dataset>/` |
| Job shards (`full`; `none` with `--with-control`) | `configs/jobs/persona-fit/<dataset>/<mode>/` |
| Trials | `jobs/pf-<dataset>-<mode>-NNNN/` |
| Metrics, predictions | `data/persona_fit/results/<dataset>/score.{json,md}`, `predictions.csv` |

## How a trial runs

Harbor runs every agent in a job against every task in it, so each job shard is
a block where all pairs are real decisions: one shard per person with all of
that person's own cards. `persona-json-survey`
reads the trial's own task from Harbor's `config.json`, so one job can hold
many different cards. The verifier (`tests/test_state.py`, a copy of
`persona/persona_fit/verifier/ground_truth.py`) reads the persona id from
`/app/input/persona.yaml`, looks up that person's decision, and writes
`reward.txt` (1/0 for choices, `1 - |error| / range` for ratings) plus
`structured_output.json`. Persona-free shards export
`MATRIX_PERSONA_MODE=none`.

## Scoring

`score` compares each run with the real decisions on the rows it answered
(and, if the persona-free run exists, the full persona with it on the rows
both answered):

| Decision | Metrics |
|----------|---------|
| Binary (EB-NeRD open or not) | AUC, Brier, log-loss, calibration slope, rate error (pp) |
| Two-profile choice (conjoints) | AUC, accuracy, log-loss |
| Multinomial (Twin-2K survey item) | accuracy, log-loss; five or more options give half credit for a one-step miss |
| Rating (MovieLens) | RMSE, MAE, within-person correlation |

When the persona-free run exists, the full-minus-none difference uses a
bootstrap that resamples whole persons, and the verdict line says whether the
full persona beats the control at 95%.

## Data access

Direct downloads: Twin-2K-500, immigration conjoint, MovieLens 1M, Bansak.
EB-NeRD is behind an accept-terms gate; `download` prints the steps.

Licences: MovieLens forbids redistribution; EB-NeRD is research only, with no
redistribution and no use for training a language model. Keep everything
derived from these files under the gitignored paths above.

## Add a dataset

1. Add an adapter under `persona/persona_fit/adapters/` (subclass
   `DatasetAdapter`): `load` returns one row per decision with `row_id`,
   `person_id`, `outcome` (plus `cluster_id`, `arm`, `weight` when relevant);
   declare `persona_fields`, `card_fields`, `leakage_fields`,
   `overlay_dimensions`, `persona`, `card`, and synthetic `example_rows`.
2. Register it in `persona/persona_fit/registry.py`.
3. `python -m persona.persona_fit templates --dataset <slug>` writes the template task.
4. `tests/persona/test_persona_fit.py` checks that leakage columns
   never reach the persona or the card, that overlays are declared and
   dataset-scoped, and that the template is in sync.
