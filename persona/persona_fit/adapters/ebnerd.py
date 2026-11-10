"""EB-NeRD (RecSys 2024): real clicks on the Danish newspaper Ekstra Bladet.

One questionnaire is one impression the person actually saw. Each article on
that screen is its own yes/no row ("would you open it"), and the form lists
every article on the screen. The released inview order was shuffled, so the
order on the card is not the order on the page. The exam is the later labeled
week: its history file stops the day before that week, so a scored click is
never in the persona. The     persona carries gender, age band, subscription,
    postcode band, every article opened in the previous 21 days, every article
    shown but not opened in the week just before the exam, and that week's
    click count: articles opened out of articles shown, and how many of those
    screens had exactly one click. A screen with no click is not in the file. Article bodies stay
out, of the screen being scored and of the history. The read time and scroll of
the screen being scored stay out too, as do the catalog-wide view counts, which
keep accumulating after publication. Research licence: no redistribution.
"""

from __future__ import annotations

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
    coded_overlay,
    is_missing,
    overlay_id,
)

GENDER = {0: "mand", 1: "kvinde"}
POSTCODE = {0: "hovedstadsområdet", 1: "landdistrikt", 2: "kommune", 3: "provins", 4: "storby"}
DEVICE = {1: "en computer", 2: "en telefon", 3: "en tablet"}
# What the reader could tell the article was, beyond an ordinary text piece.
ARTICLE_KIND = {
    "article_video_standalone": "en video",
    "article_webtv": "en video",
    "article_fullscreen_gallery": "et billedgalleri",
    "article_scribblelive": "et liveblog",
    "article_native": "en annonce",
    "article_native_feature": "en annonce",
    "article_opinionen": "en kommentar",
}
YES_NO = (("yes", "Ja, jeg ville åbne den"), ("no", "Nej, jeg ville ikke"))
# The later labeled week. Its history ends before its impressions begin.
SPLIT = "validation"
SLUG = "eb-nerd"
GENDER_OVERLAY = coded_overlay(SLUG, "gender", "Køn", GENDER)
POSTCODE_OVERLAY = coded_overlay(SLUG, "postcode", "Område", POSTCODE)
SUBSCRIBER_OVERLAY = OverlayDim(overlay_id(SLUG, "subscriber"), "Abonnement", ("abonnent", "ikke abonnent"))


class EBNeRD(DatasetAdapter):
    slug = SLUG
    sheet_id = "ebnerd"
    title = "EB-NeRD news clicks"
    path = "application"
    decision_type = "binary"
    domain = "news"
    raw_files = (
        RawFile(
            "ebnerd_small.zip",
            note="Sign in at recsys.eb.dk, accept the research terms, and download ebnerd_small. Unzip it here. No redistribution.",
        ),
    )
    persona_fields = ("gender", "age", "postcode", "is_subscriber", "device", "recent_reading", "passed_over", "click_habit")
    card_fields = ("title", "subtitle", "category_str", "premium", "article_kind", "published_time", "page", "when")
    # The impression being scored. Its own read time and scroll are the click
    # after the fact. The same two measures from the earlier history are not.
    # The catalog totals count the first seven days after publication, so an
    # article published inside the exam week carries clicks from that week.
    leakage_fields = (
        "clicked",
        "read_time",
        "scroll_percentage",
        "next_read_time",
        "next_scroll_percentage",
        "body",
        "total_inviews",
        "total_pageviews",
        "total_read_time",
    )
    overlay_dimensions = (GENDER_OVERLAY, POSTCODE_OVERLAY, SUBSCRIBER_OVERLAY)
    options = YES_NO
    positive_option = "yes"
    metric_key = "opened"
    # People, not articles. Each person answers every article on one screen.
    default_sample_rows = None
    instruction_md = (
        "# En skærm på Ekstra Bladet\n\n"
        "Det er maj 2023. Herunder er artiklerne på en skærm, du så. Rækkefølgen er ikke "
        "den, de havde på siden. Sig for hver artikel, om du ville åbne den.\n\n"
        "## Sådan svarer du\n\n"
        "- Svar på hver artikel.\n"
        "- Ja betyder, at du åbner den. Nej betyder, at du ikke gør.\n"
    )

    def load(self, raw: Path) -> pd.DataFrame:
        behaviors = self._parquet(raw, SPLIT + "/behaviors.parquet")
        history = self._parquet(raw, SPLIT + "/history.parquet")
        articles = self._parquet(raw, "articles.parquet")
        self.check_columns(
            behaviors,
            ["impression_id", "user_id", "impression_time", "article_id", "article_ids_inview",
             "article_ids_clicked", "gender", "age", "postcode", "is_subscriber", "device_type"],
            SPLIT + "/behaviors.parquet",
        )
        profile = behaviors.groupby("user_id", sort=False).agg(
            gender=("gender", "first"), age=("age", "first"),
            postcode=("postcode", "first"), is_subscriber=("is_subscriber", "first"),
        )
        # Anonymous traffic has neither age nor gender, so there is no person to be.
        known = profile[profile["gender"].notna() | profile["age"].notna()]
        chosen = (
            behaviors[behaviors["user_id"].isin(known.index)]
            .sort_values(["impression_time", "impression_id"])
            .groupby("user_id", sort=False)
            .head(1)
        )
        cards = articles.set_index("article_id")[
            ["title", "subtitle", "category_str", "premium", "article_type", "published_time"]
        ]
        known_users = set(known.index)
        reading = self._reading(history[history["user_id"].isin(known_users)], cards)
        # The week before the exam logs every article shown, not only the ones
        # opened, so it is the one place a seen-but-not-clicked exists.
        earlier = self._parquet(raw, "train/behaviors.parquet")
        self.check_columns(
            earlier, ["user_id", "impression_time", "article_ids_inview", "article_ids_clicked"],
            "train/behaviors.parquet",
        )
        earlier = earlier[earlier["user_id"].isin(known_users)]
        passed = self._passed_over(earlier, cards)
        habit = self._click_habit(earlier)
        rows = []
        for impression in chosen.itertuples(index=False):
            user = int(impression.user_id)
            clicked = {int(a) for a in impression.article_ids_clicked}
            inview = [int(a) for a in impression.article_ids_inview]
            shown = [(i, a) for i, a in enumerate(inview, start=1) if a in cards.index]
            if len(shown) < 2 or not clicked.issubset({a for _, a in shown}):
                continue
            person = known.loc[user]
            page = _page(impression.article_id, cards)
            when = impression.impression_time
            for position, article_id in shown:
                card = cards.loc[article_id]
                rows.append({
                    "row_id": "{}-{}".format(int(impression.impression_id), article_id),
                    "person_id": str(user),
                    "impression_id": int(impression.impression_id),
                    "position": position,
                    "article_id": article_id,
                    "title": card.title,
                    "subtitle": card.subtitle,
                    "category_str": card.category_str,
                    "premium": bool(card.premium),
                    "article_kind": ARTICLE_KIND.get(str(card.article_type), ""),
                    "published_time": card.published_time,
                    "page": page,
                    "when": when,
                    "gender": GENDER.get(as_int(person["gender"])),
                    "age": as_int(person["age"]),
                    "postcode": POSTCODE.get(as_int(person["postcode"])),
                    "is_subscriber": bool(person["is_subscriber"]),
                    "device": DEVICE.get(as_int(impression.device_type), ""),
                    "recent_reading": reading.get(user, ""),
                    "passed_over": passed.get(user, ""),
                    "click_habit": habit.get(user, ""),
                    "outcome": "yes" if article_id in clicked else "no",
                })
        return pd.DataFrame(rows)

    def persona(self, person_rows: pd.DataFrame, history: pd.DataFrame | None = None) -> PersonaSpec:
        r = person_rows.iloc[0]
        age = as_int(r.get("age"))
        overlays = {
            GENDER_OVERLAY.id: None if is_missing(r.get("gender")) else str(r.get("gender")),
            POSTCODE_OVERLAY.id: None if is_missing(r.get("postcode")) else str(r.get("postcode")),
            SUBSCRIBER_OVERLAY.id: "abonnent" if bool(r.get("is_subscriber")) else "ikke abonnent",
        }
        device = r.get("device")
        where = device if not is_missing(device) else "din telefon eller computer"
        facts = ["Det er maj 2023. Du bor i Danmark og læser Ekstra Bladet, en dansk avis, på {}.".format(where)]
        if age is not None:
            facts.append("Aldersgruppe på kontoen: {}-{} år.".format(age, age + 9))
        reading = r.get("recent_reading")
        if not is_missing(reading):
            facts.append(
                "Artikler du åbnede i de tre uger før denne skærm, ældste først: {}.".format(reading)
            )
        passed = r.get("passed_over")
        if not is_missing(passed):
            facts.append("Artikler du fik vist uden at åbne dem, i ugen lige før: {}.".format(passed))
        habit = r.get("click_habit")
        if not is_missing(habit):
            facts.append(str(habit))
        return PersonaSpec(
            display_name="en læser af Ekstra Bladet",
            dimensions={},
            overlays=overlays,
            facts=facts,
        )

    def _article_question(self, row: pd.Series, number: int) -> dict:
        return choice_question(
            "Artikel {}, sektion {}: {} — {}.{} Ville du åbne den?".format(
                number, row["category_str"], row["title"], row["subtitle"], _article_note(row)
            ),
            YES_NO,
            "q{:03d}".format(number),
        )

    def card(self, row: pd.Series) -> Card:
        return Card(_screen(row), [self._article_question(row, 1)])

    def form(self, rows: list[pd.Series]) -> Card:
        # The caller zips these questions back onto the same rows, so the caller's
        # list has to come out in this order too.
        rows.sort(key=lambda row: int(row["position"]))
        return Card(_screen(rows[0]), [self._article_question(row, i) for i, row in enumerate(rows, start=1)])

    def example_rows(self) -> pd.DataFrame:
        rows = [
            {"user_id": 7, "impression_id": 1, "position": 1, "article_id": 101,
             "title": "Danmark vinder", "subtitle": "Sen aften i Parken", "category_str": "sport",
             "premium": False, "article_kind": "", "published_time": "2023-05-25 18:00:00",
             "page": "forsiden", "when": "2023-05-25 21:00:00",
             "gender": "kvinde", "age": 40, "postcode": "hovedstadsområdet", "is_subscriber": True,
             "device": "en telefon",
             "recent_reading": "sport: Danmark vinder — Sen aften i Parken (læst 24 sek, rullet 72%)",
             "passed_over": "krimi: Gammel sag — Ingen nye spor",
             "click_habit": "I ugen lige før åbnede du 3 af de 40 artikler, du fik vist (7,5 %), på 4 skærme. På hver af skærmene åbnede du én artikel.",
             "clicked": True},
            {"user_id": 7, "impression_id": 1, "position": 2, "article_id": 102,
             "title": "Ny sag i retten", "subtitle": "Tiltalte nægter", "category_str": "krimi",
             "premium": True, "article_kind": "en video", "published_time": "2023-05-10 09:00:00",
             "page": "forsiden", "when": "2023-05-25 21:00:00",
             "gender": "kvinde", "age": 40, "postcode": "hovedstadsområdet", "is_subscriber": True,
             "device": "en telefon",
             "recent_reading": "sport: Danmark vinder — Sen aften i Parken (læst 24 sek, rullet 72%)",
             "passed_over": "krimi: Gammel sag — Ingen nye spor",
             "click_habit": "I ugen lige før åbnede du 3 af de 40 artikler, du fik vist (7,5 %), på 4 skærme. På hver af skærmene åbnede du én artikel.",
             "clicked": False},
        ]
        df = pd.DataFrame(rows)
        df["row_id"] = df["impression_id"].astype(str) + "-" + df["article_id"].astype(str)
        df["person_id"] = df["user_id"].astype(str)
        df["cluster_id"] = df["person_id"]
        df["outcome"] = df["clicked"].map({True: "yes", False: "no"})
        return df

    def _parquet(self, raw: Path, name: str) -> pd.DataFrame:
        path = raw / name
        if not path.is_file():
            raise FileNotFoundError(
                "{}: expected {} (download ebnerd_small from recsys.eb.dk and unzip it here)".format(self.slug, path)
            )
        return pd.read_parquet(path)

    @staticmethod
    def _reading(history: pd.DataFrame, cards: pd.DataFrame) -> dict[int, str]:
        out: dict[int, str] = {}
        for row in history.itertuples(index=False):
            order = sorted(
                range(len(row.article_id_fixed)),
                key=lambda i: (row.impression_time_fixed[i], int(row.article_id_fixed[i])),
            )
            lines = []
            for i in order:
                lines.append(_article_line(
                    int(row.article_id_fixed[i]), cards,
                    _engagement(row.read_time_fixed[i], row.scroll_percentage_fixed[i]),
                ))
            out[int(row.user_id)] = "; ".join(line for line in lines if line)
        return out

    @staticmethod
    def _passed_over(behaviors: pd.DataFrame, cards: pd.DataFrame) -> dict[int, str]:
        """Articles shown but not opened, in the week before the exam.

        The released history lists only what was opened. This file lists everything
        that was on screen, so the ones left unopened are the negatives the reader
        actually had. The exam week itself is not in here.
        """
        out: dict[int, str] = {}
        for user, group in behaviors.groupby("user_id", sort=False):
            opened = {int(a) for clicked in group["article_ids_clicked"] for a in clicked}
            seen: list[int] = []
            for inview in group.sort_values("impression_time")["article_ids_inview"]:
                for article_id in inview:
                    article_id = int(article_id)
                    if article_id not in opened and article_id not in seen:
                        seen.append(article_id)
            lines = [_article_line(article_id, cards, "") for article_id in seen]
            out[int(user)] = "; ".join(line for line in lines if line)
        return out

    @staticmethod
    def _click_habit(behaviors: pd.DataFrame) -> dict[int, str]:
        """How often this reader opened an article in the week before the exam.

        The released file keeps a screen only when something on it was opened,
        so a screen with no click is absent and the rate is not filled in.
        The exam week is not in this file.
        """
        out: dict[int, str] = {}
        for user, group in behaviors.groupby("user_id", sort=False):
            shown = int(sum(len(articles) for articles in group["article_ids_inview"]))
            opened = int(sum(len(articles) for articles in group["article_ids_clicked"]))
            if shown == 0:
                continue
            per_screen = group["article_ids_clicked"].map(len)
            screens = int(len(group))
            one = int((per_screen == 1).sum())
            more = screens - one
            rate = "{:.1f}".format(100 * opened / shown).replace(".", ",")
            text = (
                "I ugen lige før åbnede du {} af de {} artikler, du fik vist ({} %), på {} skærme."
                .format(opened, shown, rate, screens)
            )
            if more:
                text += " På {} af skærmene åbnede du én artikel, og på {} åbnede du mere end én.".format(one, more)
            else:
                text += " På hver af skærmene åbnede du én artikel."
            out[int(user)] = text
        return out


def _text(value: object) -> str:
    return "" if is_missing(value) else str(value)


def _article_line(article_id: int, cards: pd.DataFrame, extra: str) -> str:
    if article_id not in cards.index:
        return ""
    article = cards.loc[article_id]
    return "{}: {} — {}{}".format(
        _text(article.category_str), _text(article.title), _text(article.subtitle), extra
    )


def _page(article_id: object, cards: pd.DataFrame) -> str:
    """Where the screen sat. An empty article id is the front page; otherwise the
    reader was at the bottom of that article, looking at what came next."""
    if is_missing(article_id) or int(article_id) not in cards.index:
        return "forsiden"
    article = cards.loc[int(article_id)]
    return "nederst i artiklen {}: {} — {}".format(
        _text(article.category_str), _text(article.title), _text(article.subtitle)
    )


def _screen(row: pd.Series) -> str:
    page = row.get("page")
    where = page if not is_missing(page) else "forsiden"
    return "Skærmen er {}.".format(where)


def _article_note(row: pd.Series) -> str:
    """What the reader could see about the article before opening it."""
    notes = []
    if bool(row.get("premium")):
        notes.append("kræver abonnement" if bool(row.get("is_subscriber")) else "kræver abonnement, som du ikke har")
    kind = row.get("article_kind")
    if not is_missing(kind):
        notes.append(str(kind))
    published = pd.to_datetime(row.get("published_time"), errors="coerce")
    seen = pd.to_datetime(row.get("when"), errors="coerce")
    if not (pd.isna(published) or pd.isna(seen)):
        days = int((seen - published).total_seconds() // 86400)
        if days >= 7:
            notes.append("udgivet {} dage tidligere".format(days))
    return " ({})".format(", ".join(notes)) if notes else " "


def _engagement(seconds: object, scroll: object) -> str:
    """How long the opened article was read, and how far down it was scrolled.

    Both come from the history, which ends before the screen being scored.
    Read time is seconds. Scroll is absent for about one opened article in ten,
    and a missing one is left out rather than filled in.
    """
    parts = []
    if not is_missing(seconds):
        parts.append("læst {} sek".format(int(round(float(seconds)))))
    if not is_missing(scroll):
        parts.append("rullet {}%".format(int(round(float(scroll)))))
    return " ({})".format(", ".join(parts)) if parts else ""
