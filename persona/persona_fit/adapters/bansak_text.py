"""Bansak instrument in the language of each survey country.

The published files store attribute levels as integers and an English codebook.
The translated questionnaires were not released, so this is our rendering of
that codebook, not the field instrument. Switzerland has no recorded language
and stays on the English text.
"""

from __future__ import annotations

# Survey language, not the language named in the language-skills cell.
SURVEY_LANGUAGE = {
    "Austria": "de", "Germany": "de", "Sweden": "sv", "France": "fr", "Spain": "es",
    "Norway": "no", "Czech Republic": "cs", "Denmark": "da", "Poland": "pl",
    "United Kingdom": "en", "Netherlands": "nl", "Greece": "el", "Hungary": "hu", "Italy": "it",
}

_EN_INSTRUCTION = (
    "# Asylum application choice\n\n"
    "It is early 2016, during the European asylum crisis.\n\n"
    "You will see five pairs. Each pair is two people who have applied for asylum in your "
    "country, shown side by side, the way they were shown to you.\n\n"
    "For each pair, if you had to choose, which of the two applicants should be given asylum?\n\n"
    "## How to answer\n\n"
    "- Answer every pair.\n"
    "- Use the listed option ids.\n"
)

# One surface per language. Attribute codes match the codebook. Choice ids stay a/b.
SURFACES = {
    "en": {
        "pair": "Pair",
        "applicant": "Applicant",
        "question": "Pair {}: which of these two applicants should be given asylum?",
        "intro": (
            "Five pairs of people who have applied for asylum in your country. "
            "For each pair, choose which applicant is given asylum."
        ),
        "instruction": _EN_INSTRUCTION,
        "persona": {
            "who": "an eligible voter",
            "country": "Country you live in",
            "education": "Highest education",
            "employment": "Employment",
            "income": "Household income decile in your country, 1 lowest to 10 highest",
            "education_levels": (
                "Less than lower secondary", "Lower secondary", "Lower tier upper secondary",
                "Upper tier upper secondary", "Advanced vocational / sub-degree",
                "Lower tertiary (bachelor's level)", "Higher tertiary (master's level or above)",
            ),
            "employment_levels": (
                "Paid employee", "Self-employed", "Student", "Unemployed, searching",
                "Unemployed, not searching", "Chronic illness or permanent disability",
                "Retired", "Working at home",
            ),
            "setting": "It is early 2016. You are an eligible voter living in {}.",
            "age": "Age: {}",
            "ideology": "Self-placement on the left-right scale, 0 left to 10 right: {}",
            "born": "You were born in {}.",
            "not_born": "You were not born in {}.",
            "asylum": "The number of asylum seekers your country should accept, -2 far fewer to 2 far more: {}.",
            "party": "The party you feel closest to: {}.",
            "empathy": "Empathy item {}, from -6 to 6: {}.",
        },
        "labels": {
            "cgender": "Gender", "cage": "Age", "corigin": "Country of origin", "creligion": "Religion",
            "cjob": "Previous occupation", "clang": "Language skills", "creason": "Reason for migrating",
            "cvulner": "Special vulnerability", "cconsist": "Consistency of asylum testimony",
        },
        "values": {
            "cgender": {1: "Female", 2: "Male"},
            "cage": {1: "21 years", 2: "38 years", 3: "62 years"},
            "corigin": {1: "Syria", 2: "Afghanistan", 3: "Kosovo", 4: "Eritrea", 5: "Pakistan", 6: "Ukraine", 7: "Iraq"},
            "creligion": {1: "Christian", 2: "Agnostic", 3: "Muslim"},
            "cjob": {1: "Unemployed", 2: "Cleaner", 3: "Farmer", 4: "Accountant", 5: "Teacher", 6: "Doctor"},
            "clang": {1: "Speaks fluent English", 2: "Speaks broken English", 3: "Speaks no English"},
            "creason": {
                1: "Persecution for political views", 2: "Persecution for religious beliefs",
                3: "Persecution for ethnicity", 4: "Seeking better economic opportunities",
            },
            "cvulner": {
                1: "None", 2: "Post-traumatic stress disorder (PTSD)", 3: "Victim of torture",
                4: "No surviving family members", 5: "Physically handicapped",
            },
            "cconsist": {1: "No inconsistencies", 2: "Minor inconsistencies", 3: "Major inconsistencies"},
        },
    },
    "de": {
        "pair": "Paar",
        "applicant": "Antragsteller",
        "question": "Paar {}: Welchem der beiden Antragsteller soll Asyl gewährt werden?",
        "intro": (
            "Fünf Paare von Personen, die in Ihrem Land Asyl beantragt haben. "
            "Wählen Sie für jedes Paar, welchem Antragsteller Asyl gewährt wird."
        ),
        "persona": {
            "who": "eine wahlberechtigte Person",
            "country": "Land, in dem Sie leben",
            "education": "Höchster Bildungsabschluss",
            "employment": "Erwerbsstatus",
            "income": "Dezil des Haushaltseinkommens in Ihrem Land, 1 am niedrigsten bis 10 am höchsten",
            "education_levels": (
                "Weniger als Sekundarstufe I", "Sekundarstufe I", "Sekundarstufe II, untere Stufe",
                "Sekundarstufe II, obere Stufe", "Höhere Berufsbildung",
                "Tertiärbereich, Bachelor", "Tertiärbereich, Master oder höher",
            ),
            "employment_levels": (
                "Angestellt", "Selbstständig", "In Ausbildung", "Arbeitslos, auf Stellensuche",
                "Arbeitslos, nicht auf Stellensuche", "Chronische Krankheit oder dauerhafte Behinderung",
                "Im Ruhestand", "Hausarbeit",
            ),
            "setting": "Es ist Anfang 2016. Sie sind wahlberechtigt und leben in {}.",
            "age": "Alter: {}",
            "ideology": "Selbsteinstufung auf der Links-rechts-Skala, 0 links bis 10 rechts: {}",
            "born": "Sie sind in {} geboren.",
            "not_born": "Sie sind nicht in {} geboren.",
            "asylum": "Wie viele Asylsuchende Ihr Land aufnehmen sollte, -2 viel weniger bis 2 viel mehr: {}.",
            "party": "Die Partei, der Sie sich am nächsten fühlen: {}.",
            "empathy": "Empathiefrage {}, von -6 bis 6: {}.",
        },
        "instruction": (
            "# Entscheidung über einen Asylantrag\n\n"
            "Es ist Anfang 2016, während der europäischen Asylkrise.\n\n"
            "Sie sehen fünf Paare. Jedes Paar zeigt zwei Personen, die in Ihrem Land Asyl "
            "beantragt haben, nebeneinander, so wie sie Ihnen vorgelegt wurden.\n\n"
            "Wenn Sie sich für jedes Paar entscheiden müssten: Welchem der beiden Antragsteller "
            "soll Asyl gewährt werden?\n\n"
            "## So antworten Sie\n\n"
            "- Beantworten Sie jedes Paar.\n"
            "- Verwenden Sie die angegebenen Optionsnummern.\n"
        ),
        "labels": {
            "cgender": "Geschlecht", "cage": "Alter", "corigin": "Herkunftsland", "creligion": "Religion",
            "cjob": "Früherer Beruf", "clang": "Sprachkenntnisse", "creason": "Grund für die Migration",
            "cvulner": "Besondere Schutzbedürftigkeit", "cconsist": "Widerspruchsfreiheit der Asylaussage",
        },
        "values": {
            "cgender": {1: "weiblich", 2: "männlich"},
            "cage": {1: "21 Jahre", 2: "38 Jahre", 3: "62 Jahre"},
            "corigin": {1: "Syrien", 2: "Afghanistan", 3: "Kosovo", 4: "Eritrea", 5: "Pakistan", 6: "Ukraine", 7: "Irak"},
            "creligion": {1: "christlich", 2: "agnostisch", 3: "muslimisch"},
            "cjob": {1: "arbeitslos", 2: "Reinigungskraft", 3: "Landwirt", 4: "Buchhalter", 5: "Lehrer", 6: "Arzt"},
            "clang": {1: "Spricht fließend Deutsch", 2: "Spricht gebrochen Deutsch", 3: "Spricht kein Deutsch"},
            "creason": {
                1: "Verfolgung wegen politischer Ansichten", 2: "Verfolgung wegen religiöser Überzeugungen",
                3: "Verfolgung wegen der ethnischen Zugehörigkeit", 4: "Auf der Suche nach besseren wirtschaftlichen Möglichkeiten",
            },
            "cvulner": {
                1: "keine", 2: "Posttraumatische Belastungsstörung (PTBS)", 3: "Opfer von Folter",
                4: "Keine überlebenden Familienangehörigen", 5: "körperlich behindert",
            },
            "cconsist": {1: "keine Widersprüche", 2: "geringe Widersprüche", 3: "erhebliche Widersprüche"},
        },
    },
    "da": {
        "pair": "Par",
        "applicant": "Ansøger",
        "question": "Par {}: Hvem af de to ansøgere skal have asyl?",
        "intro": (
            "Fem par af personer, der har søgt asyl i dit land. "
            "Vælg for hvert par, hvilken ansøger der skal have asyl."
        ),
        "persona": {
            "who": "en stemmeberettiget",
            "country": "Landet du bor i",
            "education": "Højeste uddannelse",
            "employment": "Beskæftigelse",
            "income": "Husstandens indkomstdecil i dit land, 1 lavest til 10 højest",
            "education_levels": (
                "Mindre end grundskolens ældste trin", "Grundskolens ældste trin", "Gymnasial uddannelse, lavere trin",
                "Gymnasial uddannelse, højere trin", "Kort videregående uddannelse",
                "Bachelor", "Kandidat eller højere",
            ),
            "employment_levels": (
                "Lønmodtager", "Selvstændig", "Under uddannelse", "Arbejdsløs, jobsøgende",
                "Arbejdsløs, ikke jobsøgende", "Kronisk sygdom eller varigt handicap",
                "Pensionist", "Hjemmearbejdende",
            ),
            "setting": "Det er begyndelsen af 2016. Du er stemmeberettiget og bor i {}.",
            "age": "Alder: {}",
            "ideology": "Egen placering på venstre-højre-skalaen, 0 venstre til 10 højre: {}",
            "born": "Du er født i {}.",
            "not_born": "Du er ikke født i {}.",
            "asylum": "Hvor mange asylansøgere dit land bør modtage, -2 langt færre til 2 langt flere: {}.",
            "party": "Det parti du føler dig tættest på: {}.",
            "empathy": "Empatispørgsmål {}, fra -6 til 6: {}.",
        },
        "instruction": (
            "# Valg om en asylansøgning\n\n"
            "Det er begyndelsen af 2016, under den europæiske asylkrise.\n\n"
            "Du ser fem par. Hvert par er to personer, der har søgt asyl i dit land, "
            "vist ved siden af hinanden, sådan som de blev vist for dig.\n\n"
            "Hvis du skulle vælge for hvert par: Hvem af de to ansøgere skal have asyl?\n\n"
            "## Sådan svarer du\n\n"
            "- Svar på hvert par.\n"
            "- Brug de angivne svarmuligheder.\n"
        ),
        "labels": {
            "cgender": "Køn", "cage": "Alder", "corigin": "Oprindelsesland", "creligion": "Religion",
            "cjob": "Tidligere erhverv", "clang": "Sprogkundskaber", "creason": "Årsag til migration",
            "cvulner": "Særlig sårbarhed", "cconsist": "Sammenhæng i asylforklaringen",
        },
        "values": {
            "cgender": {1: "kvinde", 2: "mand"},
            "cage": {1: "21 år", 2: "38 år", 3: "62 år"},
            "corigin": {1: "Syrien", 2: "Afghanistan", 3: "Kosovo", 4: "Eritrea", 5: "Pakistan", 6: "Ukraine", 7: "Irak"},
            "creligion": {1: "kristen", 2: "agnostiker", 3: "muslim"},
            "cjob": {1: "arbejdsløs", 2: "rengøringsassistent", 3: "landmand", 4: "bogholder", 5: "lærer", 6: "læge"},
            "clang": {1: "Taler flydende dansk", 2: "Taler gebrokkent dansk", 3: "Taler ikke dansk"},
            "creason": {
                1: "Forfulgt på grund af politiske holdninger", 2: "Forfulgt på grund af religiøs overbevisning",
                3: "Forfulgt på grund af etnisk tilhørsforhold", 4: "Søger bedre økonomiske muligheder",
            },
            "cvulner": {
                1: "ingen", 2: "Posttraumatisk stresslidelse (PTSD)", 3: "Offer for tortur",
                4: "Ingen overlevende familiemedlemmer", 5: "Fysisk handicappet",
            },
            "cconsist": {1: "Ingen uoverensstemmelser", 2: "Mindre uoverensstemmelser", 3: "Store uoverensstemmelser"},
        },
    },
    "sv": {
        "pair": "Par",
        "applicant": "Sökande",
        "question": "Par {}: Vem av de två sökande ska beviljas asyl?",
        "intro": (
            "Fem par av personer som har sökt asyl i ditt land. "
            "Välj för varje par vilken sökande som ska beviljas asyl."
        ),
        "persona": {
            "who": "en röstberättigad",
            "country": "Landet du bor i",
            "education": "Högsta utbildning",
            "employment": "Sysselsättning",
            "income": "Hushållets inkomstdecil i ditt land, 1 lägst till 10 högst",
            "education_levels": (
                "Mindre än grundskola", "Grundskola", "Gymnasial utbildning, lägre nivå",
                "Gymnasial utbildning, högre nivå", "Eftergymnasial yrkesutbildning",
                "Kandidatnivå", "Master eller högre",
            ),
            "employment_levels": (
                "Anställd", "Egenföretagare", "Studerande", "Arbetslös, söker arbete",
                "Arbetslös, söker inte arbete", "Kronisk sjukdom eller bestående funktionsnedsättning",
                "Pensionär", "Hemarbetande",
            ),
            "setting": "Det är början av 2016. Du är röstberättigad och bor i {}.",
            "age": "Ålder: {}",
            "ideology": "Egen placering på vänster-högerskalan, 0 vänster till 10 höger: {}",
            "born": "Du är född i {}.",
            "not_born": "Du är inte född i {}.",
            "asylum": "Hur många asylsökande ditt land bör ta emot, -2 mycket färre till 2 mycket fler: {}.",
            "party": "Det parti du känner dig närmast: {}.",
            "empathy": "Empatifråga {}, från -6 till 6: {}.",
        },
        "instruction": (
            "# Val om en asylansökan\n\n"
            "Det är början av 2016, under den europeiska asylkrisen.\n\n"
            "Du ser fem par. Varje par är två personer som har sökt asyl i ditt land, "
            "visade sida vid sida, så som de visades för dig.\n\n"
            "Om du var tvungen att välja för varje par: Vem av de två sökande ska beviljas asyl?\n\n"
            "## Så svarar du\n\n"
            "- Svara på varje par.\n"
            "- Använd de angivna svarsalternativen.\n"
        ),
        "labels": {
            "cgender": "Kön", "cage": "Ålder", "corigin": "Ursprungsland", "creligion": "Religion",
            "cjob": "Tidigare yrke", "clang": "Språkkunskaper", "creason": "Orsak till migration",
            "cvulner": "Särskild utsatthet", "cconsist": "Samstämmighet i asylberättelsen",
        },
        "values": {
            "cgender": {1: "kvinna", 2: "man"},
            "cage": {1: "21 år", 2: "38 år", 3: "62 år"},
            "corigin": {1: "Syrien", 2: "Afghanistan", 3: "Kosovo", 4: "Eritrea", 5: "Pakistan", 6: "Ukraina", 7: "Irak"},
            "creligion": {1: "kristen", 2: "agnostiker", 3: "muslim"},
            "cjob": {1: "arbetslös", 2: "städare", 3: "jordbrukare", 4: "revisor", 5: "lärare", 6: "läkare"},
            "clang": {1: "Talar flytande svenska", 2: "Talar bristfällig svenska", 3: "Talar inte svenska"},
            "creason": {
                1: "Förföljelse på grund av politiska åsikter", 2: "Förföljelse på grund av religiös övertygelse",
                3: "Förföljelse på grund av etnicitet", 4: "Söker bättre ekonomiska möjligheter",
            },
            "cvulner": {
                1: "ingen", 2: "Posttraumatiskt stressyndrom (PTSD)", 3: "Offer för tortyr",
                4: "Inga överlevande familjemedlemmar", 5: "Fysiskt funktionsnedsatt",
            },
            "cconsist": {1: "Inga motsägelser", 2: "Mindre motsägelser", 3: "Stora motsägelser"},
        },
    },
    "no": {
        "pair": "Par",
        "applicant": "Søker",
        "question": "Par {}: Hvem av de to søkerne skal få asyl?",
        "intro": (
            "Fem par av personer som har søkt asyl i landet ditt. "
            "Velg for hvert par hvilken søker som skal få asyl."
        ),
        "persona": {
            "who": "en stemmeberettiget",
            "country": "Landet du bor i",
            "education": "Høyeste utdanning",
            "employment": "Yrkesstatus",
            "income": "Husholdningens inntektsdesil i landet ditt, 1 lavest til 10 høyest",
            "education_levels": (
                "Mindre enn ungdomsskole", "Ungdomsskole", "Videregående, lavere trinn",
                "Videregående, høyere trinn", "Fagskole",
                "Bachelor", "Master eller høyere",
            ),
            "employment_levels": (
                "Ansatt", "Selvstendig næringsdrivende", "Student", "Arbeidsledig, søker arbeid",
                "Arbeidsledig, søker ikke arbeid", "Kronisk sykdom eller varig funksjonsnedsettelse",
                "Pensjonist", "Hjemmearbeidende",
            ),
            "setting": "Det er begynnelsen av 2016. Du er stemmeberettiget og bor i {}.",
            "age": "Alder: {}",
            "ideology": "Egen plassering på venstre-høyre-skalaen, 0 venstre til 10 høyre: {}",
            "born": "Du er født i {}.",
            "not_born": "Du er ikke født i {}.",
            "asylum": "Hvor mange asylsøkere landet ditt bør ta imot, -2 langt færre til 2 langt flere: {}.",
            "party": "Partiet du føler deg nærmest: {}.",
            "empathy": "Empatispørsmål {}, fra -6 til 6: {}.",
        },
        "instruction": (
            "# Valg om en asylsøknad\n\n"
            "Det er begynnelsen av 2016, under den europeiske asylkrisen.\n\n"
            "Du ser fem par. Hvert par er to personer som har søkt asyl i landet ditt, "
            "vist ved siden av hverandre, slik de ble vist til deg.\n\n"
            "Hvis du måtte velge for hvert par: Hvem av de to søkerne skal få asyl?\n\n"
            "## Slik svarer du\n\n"
            "- Svar på hvert par.\n"
            "- Bruk de oppgitte svaralternativene.\n"
        ),
        "labels": {
            "cgender": "Kjønn", "cage": "Alder", "corigin": "Opprinnelsesland", "creligion": "Religion",
            "cjob": "Tidligere yrke", "clang": "Språkkunnskaper", "creason": "Årsak til migrasjon",
            "cvulner": "Særlig sårbarhet", "cconsist": "Sammenheng i asylforklaringen",
        },
        "values": {
            "cgender": {1: "kvinne", 2: "mann"},
            "cage": {1: "21 år", 2: "38 år", 3: "62 år"},
            "corigin": {1: "Syria", 2: "Afghanistan", 3: "Kosovo", 4: "Eritrea", 5: "Pakistan", 6: "Ukraina", 7: "Irak"},
            "creligion": {1: "kristen", 2: "agnostiker", 3: "muslim"},
            "cjob": {1: "arbeidsledig", 2: "renholder", 3: "bonde", 4: "regnskapsfører", 5: "lærer", 6: "lege"},
            "clang": {1: "Snakker flytende norsk", 2: "Snakker gebrokkent norsk", 3: "Snakker ikke norsk"},
            "creason": {
                1: "Forfulgt på grunn av politiske meninger", 2: "Forfulgt på grunn av religiøs overbevisning",
                3: "Forfulgt på grunn av etnisk tilhørighet", 4: "Søker bedre økonomiske muligheter",
            },
            "cvulner": {
                1: "ingen", 2: "Posttraumatisk stresslidelse (PTSD)", 3: "Offer for tortur",
                4: "Ingen gjenlevende familiemedlemmer", 5: "Fysisk funksjonshemmet",
            },
            "cconsist": {1: "Ingen uoverensstemmelser", 2: "Mindre uoverensstemmelser", 3: "Store uoverensstemmelser"},
        },
    },
    "fr": {
        "pair": "Paire",
        "applicant": "Demandeur",
        "question": "Paire {} : lequel de ces deux demandeurs doit obtenir l'asile ?",
        "intro": (
            "Cinq paires de personnes qui ont demandé l'asile dans votre pays. "
            "Pour chaque paire, choisissez quel demandeur obtient l'asile."
        ),
        "persona": {
            "who": "un électeur",
            "country": "Pays où vous vivez",
            "education": "Plus haut diplôme",
            "employment": "Situation professionnelle",
            "income": "Décile de revenu du ménage dans votre pays, 1 le plus bas à 10 le plus haut",
            "education_levels": (
                "Inférieur au premier cycle du secondaire", "Premier cycle du secondaire", "Second cycle du secondaire, niveau inférieur",
                "Second cycle du secondaire, niveau supérieur", "Formation professionnelle supérieure",
                "Licence", "Master ou plus",
            ),
            "employment_levels": (
                "Salarié", "Indépendant", "Étudiant", "Sans emploi, en recherche",
                "Sans emploi, pas en recherche", "Maladie chronique ou handicap permanent",
                "Retraité", "Au foyer",
            ),
            "setting": "Nous sommes au début de 2016. Vous êtes électeur et vous vivez en {}.",
            "age": "Âge : {}",
            "ideology": "Position sur l'échelle gauche-droite, 0 gauche à 10 droite : {}",
            "born": "Vous êtes né en {}.",
            "not_born": "Vous n'êtes pas né en {}.",
            "asylum": "Le nombre de demandeurs d'asile que votre pays devrait accueillir, -2 beaucoup moins à 2 beaucoup plus : {}.",
            "party": "Le parti dont vous vous sentez le plus proche : {}.",
            "empathy": "Question d'empathie {}, de -6 à 6 : {}.",
        },
        "instruction": (
            "# Choix sur une demande d'asile\n\n"
            "Nous sommes au début de 2016, pendant la crise européenne de l'asile.\n\n"
            "Vous verrez cinq paires. Chaque paire présente deux personnes qui ont demandé "
            "l'asile dans votre pays, côte à côte, telles qu'elles vous ont été montrées.\n\n"
            "Pour chaque paire, si vous deviez choisir : lequel des deux demandeurs doit obtenir l'asile ?\n\n"
            "## Comment répondre\n\n"
            "- Répondez à chaque paire.\n"
            "- Utilisez les identifiants de réponse indiqués.\n"
        ),
        "labels": {
            "cgender": "Sexe", "cage": "Âge", "corigin": "Pays d'origine", "creligion": "Religion",
            "cjob": "Profession antérieure", "clang": "Compétences linguistiques", "creason": "Motif de la migration",
            "cvulner": "Vulnérabilité particulière", "cconsist": "Cohérence du récit d'asile",
        },
        "values": {
            "cgender": {1: "femme", 2: "homme"},
            "cage": {1: "21 ans", 2: "38 ans", 3: "62 ans"},
            "corigin": {1: "Syrie", 2: "Afghanistan", 3: "Kosovo", 4: "Érythrée", 5: "Pakistan", 6: "Ukraine", 7: "Irak"},
            "creligion": {1: "chrétien", 2: "agnostique", 3: "musulman"},
            "cjob": {1: "sans emploi", 2: "agent d'entretien", 3: "agriculteur", 4: "comptable", 5: "enseignant", 6: "médecin"},
            "clang": {1: "Parle couramment le français", 2: "Parle un français approximatif", 3: "Ne parle pas français"},
            "creason": {
                1: "Persécution pour opinions politiques", 2: "Persécution pour croyances religieuses",
                3: "Persécution en raison de l'appartenance ethnique", 4: "Recherche de meilleures perspectives économiques",
            },
            "cvulner": {
                1: "aucune", 2: "Trouble de stress post-traumatique (TSPT)", 3: "Victime de torture",
                4: "Aucun membre de la famille survivant", 5: "Handicap physique",
            },
            "cconsist": {1: "Aucune incohérence", 2: "Incohérences mineures", 3: "Incohérences majeures"},
        },
    },
    "es": {
        "pair": "Par",
        "applicant": "Solicitante",
        "question": "Par {}: ¿a cuál de estos dos solicitantes se le debe conceder asilo?",
        "intro": (
            "Cinco pares de personas que han solicitado asilo en su país. "
            "Para cada par, elija a qué solicitante se le concede asilo."
        ),
        "persona": {
            "who": "un votante",
            "country": "País en el que vive",
            "education": "Nivel de estudios más alto",
            "employment": "Situación laboral",
            "income": "Decil de ingresos del hogar en su país, 1 el más bajo y 10 el más alto",
            "education_levels": (
                "Menos que secundaria inferior", "Secundaria inferior", "Secundaria superior, nivel bajo",
                "Secundaria superior, nivel alto", "Formación profesional superior",
                "Grado universitario", "Máster o superior",
            ),
            "employment_levels": (
                "Asalariado", "Autónomo", "Estudiante", "Desempleado, buscando trabajo",
                "Desempleado, sin buscar trabajo", "Enfermedad crónica o discapacidad permanente",
                "Jubilado", "Trabajo en el hogar",
            ),
            "setting": "Es principios de 2016. Es usted votante y vive en {}.",
            "age": "Edad: {}",
            "ideology": "Autoubicación en la escala izquierda-derecha, 0 izquierda a 10 derecha: {}",
            "born": "Nació en {}.",
            "not_born": "No nació en {}.",
            "asylum": "Cuántos solicitantes de asilo debería aceptar su país, -2 muchos menos a 2 muchos más: {}.",
            "party": "El partido al que se siente más cercano: {}.",
            "empathy": "Pregunta de empatía {}, de -6 a 6: {}.",
        },
        "instruction": (
            "# Elección sobre una solicitud de asilo\n\n"
            "Es principios de 2016, durante la crisis europea de asilo.\n\n"
            "Verá cinco pares. Cada par son dos personas que han solicitado asilo en su país, "
            "mostradas una al lado de la otra, tal como se le mostraron.\n\n"
            "Si tuviera que elegir en cada par: ¿a cuál de los dos solicitantes se le debe conceder asilo?\n\n"
            "## Cómo responder\n\n"
            "- Responda a cada par.\n"
            "- Use los identificadores de respuesta indicados.\n"
        ),
        "labels": {
            "cgender": "Sexo", "cage": "Edad", "corigin": "País de origen", "creligion": "Religión",
            "cjob": "Ocupación anterior", "clang": "Conocimiento del idioma", "creason": "Motivo de la migración",
            "cvulner": "Vulnerabilidad especial", "cconsist": "Coherencia del testimonio de asilo",
        },
        "values": {
            "cgender": {1: "mujer", 2: "hombre"},
            "cage": {1: "21 años", 2: "38 años", 3: "62 años"},
            "corigin": {1: "Siria", 2: "Afganistán", 3: "Kosovo", 4: "Eritrea", 5: "Pakistán", 6: "Ucrania", 7: "Irak"},
            "creligion": {1: "cristiano", 2: "agnóstico", 3: "musulmán"},
            "cjob": {1: "desempleado", 2: "limpiador", 3: "agricultor", 4: "contable", 5: "docente", 6: "médico"},
            "clang": {1: "Habla español con fluidez", 2: "Habla español con dificultad", 3: "No habla español"},
            "creason": {
                1: "Persecución por opiniones políticas", 2: "Persecución por creencias religiosas",
                3: "Persecución por pertenencia étnica", 4: "Busca mejores oportunidades económicas",
            },
            "cvulner": {
                1: "ninguna", 2: "Trastorno de estrés postraumático (TEPT)", 3: "Víctima de tortura",
                4: "Ningún familiar superviviente", 5: "Discapacidad física",
            },
            "cconsist": {1: "Sin contradicciones", 2: "Contradicciones menores", 3: "Contradicciones graves"},
        },
    },
    "it": {
        "pair": "Coppia",
        "applicant": "Richiedente",
        "question": "Coppia {}: a quale dei due richiedenti va concesso l'asilo?",
        "intro": (
            "Cinque coppie di persone che hanno chiesto asilo nel suo paese. "
            "Per ogni coppia, scelga a quale richiedente viene concesso l'asilo."
        ),
        "persona": {
            "who": "un elettore",
            "country": "Paese in cui vive",
            "education": "Titolo di studio più alto",
            "employment": "Condizione occupazionale",
            "income": "Decile di reddito familiare nel suo paese, 1 il più basso e 10 il più alto",
            "education_levels": (
                "Inferiore alla secondaria inferiore", "Secondaria inferiore", "Secondaria superiore, livello basso",
                "Secondaria superiore, livello alto", "Formazione professionale superiore",
                "Laurea triennale", "Laurea magistrale o superiore",
            ),
            "employment_levels": (
                "Dipendente", "Lavoratore autonomo", "Studente", "Disoccupato, in cerca di lavoro",
                "Disoccupato, non in cerca di lavoro", "Malattia cronica o disabilità permanente",
                "Pensionato", "Lavoro domestico",
            ),
            "setting": "È l'inizio del 2016. È un elettore e vive in {}.",
            "age": "Età: {}",
            "ideology": "Autocollocazione sulla scala sinistra-destra, 0 sinistra a 10 destra: {}",
            "born": "È nato in {}.",
            "not_born": "Non è nato in {}.",
            "asylum": "Quanti richiedenti asilo il suo paese dovrebbe accogliere, -2 molti meno a 2 molti di più: {}.",
            "party": "Il partito a cui si sente più vicino: {}.",
            "empathy": "Domanda sull'empatia {}, da -6 a 6: {}.",
        },
        "instruction": (
            "# Scelta su una domanda di asilo\n\n"
            "È l'inizio del 2016, durante la crisi europea dell'asilo.\n\n"
            "Vedrà cinque coppie. Ogni coppia sono due persone che hanno chiesto asilo nel suo paese, "
            "mostrate una accanto all'altra, come le sono state presentate.\n\n"
            "Se dovesse scegliere per ogni coppia: a quale dei due richiedenti va concesso l'asilo?\n\n"
            "## Come rispondere\n\n"
            "- Risponda a ogni coppia.\n"
            "- Usi gli identificativi di risposta indicati.\n"
        ),
        "labels": {
            "cgender": "Genere", "cage": "Età", "corigin": "Paese di origine", "creligion": "Religione",
            "cjob": "Occupazione precedente", "clang": "Competenze linguistiche", "creason": "Motivo della migrazione",
            "cvulner": "Particolare vulnerabilità", "cconsist": "Coerenza della testimonianza di asilo",
        },
        "values": {
            "cgender": {1: "donna", 2: "uomo"},
            "cage": {1: "21 anni", 2: "38 anni", 3: "62 anni"},
            "corigin": {1: "Siria", 2: "Afghanistan", 3: "Kosovo", 4: "Eritrea", 5: "Pakistan", 6: "Ucraina", 7: "Iraq"},
            "creligion": {1: "cristiano", 2: "agnostico", 3: "musulmano"},
            "cjob": {1: "disoccupato", 2: "addetto alle pulizie", 3: "agricoltore", 4: "contabile", 5: "insegnante", 6: "medico"},
            "clang": {1: "Parla fluentemente l'italiano", 2: "Parla un italiano stentato", 3: "Non parla italiano"},
            "creason": {
                1: "Persecuzione per opinioni politiche", 2: "Persecuzione per convinzioni religiose",
                3: "Persecuzione per appartenenza etnica", 4: "In cerca di migliori opportunità economiche",
            },
            "cvulner": {
                1: "nessuna", 2: "Disturbo da stress post-traumatico (PTSD)", 3: "Vittima di tortura",
                4: "Nessun familiare superstite", 5: "Disabilità fisica",
            },
            "cconsist": {1: "Nessuna incongruenza", 2: "Incongruenze minori", 3: "Incongruenze gravi"},
        },
    },
    "nl": {
        "pair": "Paar",
        "applicant": "Aanvrager",
        "question": "Paar {}: welke van deze twee aanvragers moet asiel krijgen?",
        "intro": (
            "Vijf paren van personen die asiel hebben aangevraagd in uw land. "
            "Kies voor elk paar welke aanvrager asiel krijgt."
        ),
        "persona": {
            "who": "een kiesgerechtigde",
            "country": "Land waar u woont",
            "education": "Hoogst voltooide opleiding",
            "employment": "Arbeidssituatie",
            "income": "Inkomensdeciel van het huishouden in uw land, 1 het laagst tot 10 het hoogst",
            "education_levels": (
                "Minder dan lager secundair", "Lager secundair", "Hoger secundair, lager niveau",
                "Hoger secundair, hoger niveau", "Hoger beroepsonderwijs",
                "Bachelor", "Master of hoger",
            ),
            "employment_levels": (
                "Werknemer", "Zelfstandige", "Student", "Werkloos, op zoek",
                "Werkloos, niet op zoek", "Chronische ziekte of blijvende beperking",
                "Gepensioneerd", "Werkzaam in het huishouden",
            ),
            "setting": "Het is begin 2016. U bent kiesgerechtigd en woont in {}.",
            "age": "Leeftijd: {}",
            "ideology": "Eigen plaatsing op de links-rechtsschaal, 0 links tot 10 rechts: {}",
            "born": "U bent geboren in {}.",
            "not_born": "U bent niet geboren in {}.",
            "asylum": "Hoeveel asielzoekers uw land zou moeten opnemen, -2 veel minder tot 2 veel meer: {}.",
            "party": "De partij waarbij u zich het meest thuis voelt: {}.",
            "empathy": "Empathievraag {}, van -6 tot 6: {}.",
        },
        "instruction": (
            "# Keuze over een asielaanvraag\n\n"
            "Het is begin 2016, tijdens de Europese asielcrisis.\n\n"
            "U ziet vijf paren. Elk paar zijn twee personen die asiel hebben aangevraagd in uw land, "
            "naast elkaar getoond, zoals ze aan u zijn voorgelegd.\n\n"
            "Als u voor elk paar zou moeten kiezen: welke van de twee aanvragers moet asiel krijgen?\n\n"
            "## Hoe te antwoorden\n\n"
            "- Beantwoord elk paar.\n"
            "- Gebruik de vermelde antwoordcodes.\n"
        ),
        "labels": {
            "cgender": "Geslacht", "cage": "Leeftijd", "corigin": "Land van herkomst", "creligion": "Religie",
            "cjob": "Vorig beroep", "clang": "Taalvaardigheid", "creason": "Reden van migratie",
            "cvulner": "Bijzondere kwetsbaarheid", "cconsist": "Consistentie van de asielverklaring",
        },
        "values": {
            "cgender": {1: "vrouw", 2: "man"},
            "cage": {1: "21 jaar", 2: "38 jaar", 3: "62 jaar"},
            "corigin": {1: "Syrië", 2: "Afghanistan", 3: "Kosovo", 4: "Eritrea", 5: "Pakistan", 6: "Oekraïne", 7: "Irak"},
            "creligion": {1: "christen", 2: "agnost", 3: "moslim"},
            "cjob": {1: "werkloos", 2: "schoonmaker", 3: "boer", 4: "boekhouder", 5: "leraar", 6: "arts"},
            "clang": {1: "Spreekt vloeiend Nederlands", 2: "Spreekt gebrekkig Nederlands", 3: "Spreekt geen Nederlands"},
            "creason": {
                1: "Vervolging vanwege politieke opvattingen", 2: "Vervolging vanwege religieuze overtuiging",
                3: "Vervolging vanwege etniciteit", 4: "Op zoek naar betere economische kansen",
            },
            "cvulner": {
                1: "geen", 2: "Posttraumatische stressstoornis (PTSS)", 3: "Slachtoffer van foltering",
                4: "Geen overlevende familieleden", 5: "Lichamelijk gehandicapt",
            },
            "cconsist": {1: "Geen tegenstrijdigheden", 2: "Kleine tegenstrijdigheden", 3: "Grote tegenstrijdigheden"},
        },
    },
    "cs": {
        "pair": "Dvojice",
        "applicant": "Žadatel",
        "question": "Dvojice {}: Kterému z těchto dvou žadatelů má být udělen azyl?",
        "intro": (
            "Pět dvojic osob, které požádaly o azyl ve vaší zemi. "
            "U každé dvojice vyberte, kterému žadateli se azyl udělí."
        ),
        "persona": {
            "who": "volič",
            "country": "Země, ve které žijete",
            "education": "Nejvyšší dosažené vzdělání",
            "employment": "Ekonomické postavení",
            "income": "Decil příjmu domácnosti ve vaší zemi, 1 nejnižší až 10 nejvyšší",
            "education_levels": (
                "Méně než nižší střední", "Nižší střední", "Vyšší střední, nižší stupeň",
                "Vyšší střední, vyšší stupeň", "Vyšší odborné",
                "Bakalářské", "Magisterské nebo vyšší",
            ),
            "employment_levels": (
                "Zaměstnanec", "Osoba samostatně výdělečně činná", "Student", "Nezaměstnaný, hledá práci",
                "Nezaměstnaný, nehledá práci", "Chronická nemoc nebo trvalý invalidní důchod",
                "V důchodu", "V domácnosti",
            ),
            "setting": "Je začátek roku 2016. Jste volič a žijete v zemi {}.",
            "age": "Věk: {}",
            "ideology": "Vlastní umístění na škále levice-pravice, 0 levice až 10 pravice: {}",
            "born": "Narodil jste se v zemi {}.",
            "not_born": "Nenarodil jste se v zemi {}.",
            "asylum": "Kolik žadatelů o azyl by vaše země měla přijmout, -2 mnohem méně až 2 mnohem více: {}.",
            "party": "Strana, které jste nejblíže: {}.",
            "empathy": "Otázka empatie {}, od -6 do 6: {}.",
        },
        "instruction": (
            "# Rozhodnutí o žádosti o azyl\n\n"
            "Je začátek roku 2016, v době evropské azylové krize.\n\n"
            "Uvidíte pět dvojic. Každá dvojice jsou dva lidé, kteří požádali o azyl ve vaší zemi, "
            "zobrazení vedle sebe tak, jak vám byli předloženi.\n\n"
            "Kdybyste se měl u každé dvojice rozhodnout: kterému ze dvou žadatelů má být udělen azyl?\n\n"
            "## Jak odpovídat\n\n"
            "- Odpovězte na každou dvojici.\n"
            "- Použijte uvedené kódy odpovědí.\n"
        ),
        "labels": {
            "cgender": "Pohlaví", "cage": "Věk", "corigin": "Země původu", "creligion": "Náboženství",
            "cjob": "Předchozí povolání", "clang": "Jazykové znalosti", "creason": "Důvod migrace",
            "cvulner": "Zvláštní zranitelnost", "cconsist": "Soulad výpovědi o azylu",
        },
        "values": {
            "cgender": {1: "žena", 2: "muž"},
            "cage": {1: "21 let", 2: "38 let", 3: "62 let"},
            "corigin": {1: "Sýrie", 2: "Afghánistán", 3: "Kosovo", 4: "Eritrea", 5: "Pákistán", 6: "Ukrajina", 7: "Irák"},
            "creligion": {1: "křesťan", 2: "agnostik", 3: "muslim"},
            "cjob": {1: "nezaměstnaný", 2: "uklízeč", 3: "zemědělec", 4: "účetní", 5: "učitel", 6: "lékař"},
            "clang": {1: "Mluví plynně česky", 2: "Mluví lámanou češtinou", 3: "Nemluví česky"},
            "creason": {
                1: "Pronásledování kvůli politickým názorům", 2: "Pronásledování kvůli náboženskému vyznání",
                3: "Pronásledování kvůli etnické příslušnosti", 4: "Hledá lepší ekonomické příležitosti",
            },
            "cvulner": {
                1: "žádná", 2: "Posttraumatická stresová porucha (PTSD)", 3: "Oběť mučení",
                4: "Žádní přeživší rodinní příslušníci", 5: "Tělesně postižený",
            },
            "cconsist": {1: "Žádné rozpory", 2: "Drobné rozpory", 3: "Zásadní rozpory"},
        },
    },
    "pl": {
        "pair": "Para",
        "applicant": "Wnioskodawca",
        "question": "Para {}: Któremu z tych dwóch wnioskodawców należy przyznać azyl?",
        "intro": (
            "Pięć par osób, które złożyły wniosek o azyl w twoim kraju. "
            "Dla każdej pary wybierz, któremu wnioskodawcy przyznaje się azyl."
        ),
        "persona": {
            "who": "uprawniony do głosowania",
            "country": "Kraj, w którym mieszkasz",
            "education": "Najwyższe wykształcenie",
            "employment": "Status zawodowy",
            "income": "Decyl dochodu gospodarstwa w twoim kraju, 1 najniższy do 10 najwyższy",
            "education_levels": (
                "Poniżej gimnazjum", "Gimnazjum", "Szkoła średnia, niższy poziom",
                "Szkoła średnia, wyższy poziom", "Szkoła policealna",
                "Licencjat", "Magisterium lub wyżej",
            ),
            "employment_levels": (
                "Pracownik najemny", "Pracujący na własny rachunek", "Uczeń lub student", "Bezrobotny, szuka pracy",
                "Bezrobotny, nie szuka pracy", "Choroba przewlekła lub trwała niepełnosprawność",
                "Emeryt", "Praca w domu",
            ),
            "setting": "Jest początek 2016 roku. Masz prawo głosu i mieszkasz w kraju {}.",
            "age": "Wiek: {}",
            "ideology": "Własne miejsce na skali lewica-prawica, 0 lewica do 10 prawica: {}",
            "born": "Urodziłeś się w kraju {}.",
            "not_born": "Nie urodziłeś się w kraju {}.",
            "asylum": "Ilu ubiegających się o azyl powinien przyjąć twój kraj, -2 znacznie mniej do 2 znacznie więcej: {}.",
            "party": "Partia, której jesteś najbliższy: {}.",
            "empathy": "Pytanie o empatię {}, od -6 do 6: {}.",
        },
        "instruction": (
            "# Wybór w sprawie wniosku o azyl\n\n"
            "Jest początek 2016 roku, czas europejskiego kryzysu azylowego.\n\n"
            "Zobaczysz pięć par. Każda para to dwie osoby, które złożyły wniosek o azyl w twoim kraju, "
            "pokazane obok siebie, tak jak ci je przedstawiono.\n\n"
            "Gdybyś musiał wybrać w każdej parze: któremu z dwóch wnioskodawców należy przyznać azyl?\n\n"
            "## Jak odpowiadać\n\n"
            "- Odpowiedz na każdą parę.\n"
            "- Użyj podanych identyfikatorów odpowiedzi.\n"
        ),
        "labels": {
            "cgender": "Płeć", "cage": "Wiek", "corigin": "Kraj pochodzenia", "creligion": "Religia",
            "cjob": "Poprzedni zawód", "clang": "Znajomość języka", "creason": "Powód migracji",
            "cvulner": "Szczególna bezbronność", "cconsist": "Spójność zeznań azylowych",
        },
        "values": {
            "cgender": {1: "kobieta", 2: "mężczyzna"},
            "cage": {1: "21 lat", 2: "38 lat", 3: "62 lata"},
            "corigin": {1: "Syria", 2: "Afganistan", 3: "Kosowo", 4: "Erytrea", 5: "Pakistan", 6: "Ukraina", 7: "Irak"},
            "creligion": {1: "chrześcijanin", 2: "agnostyk", 3: "muzułmanin"},
            "cjob": {1: "bezrobotny", 2: "sprzątacz", 3: "rolnik", 4: "księgowy", 5: "nauczyciel", 6: "lekarz"},
            "clang": {1: "Mówi biegle po polsku", 2: "Mówi łamaną polszczyzną", 3: "Nie mówi po polsku"},
            "creason": {
                1: "Prześladowanie za poglądy polityczne", 2: "Prześladowanie za przekonania religijne",
                3: "Prześladowanie ze względu na pochodzenie etniczne", 4: "Szuka lepszych możliwości ekonomicznych",
            },
            "cvulner": {
                1: "brak", 2: "Zespół stresu pourazowego (PTSD)", 3: "Ofiara tortur",
                4: "Brak żyjących członków rodziny", 5: "Niepełnosprawność fizyczna",
            },
            "cconsist": {1: "Brak sprzeczności", 2: "Drobne sprzeczności", 3: "Poważne sprzeczności"},
        },
    },
    "hu": {
        "pair": "Pár",
        "applicant": "Kérelmező",
        "question": "Pár {}: a két kérelmező közül melyik kapjon menedékjogot?",
        "intro": (
            "Öt pár, olyan személyekből, akik az Ön országában menedékjogot kértek. "
            "Minden párnál válassza ki, melyik kérelmező kap menedékjogot."
        ),
        "persona": {
            "who": "választópolgár",
            "country": "Az ország, ahol él",
            "education": "Legmagasabb iskolai végzettség",
            "employment": "Munkaerőpiaci helyzet",
            "income": "A háztartás jövedelmi tizede az Ön országában, 1 a legalacsonyabb, 10 a legmagasabb",
            "education_levels": (
                "Az alsó középfokúnál alacsonyabb", "Alsó középfokú", "Felső középfokú, alsó szint",
                "Felső középfokú, felső szint", "Felsőfokú szakképzés",
                "Alapképzés", "Mesterképzés vagy magasabb",
            ),
            "employment_levels": (
                "Alkalmazott", "Önfoglalkoztató", "Tanuló", "Munkanélküli, állást keres",
                "Munkanélküli, nem keres állást", "Krónikus betegség vagy tartós rokkantság",
                "Nyugdíjas", "Otthon dolgozik",
            ),
            "setting": "2016 eleje van. Választópolgár, és itt él: {}.",
            "age": "Életkor: {}",
            "ideology": "Önbesorolás a bal-jobb skálán, 0 baloldal, 10 jobboldal: {}",
            "born": "Itt született: {}.",
            "not_born": "Nem itt született: {}.",
            "asylum": "Hány menedékkérőt kellene befogadnia az országának, -2 sokkal kevesebbet, 2 sokkal többet: {}.",
            "party": "Az a párt, amelyhez a legközelebb érzi magát: {}.",
            "empathy": "Empátiakérdés {}, -6-tól 6-ig: {}.",
        },
        "instruction": (
            "# Döntés egy menedékkérelemről\n\n"
            "2016 eleje van, az európai menedékválság idején.\n\n"
            "Öt párt fog látni. Minden pár két olyan személy, aki az Ön országában menedékjogot kért, "
            "egymás mellett, úgy, ahogyan Önnek megmutatták.\n\n"
            "Ha minden párnál választania kellene: a két kérelmező közül melyik kapjon menedékjogot?\n\n"
            "## Hogyan válaszoljon\n\n"
            "- Válaszoljon minden párra.\n"
            "- A megadott válaszkódokat használja.\n"
        ),
        "labels": {
            "cgender": "Nem", "cage": "Életkor", "corigin": "Származási ország", "creligion": "Vallás",
            "cjob": "Korábbi foglalkozás", "clang": "Nyelvtudás", "creason": "A migráció oka",
            "cvulner": "Különös kiszolgáltatottság", "cconsist": "A menedékvallomás következetessége",
        },
        "values": {
            "cgender": {1: "nő", 2: "férfi"},
            "cage": {1: "21 éves", 2: "38 éves", 3: "62 éves"},
            "corigin": {1: "Szíria", 2: "Afganisztán", 3: "Koszovó", 4: "Eritrea", 5: "Pakisztán", 6: "Ukrajna", 7: "Irak"},
            "creligion": {1: "keresztény", 2: "agnosztikus", 3: "muszlim"},
            "cjob": {1: "munkanélküli", 2: "takarító", 3: "földműves", 4: "könyvelő", 5: "tanár", 6: "orvos"},
            "clang": {1: "Folyékonyan beszél magyarul", 2: "Törve beszél magyarul", 3: "Nem beszél magyarul"},
            "creason": {
                1: "Üldözés politikai nézetei miatt", 2: "Üldözés vallási meggyőződése miatt",
                3: "Üldözés etnikai hovatartozása miatt", 4: "Jobb gazdasági lehetőségeket keres",
            },
            "cvulner": {
                1: "nincs", 2: "Poszttraumás stressz zavar (PTSD)", 3: "Kínzás áldozata",
                4: "Nincs élő családtagja", 5: "Testi fogyatékos",
            },
            "cconsist": {1: "Nincs ellentmondás", 2: "Kisebb ellentmondások", 3: "Súlyos ellentmondások"},
        },
    },
    "el": {
        "pair": "Ζεύγος",
        "applicant": "Αιτών",
        "question": "Ζεύγος {}: σε ποιον από τους δύο αιτούντες πρέπει να δοθεί άσυλο;",
        "intro": (
            "Πέντε ζεύγη ανθρώπων που έχουν ζητήσει άσυλο στη χώρα σας. "
            "Για κάθε ζεύγος, επιλέξτε σε ποιον αιτούντα δίνεται άσυλο."
        ),
        "persona": {
            "who": "ένας ψηφοφόρος",
            "country": "Χώρα όπου ζείτε",
            "education": "Ανώτατο επίπεδο εκπαίδευσης",
            "employment": "Κατάσταση απασχόλησης",
            "income": "Δεκατημόριο εισοδήματος του νοικοκυριού στη χώρα σας, 1 το χαμηλότερο έως 10 το υψηλότερο",
            "education_levels": (
                "Κατώτερο από κατώτερη δευτεροβάθμια", "Κατώτερη δευτεροβάθμια", "Ανώτερη δευτεροβάθμια, χαμηλότερη βαθμίδα",
                "Ανώτερη δευτεροβάθμια, ανώτερη βαθμίδα", "Μεταδευτεροβάθμια επαγγελματική",
                "Πτυχίο", "Μεταπτυχιακό ή ανώτερο",
            ),
            "employment_levels": (
                "Μισθωτός", "Αυτοαπασχολούμενος", "Σπουδαστής", "Άνεργος, αναζητά εργασία",
                "Άνεργος, δεν αναζητά εργασία", "Χρόνια ασθένεια ή μόνιμη αναπηρία",
                "Συνταξιούχος", "Οικιακή εργασία",
            ),
            "setting": "Είναι αρχές του 2016. Είστε ψηφοφόρος και ζείτε στη χώρα {}.",
            "age": "Ηλικία: {}",
            "ideology": "Αυτοτοποθέτηση στην κλίμακα αριστερά-δεξιά, 0 αριστερά έως 10 δεξιά: {}",
            "born": "Γεννηθήκατε στη χώρα {}.",
            "not_born": "Δεν γεννηθήκατε στη χώρα {}.",
            "asylum": "Πόσους αιτούντες άσυλο θα έπρεπε να δέχεται η χώρα σας, -2 πολύ λιγότερους έως 2 πολύ περισσότερους: {}.",
            "party": "Το κόμμα στο οποίο αισθάνεστε πιο κοντά: {}.",
            "empathy": "Ερώτηση ενσυναίσθησης {}, από -6 έως 6: {}.",
        },
        "instruction": (
            "# Επιλογή για μια αίτηση ασύλου\n\n"
            "Είναι αρχές του 2016, κατά την ευρωπαϊκή κρίση ασύλου.\n\n"
            "Θα δείτε πέντε ζεύγη. Κάθε ζεύγος είναι δύο άνθρωποι που έχουν ζητήσει άσυλο στη χώρα σας, "
            "ο ένας δίπλα στον άλλον, όπως σας παρουσιάστηκαν.\n\n"
            "Αν έπρεπε να διαλέξετε για κάθε ζεύγος: σε ποιον από τους δύο αιτούντες πρέπει να δοθεί άσυλο;\n\n"
            "## Πώς να απαντήσετε\n\n"
            "- Απαντήστε σε κάθε ζεύγος.\n"
            "- Χρησιμοποιήστε τους κωδικούς απάντησης που αναγράφονται.\n"
        ),
        "labels": {
            "cgender": "Φύλο", "cage": "Ηλικία", "corigin": "Χώρα καταγωγής", "creligion": "Θρήσκευμα",
            "cjob": "Προηγούμενο επάγγελμα", "clang": "Γλωσσικές δεξιότητες", "creason": "Λόγος μετανάστευσης",
            "cvulner": "Ιδιαίτερη ευαλωτότητα", "cconsist": "Συνοχή της κατάθεσης ασύλου",
        },
        "values": {
            "cgender": {1: "γυναίκα", 2: "άνδρας"},
            "cage": {1: "21 ετών", 2: "38 ετών", 3: "62 ετών"},
            "corigin": {1: "Συρία", 2: "Αφγανιστάν", 3: "Κοσσυφοπέδιο", 4: "Ερυθραία", 5: "Πακιστάν", 6: "Ουκρανία", 7: "Ιράκ"},
            "creligion": {1: "χριστιανός", 2: "αγνωστικιστής", 3: "μουσουλμάνος"},
            "cjob": {1: "άνεργος", 2: "καθαριστής", 3: "αγρότης", 4: "λογιστής", 5: "δάσκαλος", 6: "γιατρός"},
            "clang": {1: "Μιλάει άπταιστα ελληνικά", 2: "Μιλάει σπαστά ελληνικά", 3: "Δεν μιλάει ελληνικά"},
            "creason": {
                1: "Δίωξη για πολιτικές απόψεις", 2: "Δίωξη για θρησκευτικές πεποιθήσεις",
                3: "Δίωξη λόγω εθνότητας", 4: "Αναζητά καλύτερες οικονομικές ευκαιρίες",
            },
            "cvulner": {
                1: "καμία", 2: "Διαταραχή μετατραυματικού στρες (PTSD)", 3: "Θύμα βασανιστηρίων",
                4: "Κανένα επιζών μέλος της οικογένειας", 5: "Σωματική αναπηρία",
            },
            "cconsist": {1: "Καμία αντίφαση", 2: "Μικρές αντιφάσεις", 3: "Σοβαρές αντιφάσεις"},
        },
    },
}


def surface(country: str) -> dict:
    """Instrument text for one respondent. Unknown country, including Switzerland, is English."""
    code = SURVEY_LANGUAGE.get(str(country), "en")
    text = SURFACES[code]
    if str(country) == "Switzerland":
        values = {attr: dict(levels) for attr, levels in text["values"].items()}
        values["clang"] = {
            1: "Speaks fluent the local language",
            2: "Speaks broken the local language",
            3: "Speaks no the local language",
        }
        text = {**text, "values": values}
    return text
