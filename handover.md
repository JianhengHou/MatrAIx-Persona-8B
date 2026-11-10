# Handover: running the persona-fit datasets with your own model

This branch (`eval-persona-dataset`) turns five public datasets of real
decisions into survey tasks. Each real person becomes a simulated persona, the
persona answers the items that person actually saw, and the answers are scored
against what the person really did. You bring a model and an API key; the rest
is fixed.

Reference numbers from GLM 5.3, and what they mean, are in
[`docs/application/persona-fit-results.md`](docs/application/persona-fit-results.md).
Pipeline internals are in
[`docs/application/persona-fit.md`](docs/application/persona-fit.md).

## 1. Install

```bash
git clone -b eval-persona-dataset https://github.com/JianhengHou/MatrAIx-Persona-8B.git
cd MatrAIx-Persona-8B
uv sync --python 3.12
```

Use Python 3.12. With Python 3.15 some dependencies have no prebuilt wheel and
`uv sync` fails while building `tiktoken`.

Every command below goes through one shell function. Define it once per shell:

```bash
pf() { uv run python application/scripts/run_persona_fit.py "$@"; }
```

A plain variable (`PF="uv run ..."; $PF list`) does not work in zsh, the macOS
default shell, because zsh does not split it into words.

Behind a corporate proxy that intercepts TLS (Zscaler and similar), add
`--native-tls` after `uv run` and `uv sync`, and point `SSL_CERT_FILE` and
`REQUESTS_CA_BUNDLE` at your CA bundle. Otherwise leave both out.

## 2. Download the data

The raw files go under `data/persona_fit/raw/<dataset>/`, which is gitignored.
Never commit them; two of the licences forbid redistribution.

Four datasets download directly:

```bash
pf download --dataset twin-2k-500,immigration-conjoint,movielens-1m,bansak-asylum
```

| Dataset | Files | Source | Licence |
|---------|-------|--------|---------|
| `twin-2k-500` | `question_catalog.json`, `wave1_3_response.csv`, `wave4_response.csv` (6 MB) | [Hugging Face, LLM-Digital-Twin/Twin-2K-500](https://huggingface.co/datasets/LLM-Digital-Twin/Twin-2K-500) | See the dataset card |
| `immigration-conjoint` | `repdata.tab` (2 MB) | [Harvard Dataverse doi:10.7910/DVN/25505](https://doi.org/10.7910/DVN/25505) | CC0 |
| `movielens-1m` | `ml-1m.zip`, unzipped to `ml-1m/` (6 MB) | [GroupLens](https://grouplens.org/datasets/movielens/1m/) | Research use, no redistribution, cite Harper & Konstan 2015 |
| `movielens-1m` | `zcta_county.txt`, `zcta_place.txt` (17 MB) | US Census 2020 ZCTA relationship files; they turn a zip code into a town and county | Public domain |
| `bansak-asylum` | `conjoint_data_final.tab`, `respondent_data_final.tab` (18 MB) | [Harvard Dataverse doi:10.7910/DVN/KL0FDF](https://doi.org/10.7910/DVN/KL0FDF) | CC0 |

EB-NeRD needs a manual step, because the newspaper requires you to accept its
terms first:

1. Go to [recsys.eb.dk](https://recsys.eb.dk/), sign in, and accept the
   research terms.
2. Download **ebnerd_small** (80 MB zip). Not demo, not large.
3. Put it at `data/persona_fit/raw/eb-nerd/ebnerd_small.zip` and unzip it in
   that folder:

   ```bash
   cd data/persona_fit/raw/eb-nerd && unzip ebnerd_small.zip && cd -
   ```

   You should now have `articles.parquet`, `train/behaviors.parquet`,
   `train/history.parquet`, `validation/behaviors.parquet` and
   `validation/history.parquet`. A `__MACOSX/` folder from the zip is harmless.

EB-NeRD is research-only: no redistribution, and the files must not be used
to train a language model.

To confirm you have the same files the reference run used:

```bash
cd data/persona_fit/raw && shasum -a 256 -c - <<'EOF'
e72e305f0c7c83bb990e97de4c0cf2c718ead18cc197239b7feeb354c9ac1bef  twin-2k-500/question_catalog.json
fc227b1682e2654fd4b2a8152294b68118c0e3be4d83f4a9af5f3e96df56d3f0  twin-2k-500/wave1_3_response.csv
09ec1a88bdd48fec95963da3102df0ca467378bf729cbc1c0b869b0f1e4fb942  twin-2k-500/wave4_response.csv
d40a380bcf8d0edcafd5899d6385f77f6bdcb1f7a94db97c937b1b6c3c6f35d6  immigration-conjoint/repdata.tab
a6898adb50b9ca05aa231689da44c217cb524e7ebd39d264c56e2832f2c54e20  movielens-1m/ml-1m.zip
3ed41278d637dc249e0323306f68be8a6c234e3090f4de88ef328dee71aeaaaf  movielens-1m/zcta_county.txt
698a5dad71ed419411677d0ffd8ecd9331067f59c472cdd239b92c12f698285d  movielens-1m/zcta_place.txt
84675e4f54bdc3f4f6b21189156d67d00a57bc14d2c1d1566116790050de6dea  bansak-asylum/conjoint_data_final.tab
06c24e6e73b7d9ce86ed0701b567c2498ae4289ef37daade754d1c38a6724369  bansak-asylum/respondent_data_final.tab
84fc6fc902b8e8dad8383835c90185d54e0916060586d428ced391da4a92bd4f  eb-nerd/ebnerd_small.zip
EOF
cd -
```

## 3. Point it at your model

Put your key in `.env.local` at the repo root (gitignored), or export it in
the shell; a shell export wins over `.env.local`. Then name the model as
`<provider>/<model id>`.

| Provider | `--model` | Required variables | Optional |
|----------|-----------|--------------------|----------|
| OpenAI | `openai/<model>` | `OPENAI_API_KEY` | |
| Any OpenAI-compatible server (vLLM, SGLang, Together, Fireworks, a gateway) | `openai/<served model name>` | `OPENAI_API_KEY`, `OPENAI_BASE_URL` | |
| Anthropic | `anthropic/<model>` | `ANTHROPIC_API_KEY` | |
| Google Gemini | `gemini/<model>` | `GEMINI_API_KEY` | `GEMINI_API_BASE` |
| OpenRouter | `openrouter/<vendor>/<model>` | `OPENROUTER_API_KEY` | `OPENROUTER_API_BASE` |
| DeepSeek | `deepseek/<model>` | `DEEPSEEK_API_KEY` | `DEEPSEEK_API_BASE` |
| xAI | `xai/<model>` | `XAI_API_KEY` | `XAI_API_BASE` |
| Z.ai (GLM) | `zai/<model>` | `ZAI_API_KEY` | `ZAI_API_BASE` |
| Alibaba DashScope | `dashscope/<model>` | `DASHSCOPE_API_KEY` | `DASHSCOPE_API_BASE` |

A self-hosted model, for example served with vLLM:

```bash
# .env.local
OPENAI_BASE_URL=http://my-gpu-box:8000/v1
OPENAI_API_KEY=anything-your-server-accepts
```

and run with `--model openai/<the name vLLM serves it under>`. Setting
`OPENAI_BASE_URL` also sends `anthropic/` models through that URL, so leave it
unset if you switch back to Anthropic.

What the model has to support:

- **Context of at least 128k tokens.** The largest prompts are about 76k input
  tokens (EB-NeRD) and 59k (Twin-2K), measured with the GLM tokenizer; other
  tokenizers differ, Danish text especially. A 32k model will fail those
  trials.
- **JSON output.** The request sets `response_format: json_object`. A model or
  server that ignores it and wraps the answer in prose will fail to parse.
- **Enough output budget.** Twin-2K asks about 84 questions in one call.
  Anthropic models get 16,384 output tokens. OpenAI-family calls use the
  server's default `max_tokens`; a reasoning model with a small default can be
  cut off mid-JSON. GLM through `zai/` is special-cased to 65,536 tokens with
  low reasoning effort.
- **Timeout.** Each request times out after 180 seconds. Raise it with
  `LLM_REQUEST_TIMEOUT_SECONDS=600` for slow or reasoning models; one Twin-2K
  trial took 534 seconds on GLM.

### Model families to run

The families planned for comparison are Anthropic (Claude), Google (Gemini),
OpenAI (GPT), Z.ai (GLM), Moonshot (Kimi K3), DeepSeek and xAI (Grok). Each
has a route that needs no code change. Take the exact model id from your
provider's model list; ids below are only the ones checked here.

| Family | Recommended `--model` | Checked here (Nov 2026) | Notes |
|--------|-----------------------|--------------------------|-------|
| Anthropic | `anthropic/<id>` | Not run, no key | Native Messages API, not JSON mode: the prompt asks for JSON only. Output capped at 16,384 tokens. Temperature is left out only for ids matching `opus-4-7` and later 4.x; any other id, including a newer naming such as `opus-5`, is sent 0.7. If the API rejects that, the smoke test shows it. |
| Gemini | `gemini/<id>` | Not run, no key | Google's OpenAI-compatible endpoint, with JSON mode. `google/<id>` is the same route. |
| OpenAI | `openai/<id>`, e.g. `openai/gpt-6-sol` | Request reached OpenAI and the id was accepted; the test account had no credit, so no answers | No temperature is sent to `gpt-5*` and `gpt-6*`. The o-series (`o3`, `o4`) also rejects a custom temperature, and the code does not yet omit it for them, so they fail until it does. |
| GLM | `zai/glm-5.3` | Reference run, all five datasets | `zai/` is special-cased: 65,536 output tokens, thinking on at low effort. The same model through `dashscope/` or `openrouter/` gets neither setting; that route was not tested. |
| Kimi K3 | `dashscope/kimi-k3` | Request reached DashScope and the id was accepted; the test account's free quota was used up, so no answers | Alibaba DashScope hosts it. Moonshot's own API or OpenRouter also work through `openai/` with `OPENAI_BASE_URL`, or `openrouter/<id>`. |
| DeepSeek | `dashscope/deepseek-v4-pro` or `deepseek/<id>` | `dashscope/deepseek-v4-pro` ran Immigration and Twin-2K end to end | It reasons before answering: about 5.7k output tokens on one Twin-2K trial against GLM's 1.1k. Budget output cost accordingly. |
| Grok | `xai/<id>` | Not run, no key | xAI's OpenAI-compatible endpoint. |

To keep the comparison fair:

- **Record the route, not just the model.** The same model hosted by two
  providers can differ in quantization, defaults and context. Report
  `dashscope/kimi-k3`, not "Kimi K3".
- **Temperature is not identical across families.** Every model is sent 0.7
  except `gpt-5*`, `gpt-6*` and Claude `opus-4-7` and later 4.x, which run at
  their provider's default. Say so when comparing.
- **One model per shell.** `OPENAI_BASE_URL` is global. If Kimi goes through
  `openai/` with Moonshot's URL, run OpenAI models in a different shell or
  clone.
- **Out of credit looks like a failed run.** A quota or billing error fails
  every trial with an exception. If `run` ends with many failures, read one
  `jobs/pf-*/*/exception.txt` before rerunning.

### Smoke test

Before a full run, two people on the smallest dataset and one on the largest
output:

```bash
pf all --dataset immigration-conjoint --sample-rows 2 --model <your model> --max-agents 1 --concurrent 1
pf run --dataset immigration-conjoint --mode full --parallel 2
pf score --dataset immigration-conjoint

pf all --dataset twin-2k-500 --sample-rows 1 --model <your model> --max-agents 1 --concurrent 1
pf run --dataset twin-2k-500 --mode full --parallel 1
```

You should see `Rewards:` lines and, for Immigration, a score table with
`Valid answers` 10. The Twin-2K trial checks that about 84 answers fit in the
model's output. This is not the standard sample. Remove it before the real
run (section 7).

## 4. The fixed sample

Everyone runs the same people and the same items. Do not pass `--sample-rows`;
the defaults below are the standard sample.

| Dataset | People | Items scored | Sample fingerprint |
|---------|--------|--------------|--------------------|
| `twin-2k-500` | 100 of 2,058 | 8,224 survey items | `825d306854636041` |
| `immigration-conjoint` | 100 of 1,404 | 500 pairs | `14a095ebd5536c16` |
| `movielens-1m` | 100 of 6,040 | 3,064 ratings | `6af1635699f608c2` |
| `bansak-asylum` | 3,606 of 18,030 (20%) | 18,030 pairs | `775b2ee159729cfc` |
| `eb-nerd` | 100 of 635 | 1,098 articles | `b41c7940914713cb` |

How the people are picked: each person id is hashed with the fixed seed
`20261104` (SHA-256 of `20261104:sample:<person id>`), people are sorted by that
hash, and the first N are taken. Nothing depends on the machine, the model, or
the run order, so the same raw files always give the same people. A larger N
keeps everyone in a smaller N: the Bansak 3,606 contain the 100 of the GLM
reference run.

The fingerprint is a hash of every scored item id. `pf all` and `pf prepare`
print it on the first line for each dataset:

```
bansak-asylum: {"rows": 90150, ..., "scoredPersons": 3606, "sampleFingerprint": "775b2ee159729cfc"}
```

**If your fingerprint differs from the table, stop.** It means different raw
files (check the sha256 list in section 2), a different `--sample-rows`, or
changed adapter code. Results from a different sample cannot be compared.

Why these sizes: 100 people is the size of the GLM reference run and is
enough for an overall score. On the conjoints, five pairs per person, the 95%
interval on accuracy is about ±5 points; it is tighter where each person
answers more items.
Bansak is cheap per person and spans 15 countries, so it takes a fifth of the
voters: 213 to 258 per country, enough to compare countries (about ±3 points
each) and about ±1 point overall. EB-NeRD cannot go above 635, because only
readers with a known age or gender can be a persona.

## 5. How much each dataset costs

One person is one trial is one model call.

| Dataset | Trials | Questions per trial, median (max) | Input tokens per trial, median (max) | Output tokens per trial, median | Seconds per trial on GLM, median (max) | Input tokens, whole sample |
|---------|--------|------------------------------------|---------------------------------------|----------------------------------|-----------------------------------------|----------------------------|
| `twin-2k-500` | 100 | 84 (84) | 37k (59k) | 1.1k | 17 (534) | 3.6M |
| `immigration-conjoint` | 100 | 5 (5) | 2.1k (2.1k) | 200 | 7 (20) | 0.21M |
| `movielens-1m` | 100 | 17 (209) | 2.6k (18k) | 220 | 6 (74) | about 0.3M |
| `bansak-asylum` | 3,606 | 5 (5) | 2.1k (2.7k) | 200 | 9 (24) | about 7.6M |
| `eb-nerd` | 100 | 8 (54) | 24k (76k) | 180 | 8 (49) | 2.9M |

Per-trial numbers are from the GLM reference run (100 people each). Output
tokens exclude hidden reasoning on providers that do not report it. The whole
standard sample is 4,006 calls and about 14.6M input tokens; Bansak is half of
the tokens and almost all of the calls.

## 6. Run

```bash
MODEL=openai/your-model   # your provider and model
P=20                      # parallel trials, see below

for d in twin-2k-500 immigration-conjoint movielens-1m bansak-asylum eb-nerd; do
  pf all   --dataset $d --model $MODEL --max-agents 1 --concurrent 1
  pf run   --dataset $d --mode full --parallel $P
  pf score --dataset $d
done
```

- `all` draws the standard sample, writes one persona per person, one task per
  person, and one job shard per person. Check the fingerprint it prints
  against section 4 before letting `run` start. Keep
  `--max-agents 1 --concurrent 1`: that is one person per shard, which is
  what `--parallel` spreads out.
- `run` runs every pending shard. Run it again after a crash or a rate-limit
  burst: finished trials are kept, failed ones are deleted and redone. It
  exits non-zero while anything failed.
- `score` prints the table and writes
  `data/persona_fit/results/<dataset>/score.{json,md}` and `predictions.csv`.
- One `run` command does its datasets one after another. To run datasets at
  the same time, open one terminal per dataset; the parallel counts add up
  against your provider limit.

### Choosing `--parallel`

Each parallel trial is a separate Python process that mostly waits on the API.
Measured: about 230 MB for the main process plus about 95 MB per parallel
trial, so `--parallel 20` needs about 2 GB and `--parallel 100` about 10 GB.
CPU is not the limit on a laptop. Your provider's rate limit almost always is.

Pick the largest `P` that satisfies all three:

- Memory: `P ≤ (free RAM in GB − 0.5) × 10`.
- Requests: `P ≤ requests-per-minute limit × seconds per trial / 60`.
- Tokens: `P ≤ tokens-per-minute limit × seconds per trial / (60 × input tokens per trial)`.

The token limit binds first on Twin-2K and EB-NeRD. At `P = 20` on GLM speed,
Twin-2K sends about 2.6M input tokens a minute and EB-NeRD about 3.6M; the
conjoints send about 0.3M and MovieLens about 0.5M. If you hit rate-limit errors,
lower `P` for those two and run `run` again. A self-hosted server is limited
by its own batch size instead; start at the server's maximum concurrent
sequences.

With GLM at `P = 20`, 100 Bansak people took 66 seconds and EB-NeRD's 100 took
100 seconds, so the 3,606 Bansak people take about 30 minutes at the same
speed. A single slow trial sets the tail. Bansak's 3,606 shards also mean
3,606 persona files, task folders and job folders on disk, about 650 MB.

## 7. Switching models

Job folders are named by dataset, not by model, and `run` skips anything
already finished. Before a second model, move the first one's trials and
scores out of the way, or the new run will either skip everything or be
scored together with the old one:

```bash
OLD=glm-5.3
mkdir -p jobs/archive/$OLD data/persona_fit/results-archive/$OLD
mv jobs/pf-*-full-* jobs/archive/$OLD/
mv data/persona_fit/results/* data/persona_fit/results-archive/$OLD/
```

Then run section 6 again with the new `--model`. `all` rewrites the personas,
tasks and shards for the same standard sample, so the two models are compared
on identical questions; the fingerprint confirms it.

Using a separate clone per model works too.

## 8. What to send back

Send `data/persona_fit/results/<dataset>/score.json` and `score.md` for each
dataset, with the model id and the sample fingerprint `all` printed. These are
aggregate metrics.

Keep `predictions.csv`, the personas, the tasks and `jobs/` internal. They
contain each person's real answers, and MovieLens and EB-NeRD forbid
redistribution.

## 9. Known issues

- **An invalid answer is silently replaced.** If the model returns a
  single-choice value that is not one of the options, the shared survey code
  replaces it with the first option before scoring: `yes` in EB-NeRD, `a` in
  the conjoints, the first option in Twin-2K. A missing answer is filled the
  same way. The raw model output is not stored, so this cannot be detected
  after the fact. A model that formats answers loosely will look biased
  towards `yes` and `a`.
- **Twin-2K is mostly recall.** Every scored item was asked in an earlier
  sitting, and the earlier answers are in the persona. Copying them scores
  0.761, about what GLM scores.
- **Bansak language.** The questionnaire and persona are translated into each
  country's survey language by us, not taken from the original instrument.
  Switzerland has no recorded language, so its 236 respondents in the
  standard sample see English; report Switzerland separately. The persona
  wrapper is English for everyone.
- **No persona-free control yet.** `pf jobs --dataset <d> --with-control` and
  `pf run --dataset <d> --mode none` run the same cards without a persona. None
  of the reference numbers include it.
