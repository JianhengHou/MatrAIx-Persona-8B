"""08 MovieLens 1M (Harper & Konstan 2015, doi:10.1145/2827872).

Persona: gender, age band, occupation, where the account's zip code is,
plus every earlier rating.
Card: one form of the movies held out for that user (title, year, genres).
Outcome: the star rating of each movie. Only the latest 20% of each user's
ratings (by timestamp) can be scored; every earlier rating is in the persona,
so a scored rating never appears in it.
Research licence: no redistribution, so everything derived from the files
stays under gitignored paths.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

from ..spec import Card, DatasetAdapter, PersonaSpec, RawFile, as_int, coded_overlay, is_missing, rating_question

AGE = {1: "Under 18", 18: "18-24", 25: "25-34", 35: "35-44", 45: "45-49", 50: "50-55", 56: "56+"}
OCCUPATION = {
    0: "other or not specified", 1: "academic/educator", 2: "artist", 3: "clerical/admin",
    4: "college/grad student", 5: "customer service", 6: "doctor/health care", 7: "executive/managerial",
    8: "farmer", 9: "homemaker", 10: "K-12 student", 11: "lawyer", 12: "programmer", 13: "retired",
    14: "sales/marketing", 15: "scientist", 16: "self-employed", 17: "technician/engineer",
    18: "tradesman/craftsman", 19: "unemployed", 20: "writer",
}
# USPS three-digit sectional center ranges. The first matching range wins, so the
# military and Maine exceptions precede the state they sit inside numerically.
ZIP3_RANGES = (
    (90, 99, "Armed Forces"), (340, 346, "Armed Forces"),
    (6, 9, "Puerto Rico"), (969, 969, "Guam"),
    (10, 27, "Massachusetts"), (28, 29, "Rhode Island"), (30, 38, "New Hampshire"),
    (39, 49, "Maine"), (55, 55, "Maine"), (50, 54, "Vermont"), (56, 59, "Vermont"),
    (60, 69, "Connecticut"), (70, 89, "New Jersey"),
    (5, 5, "New York"), (100, 149, "New York"),
    (150, 196, "Pennsylvania"), (197, 199, "Delaware"),
    (200, 205, "District of Columbia"), (569, 569, "District of Columbia"),
    (206, 219, "Maryland"), (220, 246, "Virginia"), (247, 269, "West Virginia"),
    (270, 289, "North Carolina"), (290, 299, "South Carolina"),
    (300, 319, "Georgia"), (398, 399, "Georgia"),
    (320, 339, "Florida"), (347, 347, "Florida"), (349, 349, "Florida"),
    (350, 369, "Alabama"), (370, 385, "Tennessee"), (386, 397, "Mississippi"),
    (400, 427, "Kentucky"), (430, 459, "Ohio"), (460, 479, "Indiana"),
    (480, 499, "Michigan"), (500, 528, "Iowa"), (530, 549, "Wisconsin"),
    (550, 567, "Minnesota"), (570, 577, "South Dakota"), (580, 588, "North Dakota"),
    (590, 599, "Montana"), (600, 629, "Illinois"), (630, 658, "Missouri"),
    (660, 679, "Kansas"), (680, 693, "Nebraska"), (700, 714, "Louisiana"),
    (716, 729, "Arkansas"), (730, 749, "Oklahoma"),
    (750, 799, "Texas"), (885, 885, "Texas"),
    (800, 816, "Colorado"), (820, 831, "Wyoming"), (832, 838, "Idaho"),
    (840, 847, "Utah"), (850, 865, "Arizona"), (870, 884, "New Mexico"),
    (889, 898, "Nevada"), (900, 961, "California"), (967, 968, "Hawaii"),
    (970, 979, "Oregon"), (980, 994, "Washington"), (995, 999, "Alaska"),
)


def _zip3_state(prefix: int) -> str | None:
    return next((name for start, end, name in ZIP3_RANGES if start <= prefix <= end), None)


def _place(name: str) -> str:
    """Census place name without its class suffix: 'New York city' -> 'New York'."""
    return re.sub(r" (city|town|village|CDP|borough|municipality|comunidad|zona urbana|urbanización)$", "", name)


@lru_cache(maxsize=1)
def _zip_places() -> dict[str, tuple[str, str]]:
    """Five-digit zip -> (largest overlapping place, county).

    Census 2020 ZCTA relationship files. A ZCTA is the area where that zip is
    the most common one, so a PO-box-only zip has no row and is not mapped.
    """
    base = Path(__file__).resolve().parents[3] / "data" / "persona_fit" / "ref"
    county = pd.read_csv(base / "zcta_county.txt", sep="|", dtype=str, encoding="utf-8-sig")
    place = pd.read_csv(base / "zcta_place.txt", sep="|", dtype=str, encoding="utf-8-sig")
    county["part"] = pd.to_numeric(county["AREALAND_PART"], errors="coerce").fillna(0)
    place["part"] = pd.to_numeric(place["AREALAND_PART"], errors="coerce").fillna(0)
    county = county.sort_values("part", ascending=False).drop_duplicates("GEOID_ZCTA5_20")
    place = place[place["NAMELSAD_PLACE_20"].notna() & (place["part"] > 0)]
    place = place.sort_values("part", ascending=False).drop_duplicates("GEOID_ZCTA5_20")
    places = dict(zip(place["GEOID_ZCTA5_20"], place["NAMELSAD_PLACE_20"].map(_place)))
    return {
        code: (places.get(code, ""), county_name)
        for code, county_name in zip(county["GEOID_ZCTA5_20"], county["NAMELSAD_COUNTY_20"])
    }


def _where(zip_code: str) -> str | None:
    """Place and county for a street zip; state only when the zip has no area."""
    code = re.match(r"^(\d{5})", zip_code.strip())
    if not code:
        return None
    prefix = int(code.group(1)[:3])
    state = _zip3_state(prefix)
    found = _zip_places().get(code.group(1))
    if found:
        place, county = found
        where = ", ".join(part for part in (place, county) if part)
        return "{}, {}".format(where, state) if state else where
    return state


SLUG = "movielens-1m"
AGE_OVERLAY = coded_overlay(SLUG, "age_band", "Age band", AGE)
OCCUPATION_OVERLAY = coded_overlay(SLUG, "occupation", "Occupation", OCCUPATION)
SCORED_FRACTION = 0.2


def _split_title(title: str) -> tuple[str, int | None]:
    match = re.match(r"^(.*)\s\((\d{4})\)\s*$", str(title))
    if not match:
        return str(title), None
    return match.group(1), int(match.group(2))


class MovieLens1M(DatasetAdapter):
    slug = SLUG
    sheet_id = "08"
    title = "MovieLens 1M ratings"
    path = "application"
    decision_type = "rating"
    domain = "entertainment"
    raw_files = (
        RawFile(
            "ml-1m.zip",
            "https://files.grouplens.org/datasets/movielens/ml-1m.zip",
            "GroupLens research licence: cite Harper & Konstan 2015; no redistribution.",
            unzip=True,
        ),
    )
    persona_fields = ("gender", "age", "occupation", "zip")
    card_fields = ("movie_id", "movie_title", "year", "genres")
    leakage_fields = ("rating", "timestamp")
    overlay_dimensions = (AGE_OVERLAY, OCCUPATION_OVERLAY)
    rating_range = (1, 5)
    metric_key = "stars"
    # People, not ratings. Each person rates every held-out movie in one job.
    default_sample_rows = 20
    instruction_md = (
        "# Rate these movies\n\n"
        "It is the early 2000s. Each movie below is one you have not rated yet. Say how many "
        "stars you give it on a 1-5 scale, the way you rate movies on a movie-recommendation "
        "website (5 = loved it, 1 = hated it).\n\n"
        "## How to answer\n\n"
        "- Rate every movie.\n"
        "- Give a whole number from 1 to 5.\n"
    )

    @property
    def uses_history(self) -> bool:
        return True

    def load(self, raw: Path) -> pd.DataFrame:
        base = raw / "ml-1m"
        for name in ("users.dat", "movies.dat", "ratings.dat"):
            if not (base / name).is_file():
                raise FileNotFoundError("{}: expected {} (run download)".format(self.slug, base / name))
        users = pd.read_csv(base / "users.dat", sep="::", engine="python", names=["user_id", "gender", "age", "occupation", "zip"])
        movies = pd.read_csv(base / "movies.dat", sep="::", engine="python", names=["movie_id", "title", "genres"], encoding="latin-1")
        ratings = pd.read_csv(base / "ratings.dat", sep="::", engine="python", names=["user_id", "movie_id", "rating", "timestamp"])
        movies["movie_title"], movies["year"] = zip(*movies["title"].map(_split_title))
        df = ratings.merge(users, on="user_id").merge(movies, on="movie_id")
        df["row_id"] = df["user_id"].astype(str) + "-" + df["movie_id"].astype(str)
        df["person_id"] = df["user_id"].astype(str)
        df["outcome"] = df["rating"].astype(int)
        return df

    def eligible(self, frame: pd.DataFrame) -> pd.Series:
        """Latest ``SCORED_FRACTION`` of each user's ratings by timestamp."""
        order = frame.groupby("person_id")["timestamp"].rank(method="first", ascending=True)
        counts = frame.groupby("person_id")["timestamp"].transform("count")
        held_out = (counts * SCORED_FRACTION).round().clip(lower=1)
        return order > (counts - held_out)

    def persona(self, person_rows: pd.DataFrame, history: pd.DataFrame | None = None) -> PersonaSpec:
        r = person_rows.iloc[0]
        dims = {"gender_identity": {"F": "Woman", "M": "Man"}.get(str(r.get("gender"))), "region": "North America"}
        overlays = {
            AGE_OVERLAY.id: AGE.get(as_int(r.get("age"))),
            OCCUPATION_OVERLAY.id: OCCUPATION.get(as_int(r.get("occupation"))),
        }
        facts = ["It is the early 2000s. You rate movies on a movie-recommendation website."]
        where = None if is_missing(r.get("zip")) else _where(str(r.get("zip")))
        if where:
            facts.append("You live in {}.".format(where))
        if history is not None and len(history):
            ordered = history.sort_values(["timestamp", "movie_id"], ascending=[True, True])
            facts.append("You have rated {} movies so far; your average is {:.1f} stars.".format(len(ordered), ordered["outcome"].mean()))
            rated = "; ".join(
                "{} ({}) {}*".format(title, year, int(stars))
                for title, year, stars in zip(ordered["movie_title"], ordered["year"], ordered["outcome"])
            )
            facts.append("Movies you have rated, oldest first: " + rated)
        return PersonaSpec(display_name="a movie-website user", dimensions=dims, overlays=overlays, facts=facts)

    def _movie_block(self, row: pd.Series, number: int) -> str:
        year = as_int(row.get("year"))
        return "## Movie {}\n\n- **Title:** {}\n- **Year:** {}\n- **Genres:** {}".format(
            number, row["movie_title"], year if year else "unknown", str(row["genres"]).replace("|", ", ")
        )

    def _movie_question(self, row: pd.Series, number: int) -> dict:
        question = rating_question(
            "Movie {}: how many stars (1-5) do you give {}?".format(number, row["movie_title"]), 1, 5
        )
        question["id"] = "q{:03d}".format(number)
        question["construct"] = question["id"]
        return question

    def card(self, row: pd.Series) -> Card:
        return Card("# Movies to rate\n\n{}\n".format(self._movie_block(row, 1)), [self._movie_question(row, 1)])

    def form(self, rows: list[pd.Series]) -> Card:
        ordered = sorted(rows, key=lambda row: (int(row["timestamp"]), str(row["movie_id"])))
        # The caller zips these questions onto the same rows. Both must share this order.
        rows.sort(key=lambda row: (int(row["timestamp"]), str(row["movie_id"])))
        return Card(
            "# Movies to rate\n\n"
            "Movies you have not rated yet. Give each one a star rating.\n\n"
            + "\n\n".join(self._movie_block(row, i) for i, row in enumerate(ordered, start=1))
            + "\n",
            [self._movie_question(row, i) for i, row in enumerate(ordered, start=1)],
        )

    def example_rows(self) -> pd.DataFrame:
        rows = [
            {"user_id": 99001, "movie_id": 1, "movie_title": "Example Comedy", "year": 1995, "genres": "Comedy|Romance",
             "gender": "F", "age": 25, "occupation": 4, "zip": "10027", "rating": 4, "timestamp": 1},
            {"user_id": 99001, "movie_id": 2, "movie_title": "Example Thriller", "year": 1998, "genres": "Thriller",
             "gender": "F", "age": 25, "occupation": 4, "zip": "10027", "rating": 2, "timestamp": 2},
        ]
        df = pd.DataFrame(rows)
        df["row_id"] = df["user_id"].astype(str) + "-" + df["movie_id"].astype(str)
        df["person_id"] = df["user_id"].astype(str)
        df["cluster_id"] = df["person_id"]
        df["outcome"] = df["rating"]
        return df
