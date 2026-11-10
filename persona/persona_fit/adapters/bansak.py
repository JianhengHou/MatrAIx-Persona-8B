"""35 Bansak, Hainmueller & Hangartner 2016 European asylum conjoint (doi:10.7910/DVN/KL0FDF).

Persona: respondent country, gender, age, education, income decile,
ideology, employment. Card: the five side-by-side pairs that one respondent
actually saw, as one questionnaire, in that country's survey language.
Outcome: which profile in each pair the respondent preferred. The 1-7 rating
of each profile is recorded but not scored, and the 1-99 likelihood was never
asked of the real people, so it is not asked here. Stated preference (SP).
``NAsySeek*`` / ``Cat*`` respondent columns are computed from the choices and
never enter the persona.

The released files have integer levels and an English codebook, not the
translated instruments. The per-country wording is our rendering of that
codebook. Switzerland has no recorded language and stays in English.
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
    read_delimited,
)
from ._pairs import pair_options, pair_table, to_pairs
from .bansak_text import SURFACES, SURVEY_LANGUAGE, surface

ATTRS = ("cconsist", "cgender", "corigin", "cage", "cjob", "cvulner", "creason", "creligion", "clang")
COUNTRIES = (*sorted(SURVEY_LANGUAGE), "Switzerland")
EASTERN = {"Czech Republic", "Poland", "Hungary"}
# English labels stay the overlay's declared value set. Other languages index the same codes.
EISCED = dict(enumerate(SURFACES["en"]["persona"]["education_levels"], start=1))
EMPLOYMENT = SURFACES["en"]["persona"]["employment_levels"]
SLUG = "bansak-asylum"
# Party names as printed in respondent_variable_codebook.pdf (doi:10.7910/DVN/KL0FDF).
# The file stores a within-country integer. The respondent chose the party, not the integer.
PARTIES = {
    "United Kingdom": {
        1: "Conservative Party", 2: "Labour Party", 3: "United Kingdom Independence Party",
        4: "The British National Party", 5: "Scottish National Party", 6: "Plaid Cymru - Party of Wales",
        7: "Liberal Democrats Party", 8: "Green Party", 9: "Sinn Féin", 10: "Democratic Unionist Party",
        11: "Ulster Unionist Party / Conservative & Ulster Unionist Alliance",
        12: "Social Democratic & Labour Party", 13: "Other", 14: "No Party",
    },
    "Germany": {
        1: "Christlich Demokratische Union (CDU) / Christlich Soziale Union (CSU)",
        2: "Sozialdemokratische Partei Deutschlands (SPD)", 3: "Bündnis 90 / Die Grünen (Grüne)",
        4: "Die Linke (Linke)", 5: "Freie Demokratische Partei Deutschlands (FDP)",
        6: "Piratenpartei Deutschland (Piraten)", 7: "Alternative für Deutschland (AfD)",
        8: "Familien-Partei Deutschland", 9: "Freie Wähler (FW)",
        10: "Nationaldemokratische Partei Deutschlands (NPD)", 11: "Ökologisch-Demokratische Partei (ÖDP)",
        12: "Partei Bibeltreuer Christen (PBC)", 13: "Die Republikaner (REP)",
        14: "Partei Mensch Umwelt Tierschutz (Tierschutzpartei)", 15: "Sonstige",
        16: "Nein, Sie stehen keiner Partei nahe",
    },
    "Austria": {
        1: "Sozialdemokratische Partei Österreichs (SPÖ)", 2: "Österreichische Volkspartei (ÖVP)",
        3: "Freiheitliche Partei Österreichs (FPÖ)", 4: "Bündnis Zukunft Österreich (BZÖ)",
        5: "Die Grünen – Die grüne Alternative", 6: "Kommunistische Partei Österreichs (KPÖ)",
        7: "Piratenpartei", 8: "Der Wandel", 9: "NEOS - Das neue Österreich",
        10: "Die Reformkonservativen – REKOS", 11: "Sonstige", 12: "Nein, Sie stehen keiner Partei nahe",
    },
    "Switzerland": {
        1: "Union démocratique du centre (UDC)", 2: "Parti socialiste (PS)",
        3: "PLR. Les Libéraux-Radicaux", 4: "Parti démocrate-chrétien (PDC)", 5: "Les Verts (PES)",
        6: "Parti vert liberal (PEL // PVL)", 7: "Parti bourgeois démocrate (PBD)",
        8: "Parti évangélique populaire (PEV)", 9: "Union démocratique fédérale (UDF)",
        10: "Lega dei Ticinesi", 11: "Parti du travail (PdT) / Parti ouvrier populaire (POP)",
        12: "Mouvement des Citoyens Romands", 13: "Sonstige / Autre",
        14: "Nein, Sie stehen keiner Partei nahe / Non, vous ne vous sentez pas proche d’un parti politique",
    },
    "France": {
        1: "Union des Démocrates et Indépendants, Mouvement Démocrate (UDI / MoDem)",
        2: "Nouveau Parti anticapitaliste (NPA)",
        3: "Front de Gauche (FdG) (Parti communiste ou Parti de Gauche)", 4: "Parti Socialiste (PS)",
        5: "Parti radical de gauche", 6: "Europe Ecologie - Les Verts (EELV)", 7: "Lutte ouvrière (LO)",
        8: "Union pour un Mouvement Populaire (UMP)", 9: "Front national (FN)",
        10: "Debout la République (DLR)", 11: "Union pour les Outre-Mer",
        12: "Alliance des régionalistes, écologistes et progressistes des Outre-Mer régions et peuples solidaires",
        13: "Nouvelle Donne", 14: "Autre", 15: "Non, vous ne vous sentez pas proche d’un parti politique",
    },
    "Italy": {
        1: "Italia dei Valori - Di Pietro", 2: "Lega Nord", 3: "Partito Democratico", 4: "Forza Italia",
        5: "Nuovo Centrodestra", 6: "Unione dei Democratici Cristiani e Democratici di Centro (UDC)",
        7: "Popolari per l'Italia", 8: "Fratelli d'Italia - Alleanza Nazionale", 9: "Scelta Civica",
        10: "Centro Democratico", 11: "Movimento Cinque Stelle",
        12: "Südtiroler Volkspartei (Partito popolare sudtirolese)", 13: "Sinistra Ecologia e Liberta",
        14: "Altro", 15: "No, non mi sento vicino a nessun partito politico in particolare",
    },
    "Spain": {
        1: "PSOE - Partido Socialista Obrero Español / Partit dels Socialistes de Catalunya",
        2: "PP - Partido Popular", 3: "IU - Izquierda Unida", 4: "ICV - Iniciativa per Catalunya Verds",
        5: "ANOVA - Irmandade Nacionalista", 6: "UPyD - Unión Progreso y Democracia",
        7: "CDC - Convergència Democràtica de Catalunya", 8: "EAJ-PNV - Partido Nacionalista Vasco",
        9: "Unió - Unió Democràtica de Catalunya", 10: "CC - Coalición Canaria",
        11: "CxG - Compromiso por Galicia", 12: "ERC - Esquerra Republicana de Catalunya",
        13: "NECat - Nova Esquerra Catalana", 14: "BNG - Bloque Nacionalista Galego",
        15: "EH Bildu - Euskal Herria Bildu", 16: "Equo", 17: "Ciudadanos - Partido de la Ciutadanía",
        18: "VOX", 19: "Podemos", 20: "Otro", 21: "No, no se considera próximo/a a ningún partido",
    },
    "Denmark": {
        1: "A. Socialdemokratiet", 2: "B. Det Radikale Venstre", 3: "C. Det Konservative Folkeparti",
        4: "F. Socialistisk Folkeparti (SF)", 5: "O. Dansk Folkeparti", 6: "I. Liberal Alliance",
        7: "V. Venstre, Danmarks liberale parti", 8: "K. Kristendemokraterne",
        9: "Ø. Enhedslisten - de rød-grønne", 10: "Andet",
        11: "Nej, du føler ikke, at dine holdninger ligger tæt op ad et af de politiske partier?",
    },
    "Sweden": {
        1: "Vänsterpartiet", 2: "Socialdemokraterna", 3: "Centerpartiet", 4: "Folkpartiet liberalerna",
        5: "Moderata Samlingspartiet", 6: "Kristdemokraterna", 7: "Miljöpartiet de gröna",
        8: "Sverigedemokraterna", 9: "Feministiskt initiativ", 10: "Piratpartiet", 11: "Annat",
        12: "Nej, du anser dig inte stå nära något politiskt parti",
    },
    "Greece": {
        1: "Νέα Δημοκρατία", 2: "Πανελλήνιο Σοσιαλιστικό Κίνημα", 3: "Κομμουνιστικό Κόμμα Ελλάδας",
        4: "Συνασπισμός Ριζοσπαστικής Αριστεράς", 5: "Λαϊκός Ορθόδοξος Συναγερμός -Γ. Καρατζαφέρης",
        6: "Οικολόγοι Πράσινοι", 7: "Χρυσή Αυγή", 8: "Ανεξάρτητοι Έλληνες", 9: "Δημοκρατική Αριστερά",
        10: "Το Ποτάμι", 11: "Άλλο", 12: "Όχι, δεν συµµερίζεστε τις απόψεις κανενός πολιτικού κόµµατος",
    },
    "Netherlands": {
        1: "Christen Democratisch Appèl", 2: "Partij van de Arbeid", 3: "Socialistische Partij",
        4: "Volkspartij voor Vrijheid en Democratie", 5: "GroenLinks", 6: "Partij voor de Vrijheid",
        7: "ChristenUnie - Staatkundig Gereformeerde Partij", 8: "Democraten 66",
        9: "Partij voor de Dieren", 10: "50Plus", 11: "Anders",
        12: "Nee, u voelt zich niet verbonden met één bepaalde politieke partij",
    },
    "Czech Republic": {
        1: "Občanská demokratická strana", 2: "Česká strana sociálně demokratická",
        3: "Komunistická strana Čech a Moravy (KSČM)",
        4: "Křesťanská a demokratická unie – Československá strana lidová", 5: "Věci veřejné",
        6: "TOP 09", 7: "ANO 2011", 8: "Strana zelených", 9: "Úsvit přímé demokracie",
        10: "Česká pirátská strana", 11: "Strana svobodných občanů",
        12: "Národní socialisté – levice 21. století", 13: "STAN (Starostové a nezávislí)",
        14: "Hlavu vzhůru - volební blok", 15: "Strana práv občanů", 16: "Dělnická strana",
        17: "Republika", 18: "Romská demokratická strana", 19: "SNK Evropští demokraté",
        20: "Strana zdravého rozumu - nechceme euro - za Evropu svobodných států",
        21: "Úsvit přímé demokracie Tomia Okamury", 22: "VIZE 2014",
        23: "Volte Pravý Blok - www.cibulka.net", 24: "Jiné",
        25: "Ne, žádná politická strana vám nepřijde blízká",
    },
    "Hungary": {
        1: "Együtt 2014 - Párbeszéd Magyarországért", 2: "Magyar Szocialista Párt",
        3: "Demokratikus Koalíció", 4: "Fidesz - Magyar Polgári Szövetség - Keresztény Demokrata Néppárt",
        5: "Jobbik Magyarországért Mozgalom", 6: "Lehet Más a Politika", 7: "Egyéb",
        8: "Nem, nem érzi magát közelinek egy politikai párthoz sem",
    },
    "Norway": {
        1: "Rødt", 2: "Sosialistisk Venstreparti", 3: "Det Norske Arbeiderparti", 4: "Venstre",
        5: "Kristelig Folkeparti", 6: "Senterpartiet", 7: "Høyre", 8: "Fremskrittspartiet",
        9: "Kystpartiet", 10: "Miljøpartiet De Grønne", 11: "Andre partier/lister", 12: "NEI",
    },
    "Poland": {
        1: "Prawo i Sprawiedliwość", 2: "Nowoczesna", 3: "Platforma Obywatelska", 4: "Kukiz’15",
        5: "Polskie Stronnictwo Ludowe", 6: "Sojusz Lewicy Demokratycznej", 7: "Partia Razem",
        8: "Polska Razem", 9: "Solidarna Polska", 10: "Kongres Nowej Prawicy",
        11: "Koalicja Odnowy Rzeczypospolitej Wolność i Nadzieja", 12: "Unia Pracy", 13: "Inne",
        14: "Nie, żadna partia polityczna nie jest Panu(i) bliska",
    },
}
COUNTRY_OVERLAY = OverlayDim(overlay_id(SLUG, "country"), "Country you live in", COUNTRIES)
EDUCATION_OVERLAY = coded_overlay(SLUG, "education", "Highest education (European ISCED)", EISCED)
EMPLOYMENT_OVERLAY = OverlayDim(overlay_id(SLUG, "employment"), "Employment", EMPLOYMENT)
INCOME_OVERLAY = OverlayDim(overlay_id(SLUG, "income_decile"), "Household income decile in your country (1 = lowest)", tuple(str(i) for i in range(1, 11)))


class BansakAsylum(DatasetAdapter):
    slug = "bansak-asylum"
    sheet_id = "35"
    title = "Bansak, Hainmueller & Hangartner asylum conjoint"
    path = "application"
    decision_type = "pair"
    domain = "politics"
    stated_preference = True
    raw_files = (
        RawFile("conjoint_data_final.tab", "https://dataverse.harvard.edu/api/access/datafile/2863404", "CC0, doi:10.7910/DVN/KL0FDF"),
        RawFile("respondent_data_final.tab", "https://dataverse.harvard.edu/api/access/datafile/2863405", "CC0, doi:10.7910/DVN/KL0FDF"),
    )
    persona_fields = (
        "cty", "Female", "Age", "EISCED", "IncomeDecile", "IdeoScale", "EmpStatus",
        "HomeBorn", "AsylumHome", "PartyID", "Empathy1", "Empathy2",
    )
    card_fields = tuple("{}_{}".format(a, s) for a in ATTRS for s in ("a", "b"))
    leakage_fields = ("pref", "rate", "ratebin", "ratescaled", "NAsySeekRejected", "NAsySeekAccepted", "CatRejecter", "CatAccepter")
    overlay_dimensions = (COUNTRY_OVERLAY, EDUCATION_OVERLAY, EMPLOYMENT_OVERLAY, INCOME_OVERLAY)
    options = pair_options("Applicant")
    positive_option = "a"
    metric_key = "chose_first"
    # People, not pairs. Each person answers all five pairs in one job.
    # A fifth of the 18,030 voters: about 240 per country.
    default_sample_rows = 3606
    # English is the checked-in example (Germany overrides it per person).
    instruction_md = SURFACES["en"]["instruction"]

    def load(self, raw: Path) -> pd.DataFrame:
        conj = read_delimited(self.require_file(raw, "conjoint_data_final.tab"))
        resp = read_delimited(self.require_file(raw, "respondent_data_final.tab"))
        self.check_columns(conj, ["respid", "mix", "pref", *ATTRS], "conjoint_data_final.tab")
        self.check_columns(resp, ["respid", *self.persona_fields], "respondent_data_final.tab")
        conj["pair_no"] = conj["mix"].map(lambda m: (ord(str(m)) - ord("A")) // 2 + 1)
        conj = conj.drop(columns=["cty", "weight", "id"], errors="ignore")
        pairs = to_pairs(conj, ["respid", "pair_no"], "mix", list(ATTRS), "pref")
        resp = resp.drop(columns=[c for c in self.leakage_fields if c in resp.columns])
        pairs = pairs.merge(resp, on="respid", how="left")
        pairs["row_id"] = pairs["respid"].astype(str) + "-" + pairs["pair_no"].astype(str)
        pairs["person_id"] = pairs["respid"].astype(str)
        return pairs

    def persona(self, person_rows: pd.DataFrame, history: pd.DataFrame | None = None) -> PersonaSpec:
        r = person_rows.iloc[0]
        country = str(r.get("cty"))
        text = surface(country)["persona"]
        ideo = as_int(r.get("IdeoScale"))
        income = as_int(r.get("IncomeDecile"))
        # Schema values stay the English catalog entries. The persona text below is the
        # language the respondent saw; these two cannot be recoded without losing the schema.
        dims = {
            "region": "Eastern Europe" if country in EASTERN else "Western Europe",
            "gender_identity": {1: "Woman", 0: "Man"}.get(as_int(r.get("Female"))),
        }
        education = as_int(r.get("EISCED"))
        employment = None if is_missing(r.get("EmpStatus")) else str(r.get("EmpStatus")).split(". ", 1)[-1]
        overlays = {
            COUNTRY_OVERLAY.id: country,
            EDUCATION_OVERLAY.id: EISCED.get(education),
            EMPLOYMENT_OVERLAY.id: employment,
            INCOME_OVERLAY.id: str(income) if income is not None else None,
        }
        facts = [
            "{}: {}".format(text["country"], country),
            text["setting"].format(country),
        ]
        if education in EISCED:
            facts.append("{}: {}".format(text["education"], text["education_levels"][education - 1]))
        if employment in EMPLOYMENT:
            facts.append("{}: {}".format(text["employment"], text["employment_levels"][EMPLOYMENT.index(employment)]))
        if income is not None:
            facts.append("{}: {}".format(text["income"], income))
        if as_int(r.get("Age")) is not None:
            facts.append(text["age"].format(as_int(r.get("Age"))))
        if ideo is not None and ideo >= 0:
            facts.append(text["ideology"].format(ideo))
        born = as_int(r.get("HomeBorn"))
        if born is not None:
            facts.append((text["born"] if born == 1 else text["not_born"]).format(country))
        asylum = as_int(r.get("AsylumHome"))
        if asylum is not None:
            facts.append(text["asylum"].format(asylum))
        party = PARTIES.get(country, {}).get(as_int(r.get("PartyID")))
        if party:
            facts.append(text["party"].format(party))
        for number, item in enumerate(("Empathy1", "Empathy2"), start=1):
            value = as_int(r.get(item))
            if value is not None:
                facts.append(text["empathy"].format(number, value))
        return PersonaSpec(display_name=text["who"], dimensions=dims, overlays=overlays, facts=facts)

    def _text(self, row: pd.Series) -> dict:
        return surface(str(row.get("cty")))

    def _attributes(self, row: pd.Series) -> list[tuple[str, str, str]]:
        text = self._text(row)
        attributes = []
        for attr in ("cgender", "cage", "corigin", "creligion", "cjob", "clang", "creason", "cvulner", "cconsist"):
            mapping = text["values"][attr]
            attributes.append((
                text["labels"][attr],
                mapping.get(as_int(row[attr + "_a"]), "?"),
                mapping.get(as_int(row[attr + "_b"]), "?"),
            ))
        return attributes

    def _pair_block(self, row: pd.Series, number: int) -> str:
        text = self._text(row)
        return "## {} {}\n\n{}".format(text["pair"], number, pair_table(text["applicant"], self._attributes(row)))

    def _pair_question(self, row: pd.Series, number: int) -> dict:
        text = self._text(row)
        return choice_question(
            text["question"].format(number),
            pair_options(text["applicant"]),
            "q{:03d}".format(number),
        )

    def card(self, row: pd.Series) -> Card:
        text = self._text(row)
        return Card(
            "# {}\n\n{}\n".format(text["pair"], self._pair_block(row, 1)),
            [self._pair_question(row, 1)],
            instruction_md=text["instruction"],
        )

    def form(self, rows: list[pd.Series]) -> Card:
        ordered = sorted(rows, key=lambda row: int(row["pair_no"]))
        # The caller zips these questions onto the same rows. Both must share this order.
        rows.sort(key=lambda row: int(row["pair_no"]))
        text = self._text(ordered[0])
        return Card(
            "# {}\n\n{}\n\n".format(text["pair"], text["intro"])
            + "\n\n".join(self._pair_block(row, i) for i, row in enumerate(ordered, start=1))
            + "\n",
            [self._pair_question(row, i) for i, row in enumerate(ordered, start=1)],
            instruction_md=text["instruction"],
        )

    def example_rows(self) -> pd.DataFrame:
        row = {
            "respid": "R_example", "pair_no": 1, "cty": "Germany", "Female": 1, "Age": 41, "EISCED": 6,
            "IncomeDecile": 5, "IdeoScale": 4, "EmpStatus": "1. Paid employee", "weight": 1.0,
            "HomeBorn": 1, "AsylumHome": 0, "PartyID": 3, "Empathy1": 2, "Empathy2": -1,
            "rate": 5, "NAsySeekAccepted": 4, "CatAccepter": 0,
            **{a + "_a": 1 for a in ATTRS}, **{a + "_b": 2 for a in ATTRS},
        }
        df = pd.DataFrame([row, {**row, "pair_no": 2, "cage_a": 3}])
        df["row_id"] = df["respid"] + "-" + df["pair_no"].astype(str)
        df["person_id"] = df["respid"]
        df["cluster_id"] = df["person_id"]
        df["outcome"] = ["a", "b"]
        return df
