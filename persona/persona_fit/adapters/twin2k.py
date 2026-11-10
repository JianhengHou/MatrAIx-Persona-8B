"""06 Twin-2K-500 (Toubia et al.), Hugging Face LLM-Digital-Twin/Twin-2K-500.

Persona: the respondent's demographics, Big Five scores, and every earlier
answer, including the same items asked again in wave 4. Card: the wave-4
items that person was shown. Outcome: the wave-4 answer. Only single-choice
and Likert-matrix items are scored; text entry, sliders, and multi-select
items are skipped. Keeping the repeated answers makes this a memory test.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from ..spec import (
    Card,
    DatasetAdapter,
    OverlayDim,
    PersonaSpec,
    RawFile,
    as_int,
    choice_question,
    overlay_id,
)

HF = "https://huggingface.co/datasets/LLM-Digital-Twin/Twin-2K-500/resolve/main/question_catalog_and_human_response_csv/"
DEMOGRAPHIC_QIDS = ("QID11", "QID12", "QID13", "QID14", "QID15", "QID16", "QID17", "QID18", "QID19", "QID20", "QID21", "QID22", "QID23", "QID24")
DEMO_LABELS = {
    "QID11": "Region of the US", "QID12": "Sex assigned at birth", "QID13": "Age", "QID14": "Education",
    "QID15": "Race or origin", "QID16": "US citizen", "QID17": "Marital status", "QID18": "Religion",
    "QID19": "Religious service attendance", "QID20": "Party", "QID21": "Family income last year",
    "QID22": "Political views", "QID23": "Household size", "QID24": "Employment",
}
# Standard BFI-44 key (John & Srivastava); item numbers are 1-based row positions.
BFI = {
    "extraversion": (1, -6, 11, 16, -21, 26, -31, 36),
    "agreeableness": (-2, 7, -12, 17, 22, -27, 32, -37, 42),
    "conscientiousness": (3, -8, 13, -18, -23, 28, 33, 38, -43),
    "neuroticism": (4, -9, 14, 19, -24, 29, -34, 39),
    "openness": (5, 10, 15, 20, 25, 30, -35, 40, -41, 44),
}
# Answer options exactly as worded in the survey (question_catalog.json).
DEMO_OPTIONS = {
    "QID11": ("Northeast (PA, NY, NJ, RI, CT, MA, VT, NH, ME)", "Midwest (ND, SD, NE, KS, MN, IA, MO, WI, IL, MI, IN, OH)",
              "South (TX, OK, AR, LA, KY, TN, MS, AL, WV, DC, MD, DE, VA, NC, SC, GA, FL)",
              "West (WA, OR, ID, MT, WY, CA, NV, UT, CO, AZ, NM)", "Pacific (HI, AK)"),
    "QID12": ("Male", "Female"),
    "QID13": ("18-29", "30-49", "50-64", "65+"),
    "QID14": ("Less than high school", "High school graduate", "Some college, no degree", "Associate's degree",
              "College graduate/some postgrad", "Postgraduate"),
    "QID15": ("White", "Black", "Asian", "Hispanic", "Other"),
    "QID16": ("Yes", "No"),
    "QID17": ("Married", "Living with a partner", "Divorced", "Separated", "Widowed", "Never been married"),
    "QID18": ("Protestant", "Roman Catholic", "Mormon", "Orthodox", "Jewish", "Muslim", "Buddhist", "Hindu", "Atheist",
              "Agnostic", "Other", "Nothing in particular"),
    "QID19": ("More than once a week", "Once a week", "Once or twice a month", "A few times a year", "Seldom", "Never"),
    "QID20": ("Republican", "Democrat", "Independent", "Something else"),
    "QID21": ("Less than $30,000", "$30,000-$50,000", "$50,000-$75,000", "$75,000-$100,000", "$100,000 or more"),
    "QID22": ("Very conservative", "Conservative", "Moderate", "Liberal", "Very liberal"),
    "QID23": ("1", "2", "3", "4", "More than 4"),
    "QID24": ("Full-time employment", "Part-time employment", "Unemployed", "Self-employed", "Home-maker", "Student", "Retired"),
}
OVERLAYS = {qid: OverlayDim(overlay_id("twin-2k-500", qid.lower()), DEMO_LABELS[qid], DEMO_OPTIONS[qid]) for qid in DEMOGRAPHIC_QIDS}


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", str(text or ""))
    return re.sub(r"\s+", " ", text).strip()


class Twin2K500(DatasetAdapter):
    slug = "twin-2k-500"
    sheet_id = "06"
    title = "Twin-2K-500 held-out survey items"
    path = "application"
    decision_type = "multinomial"
    domain = "survey-research"
    raw_files = (
        RawFile("question_catalog.json", HF + "question_catalog.json"),
        RawFile("wave1_3_response.csv", HF + "wave1_3_response.csv"),
        RawFile("wave4_response.csv", HF + "wave4_response.csv"),
    )
    persona_fields = (*DEMOGRAPHIC_QIDS, "bfi_extraversion", "bfi_agreeableness", "bfi_conscientiousness", "bfi_neuroticism", "bfi_openness")
    card_fields = ("item_id", "item_text", "item_options")
    leakage_fields = ("answer_position",)
    overlay_dimensions = tuple(OVERLAYS.values())
    metric_key = "answer"
    default_sample_rows = None
    instruction_md = (
        "# Survey\n\n"
        "Answer the survey in the context as yourself, the way you would on an online survey. "
        "These are the questions you were shown. Answer every one.\n\n"
        "## How to answer\n\n"
        "- For each question, pick one of that question's listed option ids.\n"
    )

    def _catalog(self, raw: Path) -> list[dict]:
        return json.loads(self.require_file(raw, "question_catalog.json").read_text(encoding="utf-8"))

    def _items(self, catalog: list[dict], columns: list[str]) -> dict[str, dict]:
        """CSV column -> scoreable item (text + options) for wave-4 columns."""
        items: dict[str, dict] = {}
        for q in catalog:
            selector = (q.get("Settings") or {}).get("Selector")
            text = _clean(q.get("QuestionText"))
            if q["QuestionType"] == "MC" and selector in ("SAVR", "SAHR") and q.get("Options"):
                for col in q["csv_columns"]:
                    if col in columns:
                        items[col] = {"text": text, "options": [_clean(o) for o in q["Options"]], "block": q["BlockName"].strip()}
            elif q["QuestionType"] == "Matrix" and q.get("Columns") and q.get("Rows"):
                row_ids = q.get("RowsID") or [str(i + 1) for i in range(len(q["Rows"]))]
                for col in q["csv_columns"]:
                    if col not in columns:
                        continue
                    sub = col.split("_", 1)[1] if "_" in col else ""
                    row_label = q["Rows"][row_ids.index(sub)] if sub in row_ids else ""
                    items[col] = {
                        "text": "{}\n\nStatement: {}".format(text, _clean(row_label)) if row_label else text,
                        "options": [_clean(o) for o in q["Columns"]],
                        "block": q["BlockName"].strip(),
                    }
        return items

    def _personas(self, catalog: list[dict], wave13: pd.DataFrame) -> pd.DataFrame:
        options = {q["QuestionID"]: q.get("Options") for q in catalog if q["QuestionID"] in DEMOGRAPHIC_QIDS and q["QuestionType"] == "MC"}
        people = pd.DataFrame({"pid": wave13["pid"]})
        for qid in DEMOGRAPHIC_QIDS:
            opts = options.get(qid) or []
            people[qid] = wave13[qid].map(lambda v, o=opts: o[int(v) - 1] if as_int(v) and 0 < int(v) <= len(o) else None)
        bfi = next((q for q in catalog if q["QuestionID"] == "QID25" and q["QuestionType"] == "Matrix"), None)
        if bfi:
            cols = bfi["csv_columns"]
            for trait, key in BFI.items():
                parts = []
                for item in key:
                    col = cols[abs(item) - 1] if abs(item) - 1 < len(cols) else None
                    if col is None or col not in wave13.columns:
                        continue
                    values = pd.to_numeric(wave13[col], errors="coerce")
                    parts.append(6 - values if item < 0 else values)
                if parts:
                    people["bfi_" + trait] = pd.concat(parts, axis=1).mean(axis=1).round(2)
        return people

    def _prior_groups(self, catalog: list[dict], columns: set[str], exam_columns: set[str]) -> list[tuple]:
        """Every earlier answer, in survey order, including items wave 4 asks again."""
        del exam_columns
        groups = []
        for question in catalog:
            present = [col for col in question.get("csv_columns") or [] if col in columns]
            if not present:
                continue
            text = _clean(question.get("QuestionText"))
            kind = question.get("QuestionType")
            selector = (question.get("Settings") or {}).get("Selector")
            if kind == "Matrix" and question.get("Columns") and question.get("Rows"):
                row_ids = question.get("RowsID") or [str(i + 1) for i in range(len(question["Rows"]))]
                choices = [_clean(option) for option in question["Columns"]]
                items = []
                for col in present:
                    sub = col.split("_", 1)[1] if "_" in col else ""
                    row_label = question["Rows"][row_ids.index(sub)] if sub in row_ids else ""
                    items.append((col, _clean(row_label), choices))
                groups.append(("matrix", text, items))
            elif kind == "MC" and question.get("Options"):
                labels = [_clean(option) for option in question["Options"]]
                groups.extend(("single", text, col, labels) for col in present)
            elif kind in {"TE", "Slider"} or selector not in ("SAVR", "SAHR", None):
                groups.extend(("text", text, col) for col in present)
        return groups

    @staticmethod
    def _shown_answer(value: object, labels: list[str]) -> str:
        if pd.isna(value) or str(value).strip() == "":
            return ""
        try:
            position = as_int(value)
        except (TypeError, ValueError, OverflowError):
            position = None
        if labels and position and 0 < int(position) <= len(labels):
            return labels[int(position) - 1]
        return _clean(value)

    def _prior_answers(self, catalog: list[dict], wave13: pd.DataFrame, exam_columns: set[str]) -> pd.Series:
        """Earlier answers that are not the wave-4 exam, keyed by pid."""
        groups = self._prior_groups(catalog, set(wave13.columns), exam_columns)
        rendered = []
        for _, person in wave13.iterrows():
            lines = []
            for group in groups:
                if group[0] == "matrix":
                    _, stem, items = group
                    answers = []
                    for col, row_label, choices in items:
                        shown = self._shown_answer(person.get(col), choices)
                        if shown:
                            answers.append("  - {}: {}".format(row_label or col, shown))
                    if answers:
                        lines.append("- " + stem)
                        lines.extend(answers)
                    continue
                _, stem, col, *rest = group
                shown = self._shown_answer(person.get(col), rest[0] if rest else [])
                if shown:
                    lines.append("- {}: {}".format(stem, shown))
            rendered.append("\n".join(lines))
        return pd.Series(rendered, index=wave13["pid"].astype(str))

    def load(self, raw: Path) -> pd.DataFrame:
        catalog = self._catalog(raw)
        wave13 = pd.read_csv(self.require_file(raw, "wave1_3_response.csv"), low_memory=False)
        wave4 = pd.read_csv(self.require_file(raw, "wave4_response.csv"), low_memory=False)
        items = self._items(catalog, list(wave4.columns))
        long = wave4.melt(id_vars="pid", value_vars=list(items), var_name="item_id", value_name="answer_position")
        long = long[pd.to_numeric(long["answer_position"], errors="coerce").notna()].copy()
        long["answer_position"] = long["answer_position"].astype(float).astype(int)
        long["item_text"] = long["item_id"].map(lambda c: items[c]["text"])
        long["item_options"] = long["item_id"].map(lambda c: items[c]["options"])
        long = long[[0 < p <= len(o) for p, o in zip(long["answer_position"], long["item_options"])]]
        long = long.merge(self._personas(catalog, wave13), on="pid", how="left")
        long.attrs["prior_source"] = (catalog, wave13, set(items))
        long["row_id"] = long["pid"].astype(str) + "-" + long["item_id"]
        long["person_id"] = long["pid"].astype(str)
        long["outcome"] = "o" + long["answer_position"].astype(str)
        return long.reset_index(drop=True)

    def persona(self, person_rows: pd.DataFrame, history: pd.DataFrame | None = None) -> PersonaSpec:
        r = person_rows.iloc[0]
        dims = {
            "region": "North America",
            "gender_identity": {"Male": "Man", "Female": "Woman"}.get(str(r.get("QID12"))),
        }
        overlays = {
            OVERLAYS[qid].id: r.get(qid) for qid in DEMOGRAPHIC_QIDS if isinstance(r.get(qid), str) and r.get(qid)
        }
        facts = ["You live in the United States."]
        traits = [
            "{} {:.1f}".format(t, float(r["bfi_" + t])) for t in BFI if pd.notna(r.get("bfi_" + t))
        ]
        if traits:
            facts.append("Your Big Five personality scores (1-5, from a personality test you took): " + ", ".join(traits))
        prior = person_rows.attrs.get("prior_answers")
        prior = prior.get(str(r["person_id"])) if prior is not None else None
        if isinstance(prior, str) and prior.strip():
            facts.append(
                "Answers you gave when asked these questions before, including questions asked again now:\n"
                + prior
            )
        return PersonaSpec(display_name="an online survey respondent", dimensions=dims, overlays=overlays, facts=facts)

    def _question(self, row: pd.Series, number: int) -> dict:
        options = [("o{}".format(i + 1), label or "Option {}".format(i + 1)) for i, label in enumerate(row["item_options"])]
        return choice_question(str(row["item_text"]), options, "q{:03d}".format(number))

    def card(self, row: pd.Series) -> Card:
        return Card("# Survey\n\nAnswer the question below.\n", [self._question(row, 1)])

    def form(self, rows: list[pd.Series]) -> Card:
        ordered = sorted(rows, key=lambda row: str(row["item_id"]))
        # The caller zips these questions onto the same rows. Both must share this order.
        rows.sort(key=lambda row: str(row["item_id"]))
        return Card(
            "# Survey\n\nAnswer every question below. These are the questions you were shown.\n",
            [self._question(row, i) for i, row in enumerate(ordered, start=1)],
        )

    def example_rows(self) -> pd.DataFrame:
        base = {
            "pid": 99001, "QID11": "Midwest (ND, SD, NE, KS, MN, IA, MO, WI, IL, MI, IN, OH)", "QID12": "Female",
            "QID13": "30-49", "QID14": "College graduate/some postgrad", "QID15": "White", "QID16": "Yes",
            "QID17": "Married", "QID18": "Roman Catholic", "QID19": "Seldom", "QID20": "Independent",
            "QID21": "$50,000-$75,000", "QID22": "Moderate", "QID23": "3", "QID24": "Full-time employment",
            "bfi_extraversion": 3.1, "bfi_agreeableness": 3.9, "bfi_conscientiousness": 4.0,
            "bfi_neuroticism": 2.5, "bfi_openness": 3.6,
        }
        rows = [
            {**base, "item_id": "QID192", "item_text": "Choose between: (example gamble A) and (example gamble B).",
             "item_options": ["Gamble A", "Gamble B"], "answer_position": 1},
            {**base, "item_id": "QID287_1", "item_text": "Would you support or oppose...\n\nStatement: an example policy",
             "item_options": ["Strongly oppose", "Somewhat oppose", "Neither", "Somewhat support", "Strongly support"], "answer_position": 4},
        ]
        df = pd.DataFrame(rows)
        df["row_id"] = df["pid"].astype(str) + "-" + df["item_id"]
        df["person_id"] = df["pid"].astype(str)
        df["cluster_id"] = df["person_id"]
        df["outcome"] = "o" + df["answer_position"].astype(str)
        return df
