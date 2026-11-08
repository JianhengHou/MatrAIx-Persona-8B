# Persona-fit candidate notes

Working notes for datasets under review. A dataset stays a candidate until the
persona contents are settled. These notes are not the run instructions; those
are in [persona-fit.md](persona-fit.md).

## Twin-2K-500 (candidate)

A long survey of real people, not a preference task. 2,058 US adults answered
about 500 questions each, in four sittings. Two weeks later the same people
were asked some of those questions again. The test is what they say the second
time. Toubia et al. 2025, [arXiv:2505.17479](https://arxiv.org/abs/2505.17479).
The paper's own human test-retest accuracy on
those items is 81.72%, and that number is a ceiling, not our score.
the same items two weeks later. The paper's own human test-retest accuracy on
those items is 81.72%, and that number is a ceiling, not our score.

One person answers, in one sitting, only the wave-4 items that person was
shown (about 80-84 of 108 scoreable items). The persona holds demographics,
the Big Five, and the wave 1-3 answers. Whether answers to the same items are
kept in the persona is not settled, so inclusion is not settled either.
Keeping them turns the task into recall of the previous answer.

Scoring covers single-choice and matrix items only. Five or more options give
half credit for a one-step miss. Chance on the 20-person sample is about 0.38.

| Persona | Sample | Model | Accuracy |
|---------|--------|-------|----------|
| Same-item answers kept | 100 people | GLM | 0.76 (100/100 finished) |

Copying the earlier answer verbatim matches 0.70 of the original 20-person
items. The 0.76 is higher than that because a neighbouring option still earns
half credit. Removing the same-item answers drops a 20-person run to about
0.55 with half credit, and Astra on the 100 people stopped at 45 of 100 on a
credit limit, at 0.75.

### Skew

The dataset leans toward cognition and perception, not preference.

The unscored free-entry and slider items were asked of the real people, and
their answers sit in the persona, but none of them enter the accuracy. Most of
them test the person rather than ask what the person would choose:

- Cognitive reflection and numeracy: the bat-and-ball price, the lily-pad
  lake, the widget machines, the hole full of dirt, credit-card payoff time.
- Self-assessment: how many of 42 cognitive items the person got right, and
  how many an average adult would.
- Anchored estimates: how many African countries are in the United Nations,
  how tall the tallest redwood is, in feet.
- Probability and perception: the lawyer/engineer slider, and a 0-100 slider
  for what share of the public supports a policy.

The scored wave-4 block has the same lean. It repeats heuristics-and-biases
tasks (conjunction, anchoring, probability matching) plus a pricing study.
Demographics, the Big Five, and purchase choices are in the data, but they do
not balance a battery built to test reasoning and perception.

## Immigration conjoint (candidate)

A survey choice, not a real visa decision. Each person saw two made-up
immigrant profiles side by side and picked which one should be admitted to
the United States. Almost everyone did this five times. Hainmueller and
Hopkins 2015, AJPS, [doi:10.7910/DVN/25505](https://doi.org/10.7910/DVN/25505).
After dropping rows without a weight
or a complete profile, 1,404 people remain; 1,396 of them saw five pairs, and
the rest saw three or four. Each pair is two invented immigrant profiles,
side by side, with nine attributes (education, gender, origin, reason, job,
experience, plans, prior trips, English).

One person is one job. The questionnaire shows the pairs that person actually
saw and scores only the forced choice. The 7-point admit rating of each
profile is recorded and not scored. The 1-99 likelihood was never asked, so
    it is not asked here. The     persona is age, education, ethnicity, gender,
    income, the state they live in (Knowledge Networks `ppstaten`, not the
    census division it was previously collapsed to; the division is kept as
    well), party, ideology, five 0-100 feeling thermometers from wave 1,
    the wave-1 immigration-attitude answer (`W1_Q4`), the three wave-1
    self-monitoring answers (`W1_Q1` to `W1_Q3`, kept as the stored 1-5 code
    because the survey randomized response polarity), and the respondent's
    own occupation where one of the eleven job dummies matches. A missing
    thermometer is written `N/A`. Of the 100 scored people, 99 answered the
    attitude item, all 100 answered the self-monitoring items, and 11 matched
    an occupation.

Chance on a pair is 0.50. There is no persona-free run, so a right answer is
not yet separated from the consensus ("college, fluent English, has a job").
The paper's own finding is that the respondent's education, party, job, and
ethnocentrism barely change which profile wins. On the first 20 people a
hand-built consensus ranking matched the human on 55/100 pairs and the model
on 63/100; 18 of the 28 misses were the model following that ranking where
the person did not. Attribute order on the real screen was randomized per
person and is not in the file; the paper says it barely matters.

| Sample | Persona | Model | Forced-choice accuracy |
|--------|---------|-------|------------------------|
| 100 people, 500 pairs | Current, with the attitude, self-monitoring, and occupation | GLM | 0.718 (359/500), AUC 0.718 |

The same 100 people scored about 0.67 on the earlier persona, which omitted
the state, the attitude, the self-monitoring answers, and the occupation.
Adding what the person already knew barely moves the result, which matches
the paper: the respondent's education, party, job, and ethnocentrism barely
change which profile wins.

## Asylum conjoint (candidate)

The same kind of survey as the immigration one, with European voters and
asylum applicants. Each person saw two made-up applicant profiles and picked
which one should get asylum. This is what they said on a questionnaire, not
a real asylum decision. Bansak, Hainmueller and Hangartner 2016, Science,
[doi:10.7910/DVN/KL0FDF](https://doi.org/10.7910/DVN/KL0FDF).
18,030 voters, each
shown exactly five pairs. Each pair is two invented asylum-seeker profiles
with nine attributes (testimony consistency, gender, origin, age, occupation,
vulnerability, reason, religion, host-country language).

One person is one job. The questionnaire shows that person's five pairs and
scores only the forced choice. The 1-7 rating of each profile is recorded and
not scored. The 1-99 likelihood was never asked, so it is not asked here. The
persona is country, gender, age, education, income decile, left-right
self-placement, employment, whether the respondent was born in that
country, how many asylum seekers the country should accept, the party they
feel closest to (a within-country code, since the codebook's party names
are not in the file), and the two empathy items. Their sum (`Empathy`) is
not repeated. Counts computed from the choices (`NAsySeek*`, `Cat*`) stay
out of the persona. All 100 scored people have the birth, asylum-preference,
party, and empathy answers. Every pair is a new draw, so there is no earlier
answer to copy.

Chance on a pair is 0.50. There is no persona-free run. A hand-built ranking
(consistent testimony, fluent host-country language, occupation, a
non-economic reason) is an audit check, not the paper's estimate. The model
followed it more often than the people did.

| Sample | Persona | Model | Forced-choice accuracy |
|--------|---------|-------|------------------------|
| 100 people, 500 pairs | Current | GLM | 0.606 (303/500), AUC 0.607 |

The same 100 people scored 0.60 (298/500) on the earlier persona, which
omitted birth, the asylum preference, the party, and the two empathy items.
Adding what the person already knew does not move the result.

All 500 items were checked: question id, pair number, stored answer, and the
origin shown on the card matched. The drop in the second sample is the
sample, not a mispaired task. Those 80 include 21 respondents in the Czech
Republic, Hungary, and Poland; the first 20 include none. Those 105 Eastern
European pairs scored 0.50. The other 295 scored 0.61.

## MovieLens 1M (candidate)

Real star ratings from a movie website, not a quiz and not a made-up profile.
6,040 people gave 1,000,209 ratings, each a whole number from 1 to 5. The
latest 20% of each person's ratings are held out. One person is one job, and
    the form lists every movie held out for that person. The persona keeps gender,
    age band, occupation, where the account's zip code is, and every earlier
    rating, oldest first. A street zip becomes the city or town and county it
    falls in (Census 2020 ZIP Code Tabulation Areas); a PO-box or military zip,
    which has no such area, keeps only its state. The card is title, year, and
    genres. No plot, cast, or reviews.
    Harper and Konstan 2015,
[doi:10.1145/2827872](https://doi.org/10.1145/2827872).

A star rating is a number, so the score is the size of the error, not the
share of exact matches. Exact match treats one star off the same as four
stars off. MSE is the mean squared error. RMSE is its square root, in stars.
MAE is the average number of stars off. The reward stored on a job is
neither: one star off scores 0.75 there. There is no persona-free run, so
this does not separate the person's taste from how popular the movie already
is.

| Sample | Movies | MSE | RMSE | MAE | Exact | Within one star |
|--------|--------|-----|------|-----|-------|-----------------|
| 100 people | 3,064 | 1.05 | 1.02 | 0.73 | 1,238/3,064 (0.40) | 2,693/3,064 (0.88) |

All 100 people finished, and every held-out movie was answered. Held-out
movies were checked against the persona by title and year; the same title in
another year is a different movie and is not a leak.

## EB-NeRD (candidate)

Real clicks on Ekstra Bladet, a Danish newspaper, not a quiz and not a rating.
Each reader is shown screens of articles; the recorded outcome is which
article on that screen they opened. Kruse et al., RecSys 2024,
[arXiv:2403.04592](https://arxiv.org/abs/2403.04592). Research licence: no
redistribution, and the files are not for training a language model.

The local file is `ebnerd_small`, one of three sizes of the same release
(demo, small, large). The full release has 1,103,602 readers, 125,541
articles, and 37,966,985 impressions. The competition test week (1–8 Jun
2023) is a separate download with the click labels removed, and it is not in
the local file, so its overlap was not counted. Counts in the local small
file:

| Week | When | Impressions | Readers | With age or gender |
|------|------|-------------|---------|--------------------|
| Train | 18–25 May 2023 | 232,887 | 15,143 | 657 |
| Validation | 25 May–1 Jun 2023 | 244,647 | 15,342 | 635 |

The anonymized user id is stable across weeks. 11,658 readers are in both
weeks, and the two weeks together hold 18,827 distinct readers. Only readers
with an age or a gender can be a persona, so the pool is the 635 known
readers of the validation week. The 100 scored people are a seeded draw of
those 635, about a sixth of them and 0.65% of all 15,342.

The exam is the validation week. One questionnaire is that reader's earliest
screen in it, and each article on the screen is a yes or no. The released
list was shuffled, so the order on the card is not the order on the page.
Every screen has at least one click; the 100 screens are 1,098 articles,
median 8, and 106 of them were opened (0.097).

What the current prompt carries, in Danish. The stored answer ids stay yes
and no.

- Persona: gender, age band, whether they subscribe, the kind of area the
  postcode is in, the device that screen was on, and the date, May 2023.
- Opened history: every article opened in the three weeks before, oldest
  first, with section, title, subtitle, seconds read, and scroll depth. A
  missing scroll is left out. No article text.
- Negatives: every article shown but not opened in the week just before the
  exam, once, with section, title, and subtitle. The released history is
  clicks only, so these come from the train week. 93 of the 100 have at least
  one.
- Card: whether the screen was the front page or the foot of a named article.
- Each article: section, title, subtitle, the paywall (and whether this
  account subscribes), the kind when it is a video, a gallery, a live blog,
  an ad, or a comment, and the age when it came out at least a week earlier.
  An ordinary new text article gets none of that.

Not carried: article text, whether it has a picture, the time of day, the
scored screen's own read time and scroll, and the catalog-wide view and click
counts. Those counts cover the first seven days after publication, so an
article published inside the exam week would carry clicks from that week.

| Sample | Prompt | Accuracy | AUC | Predicted open rate |
|--------|--------|----------|-----|---------------------|
| 100 people, 1,098 articles | Danish, with device, paywall, kind, article age, page, and skipped articles | 0.580 | 0.570 | 0.445 |

The observed open rate on these 1,098 articles is 0.097, so the model opens
far more articles than the readers did. The same prompt on the first 20 of
these 100 scored 0.696 (270 articles, observed 0.081), which does not hold
for the other 80 (0.539). Six other prompts on those 20, including article
text, a picture flag, and the time of day, all scored lower.
