# Persona-fit results: how close a simulated persona gets to the real person

Five datasets of real decisions, one simulated persona per real person, scored
against what that person actually did. This page says, per dataset, what the
simulated persona scored, whether that is good, and where the ceiling is.
How to run the same thing with another model is in
[`handover.md`](../../handover.md).

## Setup behind these numbers

- Model: `zai/glm-5.3`, thinking on at low effort.
- Sample: the same 100 people per dataset, drawn by a seeded hash of the person
  id (seed `20261104`). A larger `--sample-rows` keeps these 100 and adds the
  next people in the same order.
- One person is one trial: that person's persona, and every item that person
  actually answered, in one model call.
- The persona holds what the person knew about themselves or could see before
  the decision. Outcomes, anything computed from them, and facts the person
  never knew (survey weights, ecological variables, expert scores) stay out.
- No persona-free control was run on any dataset. Where a "no persona"
  reference appears below, it is a separate statistical model, not the LLM.

## Summary

| Dataset | Sample | Simulated persona | Reference point | Verdict |
|---------|--------|-------------------|-----------------|---------|
| Twin-2K-500 | 100 people, 8,224 items | 0.76 accuracy (half credit) | Copying the person's earlier answer: 0.761. Human two-week test-retest: 0.817 | At the measurable ceiling, but mostly recall |
| Immigration conjoint | 100 people, 500 pairs | 0.718 accuracy, AUC 0.718 | Profile-only regression, no persona: 0.718 (95% CI 0.678–0.758) | Equal to population consensus |
| Bansak asylum conjoint | 100 people, 500 pairs | 0.606 accuracy, AUC 0.607 | Profile-only regression, no persona: 0.630 (95% CI 0.584–0.678) | Inside the consensus interval |
| MovieLens 1M | 100 people, 3,064 ratings | MAE 0.73, RMSE 1.02, exact 0.40 | User mean + movie mean, rounded: MAE 0.75, RMSE 1.02, exact 0.39 | Tied with a two-number baseline |
| EB-NeRD | 100 people, 1,098 articles | 0.636 accuracy, AUC 0.563, predicts 0.359 opened | True open rate 0.097. One random click per screen: 0.787 | Below a naive rule; ranking near chance |

None of the five is near 90%. The reasons are not the same across datasets, and
for four of them the gap is not a field missing from the persona.

## Why 90% is the wrong target

### 1. The person does not repeat themselves

Twin-2K is the only dataset that measures this directly. The same people,
asked the same items two weeks apart, agree with themselves 81.72% of the time
(Toubia et al. 2025, [arXiv:2505.17479](https://arxiv.org/abs/2505.17479)). A
simulated persona cannot predict the 18% the person changes, because nothing
recorded before the second sitting predicts it.

### 2. Who the person is barely changes the choice

In both conjoints a logistic regression on the nine profile attribute
differences, which never sees who is answering, matches or beats the
simulated persona. It was fit on every respondent outside the 100 and scored
on the same 500 pairs. Hainmueller and Hopkins report the same thing in the
original paper: education, party, job and ethnocentrism barely move which
profile wins. When the choice is mostly consensus, a persona has little to
add, and the ceiling is the consensus, not 90%.

This regression saw thousands of other people's real choices. The simulated
persona saw one person's facts and the pair. They are not the same kind of
model, so the regression is a reference point, not a direct control.

### 3. The recorded outcome is noisy for reasons the data never captured

MovieLens records a star and a timestamp. It does not record mood, company,
or what else came out that week. Each person's own earlier ratings already
have a standard deviation of 1.01 stars, against 1.12 across everyone.

### 4. The model does not respect a base rate

EB-NeRD is the one dataset where the simulated persona is clearly below what
the data allows. It opens far too many articles. Telling it the person's own
click rate fixed part of the rate and none of the ranking.

## Per dataset

### Twin-2K-500

**What it measures.** 2,058 US adults answered about 500 questions in four
sittings. The score is the fourth sitting, about 84 items per person, mostly
heuristics-and-biases tasks and a pricing study. Single-choice and matrix
items only; five or more options give half credit for a one-step miss.

**Result.** 0.76 with half credit on 100 people. Chance is 0.38 exact, 0.43
with half credit.

**Is it good?** It is at the measurable ceiling, and that ceiling is mostly
memory. All 8,224 scored items on these 100 people were asked in an earlier
sitting, and every earlier answer is in the persona. Copying the earlier
answer scores 0.707 exact and 0.761 with half credit, the same as the model.
Removing those same-item answers dropped a 20-person run to about 0.55.

**Where the ceiling is.** 0.817, human test-retest. The model cannot reach it
by recall alone, because 0.761 is what recall gives.

### Immigration conjoint (Hainmueller & Hopkins 2015)

**What it measures.** US adults saw two invented immigrant profiles and chose
which to admit, five times each. Scored on the forced choice.

**Result.** 359 of 500, accuracy and AUC 0.718. The earlier persona, without
state, the wave-1 immigration attitude, self-monitoring and occupation, scored
about 0.67.

**Is it good?** It equals the population consensus. The profile-only
regression also scores 0.718 on the same 500 pairs. The two numbers landing
on the same value is rounding; the substance is that adding the persona does
not beat a model that ignores the person.

**Where the ceiling is.** Inferred at about the consensus, 0.72 with an
interval up to 0.76. The file has no repeated pair, so the person's own
consistency cannot be measured.

### Bansak asylum conjoint (Bansak, Hainmueller & Hangartner 2016)

**What it measures.** 18,030 voters in 15 European countries chose between two
invented asylum applicants, five times each.

**Result.** 303 of 500, accuracy 0.606, AUC 0.607. Three prompt versions got
the same 303 right:

| Prompt | Accuracy | AUC |
|--------|----------|-----|
| English questionnaire and persona | 0.606 | 0.607 |
| Translated into each country's survey language, party as a number | 0.606 | 0.601 |
| Translated, party as its codebook name | 0.606 | 0.607 |

**Is it good?** Inside the consensus interval. The profile-only regression,
fit on the other 17,930 voters, scores 0.630, interval 0.584–0.678. The
two-point gap is not distinguishable at 100 people, and no paired test was run.

**Where it loses.** The 105 pairs from the Czech Republic, Hungary and Poland
scored 0.505, chance. The other 395 scored 0.633, which is the consensus
level.

**Known presentation gaps.** The translations are a rendering of the English
codebook, not the unpublished Respondi instrument. Switzerland has no
recorded survey language, so its five respondents see English. The shared
persona template wraps every persona in an English "Who you are" block.

### MovieLens 1M

**What it measures.** Real star ratings. Each person's latest 20% of ratings
are held out; every earlier rating, oldest first, is in the persona. The card
is title, year and genres only.

**Result.** MAE 0.73, RMSE 1.02, exact 0.40, within one star 0.88, on 3,064
ratings.

**Is it good?** It ties a baseline made of two numbers: the person's own mean
rating and the movie's mean among other users, rounded to a whole star
(MAE 0.75, RMSE 1.02, exact 0.39, within one 0.88). Unrounded, the same
baseline has a lower RMSE, 0.99, and a higher MAE, 0.80; a whole-star answer
always favours MAE. Splitting the person's history by genre barely helps
(MAE 0.864 against 0.877 for the plain user mean).

**Where the ceiling is.** Within-person spread is about one star. Plot, cast
and reviews would help a recommender, but they are not in the 1M release.

### EB-NeRD (Ekstra Bladet news clicks, RecSys 2024)

**What it measures.** One screen of articles a reader actually saw, about 11
on average (5 to 54), and which one they opened. Each article is a yes or no.
97 of the 100 screens have exactly one click. Everything is in Danish.

**Result.**

| Prompt | Accuracy | AUC | Predicted open rate |
|--------|----------|-----|---------------------|
| Danish, device, paywall, kind, age, page, skipped articles | 0.580 | 0.570 | 0.445 |
| Same, plus the reader's own clicks in the week before | 0.636 | 0.563 | 0.359 |
| True open rate | | | 0.097 |

With the click habit, the model said yes on 394 articles and 50 of them were
opened: precision 0.127 against a base rate of 0.097. It caught 50 of the 106
real opens.

**Is it good?** No. Answering no to everything scores 0.903, but that finds
none of the clicks and has AUC 0.5. Picking one article per screen at random
scores 0.787. The model is below both on accuracy and barely above chance on
ranking.

**Where the gap is.** Calibration first: the model opens three to four times
too many articles even when told its own rate. Ranking second: the click
history helps it guess how often, not which one. The released article order
is shuffled, so the card cannot say where an article sat on the page, and a
screen with no click is not in the file. Before the click habit was added,
six other prompts on the first 20 of these people, including article bodies, a
picture flag and the time of day, all scored lower than the first row of the
table.

## What would test these claims

| Test | Dataset | What would change the conclusion |
|------|---------|----------------------------------|
| Persona-free LLM run on the same cards | All five, especially the conjoints | A clear drop without the persona would mean the persona does add something the profile regression cannot show |
| Allow exactly one click per screen | EB-NeRD | Accuracy staying near 0.64 would mean the article content, not the base rate, is the problem |
| A second model | All five | If another model scores the same, the ceiling is in the data; if it scores higher, it was the model |
| Drop the same-item answers | Twin-2K | Already run on 20 people: about 0.55 |

## Caveats

- Every simulated-persona number here is one model, GLM 5.3.
- The conjoint ceilings are inferred from a regression that saw other people's
  choices. Neither file repeats a pair for the same person.
- These runs used the earlier survey code, which replaced a single-choice answer
  outside the option list with the first option (`yes` in EB-NeRD, `a` in the
  conjoints) and did not store the raw model output, so they cannot show
  whether that happened. The code now fails such a trial instead and keeps the
  raw output; see "Known issues" in `handover.md`.
