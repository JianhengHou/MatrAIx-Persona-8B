"""07 Hainmueller & Hopkins immigration conjoint (AJPS replication, doi:10.7910/DVN/25505).

Persona: respondent demographics, the state they live in, party, ideology, group feeling thermometers.
Card: the five side-by-side pairs that one respondent actually saw, as one
questionnaire. Outcome: which profile in each pair the respondent preferred
for admission. The 7-point rating of each profile is recorded but not scored,
and the 1-99 likelihood was never asked of the real people, so it is not
asked here. Stated preference (SP). Restricted to the 1,407 wave-2 completers
that carry ``weight2``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..spec import (
    Card,
    DatasetAdapter,
    PersonaSpec,
    RawFile,
    as_int,
    choice_question,
    code_label,
    coded_overlay,
    read_delimited,
)
from ._pairs import pair_options, pair_table, to_pairs

ATTRS = ("FeatEd", "FeatGender", "FeatCountry", "FeatReason", "FeatJob", "FeatExp", "FeatPlans", "FeatTrips", "FeatLang")
LEVELS = {
    "FeatGender": ("Gender", {1: "Female", 2: "Male"}),
    "FeatEd": ("Education", {1: "No formal education", 2: "Equivalent to completing fourth grade", 3: "Equivalent to completing eighth grade",
                             4: "Equivalent to completing high school", 5: "Equivalent to completing two years of college",
                             6: "Equivalent to completing a college degree", 7: "Equivalent to completing a graduate degree"}),
    "FeatLang": ("Language", {1: "During admission interview, this applicant spoke fluent English",
                              2: "During admission interview, this applicant spoke broken English",
                              3: "During admission interview, this applicant tried to speak English but was unable",
                              4: "During admission interview, this applicant spoke through an interpreter"}),
    "FeatCountry": ("Country of origin", {1: "Germany", 2: "France", 3: "Mexico", 4: "Philippines", 5: "Poland",
                                          6: "India", 7: "China", 8: "Sudan", 9: "Somalia", 10: "Iraq"}),
    "FeatJob": ("Profession", {1: "Janitor", 2: "Waiter", 3: "Child care provider", 4: "Gardener", 5: "Financial analyst",
                               6: "Construction worker", 7: "Teacher", 8: "Computer programmer", 9: "Nurse",
                               10: "Research scientist", 11: "Doctor"}),
    "FeatReason": ("Reason for application", {1: "Reunite with family members already in U.S.",
                                              2: "Seek better job in U.S.",
                                              3: "Escape political/religious persecution"}),
    "FeatExp": ("Job experience", {1: "No job training or prior experience", 2: "One to two years of job training and experience",
                                   3: "Three to five years of job training and experience", 4: "More than five years of job training and experience"}),
    "FeatPlans": ("Employment plans", {1: "Has a contract with a U.S. employer", 2: "Has done job interviews with a U.S. employer but does not have a contract",
                                       3: "Will look for work after arriving in the U.S.", 4: "Does not have plans to look for work at this time"}),
    "FeatTrips": ("Prior trips to the U.S.", {1: "Has never been to the U.S.", 2: "Entered the U.S. once before on a tourist visa",
                                              3: "Entered the U.S. multiple times before on tourist visas",
                                              4: "Spent six months with family members in the U.S.",
                                              5: "Entered the U.S. once before without legal authorization"}),
}
EDUCATION = {1: "Less than high school", 2: "High school", 3: "Some college", 4: "Bachelor's degree or higher"}
ETHNICITY = {1: "White, non-Hispanic", 2: "Black, non-Hispanic", 3: "Other, non-Hispanic", 4: "Hispanic", 5: "Two or more races, non-Hispanic"}
PARTY = {1: "Strong Republican", 2: "Not strong Republican", 3: "Leans Republican", 4: "Independent / undecided",
         5: "Leans Democrat", 6: "Not strong Democrat", 7: "Strong Democrat"}
IDEOLOGY = {1: "Extremely liberal", 2: "Liberal", 3: "Slightly liberal", 4: "Moderate, middle of the road",
            5: "Slightly conservative", 6: "Conservative", 7: "Extremely conservative"}
INCOME = {1: "Less than $5,000", 2: "$5,000-$7,499", 3: "$7,500-$9,999", 4: "$10,000-$12,499", 5: "$12,500-$14,999",
          6: "$15,000-$19,999", 7: "$20,000-$24,999", 8: "$25,000-$29,999", 9: "$30,000-$34,999", 10: "$35,000-$39,999",
          11: "$40,000-$49,999", 12: "$50,000-$59,999", 13: "$60,000-$74,999", 14: "$75,000-$84,999",
          15: "$85,000-$99,999", 16: "$100,000-$124,999", 17: "$125,000-$149,999", 18: "$150,000-$174,999", 19: "$175,000 or more"}
DIVISION = {1: "New England", 2: "Middle Atlantic", 3: "East North Central", 4: "West North Central", 5: "South Atlantic",
            6: "East South Central", 7: "West South Central", 8: "Mountain", 9: "Pacific"}
# Knowledge Networks ppstaten: division digit, then the state within that division. Not FIPS.
STATE = {
    11: "Maine", 12: "New Hampshire", 13: "Vermont", 14: "Massachusetts", 15: "Rhode Island", 16: "Connecticut",
    21: "New York", 22: "New Jersey", 23: "Pennsylvania",
    31: "Ohio", 32: "Indiana", 33: "Illinois", 34: "Michigan", 35: "Wisconsin",
    41: "Minnesota", 42: "Iowa", 43: "Missouri", 44: "North Dakota", 45: "South Dakota", 46: "Nebraska", 47: "Kansas",
    51: "Delaware", 52: "Maryland", 53: "District of Columbia", 54: "Virginia", 55: "West Virginia",
    56: "North Carolina", 57: "South Carolina", 58: "Georgia", 59: "Florida",
    61: "Kentucky", 62: "Tennessee", 63: "Alabama", 64: "Mississippi",
    71: "Arkansas", 72: "Louisiana", 73: "Oklahoma", 74: "Texas",
    81: "Montana", 82: "Idaho", 83: "Wyoming", 84: "Colorado", 85: "New Mexico", 86: "Arizona", 87: "Utah", 88: "Nevada",
    91: "Washington", 92: "Oregon", 93: "California", 94: "Alaska", 95: "Hawaii",
}
THERMOMETERS = (("W1_Q5", "Hispanics"), ("W1_Q6", "immigrants"), ("W1_Q7", "Asian Americans"), ("W1_Q8a", "whites"), ("W1_Q8b", "blacks"))

# Wave-1 self-monitoring items (Snyder 1974, via Berinsky and Lavine 2011).
# The appendix randomizes item order and response polarity, so the stored
# 1-5 code cannot be turned back into a category. W1_Q4 is the immigration
# attitude item; its five-point scale is the standard ANES wording.
SELF_MONITORING = (
    ("W1_Q1", "When you're with other people, how often do you put on a show to impress or entertain them?"),
    ("W1_Q2", "How good or bad of an actor would you be?"),
    ("W1_Q3", "When you are in a group of people, how often are you the center of attention?"),
)
IMMIGRATION_ATTITUDE = {
    1: "increased a lot",
    2: "increased a little",
    3: "remain the same as it is",
    4: "reduced a little",
    5: "reduced a lot",
}

# The respondent's own occupation, coded as the same jobs shown on the
# immigrant profiles. The file stores one dummy per job; a person matches at
# most one.
OWN_JOB = (
    ("OCC_JA", "janitor"),
    ("OCC_WA", "waiter"),
    ("OCC_CC", "child care provider"),
    ("OCC_GA", "gardener"),
    ("OCC_FA", "financial analyst"),
    ("OCC_CO", "construction worker"),
    ("OCC_TE", "teacher"),
    ("OCC_CP", "computer programmer"),
    ("OCC_NU", "nurse"),
    ("OCC_RS", "research scientist"),
    ("OCC_DR", "doctor"),
)
SLUG = "immigration-conjoint"
OVERLAYS = {
    "ppeducat": (coded_overlay(SLUG, "education", "Education", EDUCATION), EDUCATION),
    "ppethm": (coded_overlay(SLUG, "race_ethnicity", "Race / ethnicity", ETHNICITY), ETHNICITY),
    "ppincimp": (coded_overlay(SLUG, "household_income", "Household income", INCOME), INCOME),
    "Party_ID": (coded_overlay(SLUG, "party_id", "Party identification", PARTY), PARTY),
    "Ideology": (coded_overlay(SLUG, "ideology", "Political ideology", IDEOLOGY), IDEOLOGY),
}
DIVISION_OVERLAY = coded_overlay(SLUG, "census_division", "US census division you live in", DIVISION)
STATE_OVERLAY = coded_overlay(SLUG, "state", "US state you live in", STATE)


class ImmigrationConjoint(DatasetAdapter):
    slug = "immigration-conjoint"
    sheet_id = "07"
    title = "Hainmueller & Hopkins immigration conjoint"
    path = "application"
    decision_type = "pair"
    domain = "politics"
    stated_preference = True
    raw_files = (
        RawFile("repdata.tab", "https://dataverse.harvard.edu/api/access/datafile/2461737",
                "AJPS replication file doi:10.7910/DVN/25505 (CC0). Not the thinner THJYQR extract."),
    )
    persona_fields = (
        "ppage", "ppeducat", "ppethm", "ppgender", "ppincimp", "ppstaten",
        "Party_ID", "Ideology",
        *(c for c, _ in THERMOMETERS),
        *(c for c, _ in SELF_MONITORING), "W1_Q4",
        *(c for c, _ in OWN_JOB),
    )
    card_fields = tuple("{}_{}".format(a, s) for a in ATTRS for s in ("a", "b"))
    leakage_fields = ("Chosen_Immigrant", "Support_Admission", "Rating_Immigrant", "W2_Q16")
    overlay_dimensions = (*(o for o, _ in OVERLAYS.values()), DIVISION_OVERLAY, STATE_OVERLAY)
    options = pair_options("Immigrant")
    positive_option = "a"
    metric_key = "chose_first"
    # People, not pairs. Each person answers all five pairs in one job.
    default_sample_rows = None
    instruction_md = (
        "# Immigration admission choice\n\n"
        "It is January 2012.\n\n"
        "You will see five pairs. Each pair is two people applying for admission to the "
        "United States, shown side by side, the way they were shown to you.\n\n"
        "For each pair, if you had to choose, which of the two immigrants should be given "
        "priority to come to the United States to live?\n\n"
        "## How to answer\n\n"
        "- Answer every pair.\n"
        "- Use the listed option ids.\n"
    )

    def load(self, raw: Path) -> pd.DataFrame:
        df = read_delimited(self.require_file(raw, "repdata.tab"))
        self.check_columns(df, ["CaseID", "contest_no", "weight2", "Chosen_Immigrant", *ATTRS], "repdata.tab")
        df = df[df["weight2"].notna() & df[list(ATTRS)].notna().all(axis=1)].copy()
        for attr in ATTRS:
            df[attr] = df[attr].astype(float).astype(int)
        df["_order"] = range(len(df))
        pairs = to_pairs(df, ["CaseID", "contest_no"], "_order", list(ATTRS), "Chosen_Immigrant")
        pairs["row_id"] = pairs["CaseID"].astype(int).astype(str) + "-" + pairs["contest_no"].astype(int).astype(str)
        pairs["person_id"] = pairs["CaseID"].astype(int).astype(str)
        return pairs

    def persona(self, person_rows: pd.DataFrame, history: pd.DataFrame | None = None) -> PersonaSpec:
        r = person_rows.iloc[0]
        state = as_int(r.get("ppstaten"))
        dims = {"region": "North America", "gender_identity": {1: "Man", 2: "Woman"}.get(as_int(r.get("ppgender")))}
        overlays = {overlay.id: code_label(codes, r.get(col)) for col, (overlay, codes) in OVERLAYS.items()}
        overlays[DIVISION_OVERLAY.id] = DIVISION.get(state // 10) if state else None
        overlays[STATE_OVERLAY.id] = STATE.get(state) if state else None
        facts = ["It is January 2012. You are an adult living in the United States."]
        if as_int(r.get("ppage")) is not None:
            facts.append("Age: {}".format(as_int(r.get("ppage"))))
        thermo = [
            "{} {}".format(group, as_int(r.get(col)) if as_int(r.get(col)) is not None else "N/A")
            for col, group in THERMOMETERS
        ]
        facts.append("Your feeling thermometer ratings, 0 (cold) to 100 (warm): " + ", ".join(thermo))
        for column, question in SELF_MONITORING:
            code = as_int(r.get(column))
            if code is not None:
                facts.append('{} You answered {} on a 1-5 scale.'.format(question, code))
        attitude = code_label(IMMIGRATION_ATTITUDE, r.get("W1_Q4"))
        if attitude:
            facts.append("The number of immigrants to America nowadays should be {}.".format(attitude))
        own_job = [label for column, label in OWN_JOB if as_int(r.get(column)) == 1]
        if own_job:
            facts.append("Your occupation: {}.".format(own_job[0]))
        return PersonaSpec(display_name="an American survey respondent", dimensions=dims, overlays=overlays, facts=facts)

    def _pair_block(self, row: pd.Series, number: int) -> str:
        attributes = []
        for attr in ATTRS:
            label, mapping = LEVELS[attr]
            attributes.append((label, mapping.get(as_int(row[attr + "_a"]), "?"), mapping.get(as_int(row[attr + "_b"]), "?")))
        return "## Pair {}\n\n{}".format(number, pair_table("Immigrant", attributes))

    def _pair_question(self, number: int) -> dict:
        return choice_question(
            "Pair {}: which of these two immigrants should be given priority to come to the United States to live?".format(number),
            pair_options("Immigrant"),
            "q{:03d}".format(number),
        )

    def card(self, row: pd.Series) -> Card:
        return Card(
            "# Immigration pairs\n\n{}\n".format(self._pair_block(row, 1)),
            [self._pair_question(1)],
        )

    def form(self, rows: list[pd.Series]) -> Card:
        ordered = sorted(rows, key=lambda row: int(row["contest_no"]))
        # The caller zips these questions onto the same rows. Both must share this order.
        rows.sort(key=lambda row: int(row["contest_no"]))
        return Card(
            "# Immigration pairs\n\n"
            "Five pairs of applicants for admission to the United States. "
            "For each pair, choose which immigrant gets priority.\n\n"
            + "\n\n".join(self._pair_block(row, i) for i, row in enumerate(ordered, start=1))
            + "\n",
            [self._pair_question(i) for i in range(1, len(ordered) + 1)],
        )

    def example_rows(self) -> pd.DataFrame:
        row = {
            "CaseID": 99001, "contest_no": 1, "weight2": 1.0, "ppage": 45, "ppeducat": 3, "ppethm": 1, "ppgender": 2,
            "ppincimp": 12, "ppstaten": 33, "Party_ID": 5, "Ideology": 4, "W1_Q1": 2, "W1_Q2": 3, "W1_Q3": 4,
            "W1_Q4": 3, "W1_Q5": 60, "W1_Q6": 55, "W1_Q7": 65, "W1_Q8a": 70, "W1_Q8b": None, "OCC_TE": 1,
            "Support_Admission": 1, "Rating_Immigrant": 5, "W2_Q16": 3,
            **{a + "_a": 1 for a in ATTRS}, **{a + "_b": 2 for a in ATTRS},
        }
        df = pd.DataFrame([row, {**row, "contest_no": 2, "FeatEd_a": 6, "FeatJob_b": 11}])
        df["row_id"] = df["CaseID"].astype(str) + "-" + df["contest_no"].astype(str)
        df["person_id"] = df["CaseID"].astype(str)
        df["cluster_id"] = df["person_id"]
        df["outcome"] = ["a", "b"]
        return df
