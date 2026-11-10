# Persona fit: how the five datasets were chosen

This page explains what kind of dataset persona fit needs, how 38 candidates
were graded, why the work ended up with five, and how each of the five was
turned into a task. The full graded catalog, with a reason for every row, is
[`persona_fit_datasets.xlsx`](persona_fit_datasets.xlsx). Its first four sheets
are the reorganised version; the sheets named "Original" are the earlier
catalog exactly as it was.

Results are in [persona-fit-results.md](persona-fit-results.md). How to run the
datasets with another model is in [`handover.md`](../../handover.md).

## What we are looking for

Persona fit asks whether a simulated persona, told what a real person knew
about themselves, makes the same decision that person made. A dataset can test
that only if it has all of these:

1. **A real person's recorded answer or action.** A stated choice in a survey
   counts, but is labelled stated preference; it is not a market decision.
2. **What the person knew about themselves, from before the decision.**
   Demographics, attitudes, earlier answers, earlier behaviour. Nothing measured
   after the decision, and nothing the person never knew (survey weights,
   ecological variables, expert scores).
3. **What the person saw at the decision.** The question and its options, the
   two profiles, the movie, the screen of articles. If the file only says which
   arm someone was in, the simulated persona has nothing to react to.
4. **An outcome that is that decision, in that moment.** Not a stock measured
   years later.
5. **Fields derived from the outcome can be separated out.** Ratings given
   after the choice, counts computed from choices and similar fields must not
   reach the persona.
6. **Traits that actually change the choice.** If everyone picks the same
   profile, a persona has nothing to add, and the ceiling is the consensus.
7. **Ideally, a human ceiling.** The same person answering the same item twice
   shows how consistent people are with themselves.
8. **Public or obtainable**, with enough people to score.

Datasets built for exactly this purpose are rare. Twin-2K-500 is one. Park et
al.'s 1,052-person interview bank is another, but it has no public
individual-level file.

## The tiers

| Tier | Meaning | Count |
|------|---------|-------|
| A | In use: tests one person's own decision | 5 |
| B | Group or treatment response only: the stimulus or the person's history is there, not both | 6 |
| C | Cannot test an individual decision: the stimulus or choice set is missing, there is no readable person, the unit is a household, the data is stated and thin, or the file is not obtainable | 15 |
| D | Not a decision at all (a score, a stock, kWh), or no person file | 12 |

**Tier A**: Twin-2K-500, immigration conjoint, Bansak asylum conjoint,
MovieLens 1M, EB-NeRD.

**Tier B**: Columbia speed dating, Karlan & List, Gerber, Green & Larimer,
Bertrand et al. credit mailer, KDD Cup 1998, LPMC. Each has part of what is
needed. Speed dating has both people's profiles but not the four-minute
conversation the decision was made on. Karlan & List, Gerber and Bertrand
specify the letter, but describe the person only by donation history, the
voter file, or a few demographics. KDD Cup has a long giving history, but every
person got the same letter. LPMC shows the times and costs of every mode, but
the person is a handful of fields. These can test whether a population of
personas reproduces a treatment effect; they are weak tests of one person.

**Tier C**: Hillstrom, Lenta, X5 RetailHero and NHTS 2022, which the original
catalog graded A, plus Moral Machine, dunnhumby, OPeRA, Swissmetro, in-vehicle
coupon, Book-Crossing, MIND, Open Bandit, CES 2024, ODiN 2023 and Date me for
Science.

**Tier D**: Park et al. agent bank, UKHLS, NLSY79, PISA, SCF, RECS, CER smart
meter, Criteo, Bank Marketing, KuaiRand, Online Shoppers, and the
Last.fm/Jester/Airbnb/Acquire exclusion row.

## Why five

The original catalog graded 14 datasets as Fit A, and all 14 were first built
as adapters. Hillstrom was the first to be run at scale: 300 people on GLM 5.3.
It reversed the order of the three email arms and overstated visits and
purchases. Reading the data again showed why. Each Hillstrom row is recency,
past spend, zip type, channel and an arm label. The email, the products it
promoted and the website are not in the file, so a simulated person has
nothing to decide on; only a model of group averages can fit it.

Every row of the catalog was then re-read against two questions: is the
person described from before the decision, and is what they saw in the file?

- Four Fit A rows passed: Twin-2K-500, the immigration conjoint, the Bansak
  asylum conjoint and MovieLens 1M.
- Hillstrom, Lenta, X5 RetailHero and NHTS 2022 failed on the second question
  and moved to tier C. The other six Fit A rows have one half and not the
  other, and moved to tier B.
- In Fit B and Fit C, one row was close enough: EB-NeRD, for readers who gave
  an age or gender. They have 21 days of opened articles, the articles shown
  and skipped, and every article on the screen being scored. It was added as
  the fifth dataset.

The ten other Fit A adapters were then removed, so the repository holds only
the five that test what persona fit is meant to test. None of the ten except
Hillstrom had been run with a model.

## How the tasks are designed

Every task follows the same contract.

- **One real person is one persona and one trial.** The persona is built once
  from what that person knew before the decision. The trial is every item that
  person actually answered, in one model call.
- **The card is what they saw.** Question text and options, both profiles
  attribute by attribute, the movie's title, year and genres, or every article
  on the screen with its section, title, subtitle and paywall.
- **The outcome stays hidden.** It sits only in the task's `tests/labels.json`,
  which the model never sees, and the verifier scores the answer against it.
- **Words, not codes.** A coded field is written as the text the person saw or
  chose: a party name rather than a party number, an occupation rather than a
  code. A scale with no wording per step stays a number with its endpoints.
- **The person's own language and time.** Bansak's questionnaire and persona
  are in each country's survey language; EB-NeRD is in Danish. Where the date
  is known, the prompt says when the decision happened: January 2012, early
  2016, the early 2000s, May 2023. Twin-2K-500 gives no date.
- **A fixed sample.** Bansak uses a fixed fifth of its 18,030 voters; the other
  four use every person they can score. A fingerprint of the scored item ids
  lets any run confirm it holds the same sample.
- **An answer that does not fit fails the trial.** It is never replaced with a
  default, and the model's raw output is kept.

| Dataset | Real or stated | The persona | The card | The answer |
|---------|----------------|-------------|----------|------------|
| Twin-2K-500 | Real survey answers | Demographics, Big Five, every earlier answer | The fourth-sitting questions this person saw | An option per question |
| Immigration conjoint | Stated | Demographics, party, ideology, group thermometers, attitudes, occupation | Five pairs of immigrant profiles | Which one to admit, per pair |
| Bansak asylum conjoint | Stated | Country, demographics, ideology, party, asylum attitude, empathy | Five pairs of asylum applicants, in the country's language | Which one gets asylum, per pair |
| MovieLens 1M | Real | Demographics, town and county, every earlier rating | Each held-out movie | 1-5 stars per movie |
| EB-NeRD | Real | Demographics, device, opened and skipped articles, click counts | One screen of articles, in Danish | Open or not, per article |

The "Final five" sheet of the catalog lists, per dataset, the source, the
standard sample and fingerprint, every persona field, what is kept out, the
metric, the GLM 5.3 reference result and the reference point it is compared
with.

## What changed from the original catalog

1. Fit A was regraded as above.
2. EB-NeRD moved from Fit B to tier A, restricted to readers with a profile, and
   runs as a survey of one screen rather than a web slate.
3. The original rule that a persona must beat a non-LLM logit before any claim
   was dropped. Profile-only regressions and simple baselines are reported as
   reference points, not as a gate.
4. The original "Run order" is superseded by the five datasets here.
