"""
Zentrale Keyword-Topic-Definitionen (aus routes/analytics.py extrahiert).

Wird von der Topic-Übersicht (routes/analytics.py) und der
Erklärungsgenerierung (services/explanation_service.py) gemeinsam genutzt.
Die Definitionen sind unverändert aus dem ersten Design-Zyklus übernommen.
"""

# Topics für Mitarbeiter (employee)
EMPLOYEE_TOPIC_DEFINITIONS = {
    "Work-Life Balance": {
        "keywords": [
            r'\bwork[\s-]*life[\s-]*balance\b',
            r'\büberstunden\b',
            r'\barbeitszeit\b',
            r'\burlaub\b',
            r'\bfreizeit\b',
            r'\bprivatleben\b',
            r'\bflexibilität\b',
            r'\bhomeoffice\b',
            r'\berreichbarkeit\b'
        ],
        "rating_fields": ["sternebewertung_work_life_balance"]
    },
    "Vorgesetztenverhalten": {
        "keywords": [
            r'\bführung\b',
            r'\bmanagement\b',
            r'\bvorgesetzte\b',
            r'\bchef\b',
            r'\bleitung\b',
            r'\bführungskräfte\b',
            r'\bvorgesetztenverhalten\b',
            r'\bkompetenz\b',
            r'\bentscheidung\b'
        ],
        "rating_fields": ["sternebewertung_vorgesetztenverhalten"]
    },
    "Gehalt & Sozialleistungen": {
        "keywords": [
            r'\bgehalt\b',
            r'\bbezahlung\b',
            r'\blohn\b',
            r'\bvergütung\b',
            r'\bbenefits\b',
            r'\bsozialleistungen\b',
            r'\baltersvorsorge\b',
            r'\bprämie\b',
            r'\bbonus\b'
        ],
        "rating_fields": ["sternebewertung_gehalt_sozialleistungen"]
    },
    "Kollegenzusammenhalt": {
        "keywords": [
            r'\bteam\b',
            r'\bkollegen\b',
            r'\bzusammenhalt\b',
            r'\bkollegenzusammenhalt\b',
            r'\bzusammenarbeit\b',
            r'\bgemeinschaft\b'
        ],
        "rating_fields": ["sternebewertung_kollegenzusammenhalt"]
    },
    "Karriere & Weiterbildung": {
        "keywords": [
            r'\bkarriere\b',
            r'\bweiterbildung\b',
            r'\bentwicklung\b',
            r'\baufstieg\b',
            r'\bförderung\b',
            r'\bschulungen\b',
            r'\bbeförderung\b',
            r'\bperspektive\b'
        ],
        "rating_fields": ["sternebewertung_karriere_weiterbildung"]
    },
    "Kommunikation": {
        "keywords": [
            r'\bkommunikation\b',
            r'\binformation\b',
            r'\btransparenz\b',
            r'\bfeedback\b',
            r'\bgespräch\b',
            r'\baustausch\b',
            r'\brückmeldung\b'
        ],
        "rating_fields": ["sternebewertung_kommunikation"]
    },
    "Arbeitsbedingungen": {
        "keywords": [
            r'\barbeitsbedingungen\b',
            r'\bausstattung\b',
            r'\bbüro\b',
            r'\barbeitsplatz\b',
            r'\btechnik\b',
            r'\bumgebung\b',
            r'\binfrastruktur\b'
        ],
        "rating_fields": ["sternebewertung_arbeitsbedingungen"]
    },
    "Arbeitsatmosphäre": {
        "keywords": [
            r'\batmosphäre\b',
            r'\barbeitsatmosphäre\b',
            r'\barbeitsklima\b',
            r'\bstimmung\b',
            r'\bklima\b'
        ],
        "rating_fields": ["sternebewertung_arbeitsatmosphaere"]
    },
    "Image": {
        "keywords": [
            r'\bimage\b',
            r'\bruf\b',
            r'\breputation\b',
            r'\bansehen\b',
            r'\bbekanntheitsgrad\b'
        ],
        "rating_fields": ["sternebewertung_image"]
    },
    "Interessante Aufgaben": {
        "keywords": [
            r'\baufgaben\b',
            r'\btätigkeit\b',
            r'\binteressant\b',
            r'\bherausforderung\b',
            r'\babwechslung\b',
            r'\bvielfalt\b'
        ],
        "rating_fields": ["sternebewertung_interessante_aufgaben"]
    },
    "Umwelt- & Sozialbewusstsein": {
        "keywords": [
            r'\bumwelt\b',
            r'\bnachhaltigkeit\b',
            r'\bsozialbewusstsein\b',
            r'\bverantwortung\b',
            r'\böko\b',
            r'\bklima\b'
        ],
        "rating_fields": ["sternebewertung_umwelt_sozialbewusstsein"]
    },
    "Umgang mit älteren Kollegen": {
        "keywords": [
            r'\bältere kollegen\b',
            r'\balter\b',
            r'\bsenior\b',
            r'\berfahrung\b',
            r'\bumgang\b'
        ],
        "rating_fields": ["sternebewertung_umgang_mit_aelteren_kollegen"]
    },
    "Gleichberechtigung": {
        "keywords": [
            r'\bgleichberechtigung\b',
            r'\bdiversität\b',
            r'\bvielfalt\b',
            r'\bdiskriminierung\b',
            r'\bchancengleichheit\b',
            r'\binklusion\b'
        ],
        "rating_fields": ["sternebewertung_gleichberechtigung"]
    }
}

# Topics für Bewerber (candidates)
CANDIDATE_TOPIC_DEFINITIONS = {
    "Erklärung der weiteren Schritte": {
        "keywords": [
            r'\bschritte\b',
            r'\bweitere schritte\b',
            r'\bprozess\b',
            r'\berklärung\b',
            r'\binformation\b',
            r'\bablauf\b'
        ],
        "rating_fields": ["sternebewertung_erklaerung_der_weiteren_schritte"]
    },
    "Zufriedenstellende Reaktion": {
        "keywords": [
            r'\breaktion\b',
            r'\brückmeldung\b',
            r'\bantwort\b',
            r'\bresponse\b',
            r'\bzufriedenstellend\b'
        ],
        "rating_fields": ["sternebewertung_zufriedenstellende_reaktion"]
    },
    "Vollständigkeit der Infos": {
        "keywords": [
            r'\binformation\b',
            r'\binfos\b',
            r'\bvollständig\b',
            r'\bdetail\b',
            r'\bausführlich\b'
        ],
        "rating_fields": ["sternebewertung_vollstaendigkeit_der_infos"]
    },
    "Zufriedenstellende Antworten": {
        "keywords": [
            r'\bantwort\b',
            r'\bfrage\b',
            r'\bzufriedenstellend\b',
            r'\bauskunft\b'
        ],
        "rating_fields": ["sternebewertung_zufriedenstellende_antworten"]
    },
    "Angenehme Atmosphäre": {
        "keywords": [
            r'\batmosphäre\b',
            r'\bangenehm\b',
            r'\bstimmung\b',
            r'\bklima\b',
            r'\bwohlbefinden\b'
        ],
        "rating_fields": ["sternebewertung_angenehme_atmosphaere"]
    },
    "Professionalität des Gesprächs": {
        "keywords": [
            r'\bprofessionalität\b',
            r'\bgespräch\b',
            r'\binterview\b',
            r'\bprofessionell\b',
            r'\bkompetent\b'
        ],
        "rating_fields": ["sternebewertung_professionalitaet_des_gespraechs"]
    },
    "Wertschätzende Behandlung": {
        "keywords": [
            r'\bwertschätzung\b',
            r'\bbehandlung\b',
            r'\brespekt\b',
            r'\bwertschätzend\b',
            r'\bhöflich\b'
        ],
        "rating_fields": ["sternebewertung_wertschaetzende_behandlung"]
    },
    "Erwartbarkeit des Prozesses": {
        "keywords": [
            r'\berwartbarkeit\b',
            r'\bprozess\b',
            r'\bvorhersehbar\b',
            r'\bstruktur\b',
            r'\borganisation\b'
        ],
        "rating_fields": ["sternebewertung_erwartbarkeit_des_prozesses"]
    },
    "Zeitgerechte Zu- oder Absage": {
        "keywords": [
            r'\bzusage\b',
            r'\babsage\b',
            r'\bzeitgerecht\b',
            r'\bpünktlich\b',
            r'\bfrist\b',
            r'\btermin\b'
        ],
        "rating_fields": ["sternebewertung_zeitgerechte_zu_oder_absage"]
    },
    "Schnelle Antwort": {
        "keywords": [
            r'\bschnell\b',
            r'\bantwort\b',
            r'\breaktionszeit\b',
            r'\bzügig\b',
            r'\bprompt\b'
        ],
        "rating_fields": ["sternebewertung_schnelle_antwort"]
    }
}

TOPIC_DEFINITIONS_BY_SOURCE = {
    "employee": EMPLOYEE_TOPIC_DEFINITIONS,
    "candidates": CANDIDATE_TOPIC_DEFINITIONS,
}


def dimension_key_for_topic(topic_name: str, source: str = "employee") -> str | None:
    """Dimensionsschlüssel (z.B. 'kommunikation') zu einem Topic-Anzeigenamen."""
    config = TOPIC_DEFINITIONS_BY_SOURCE[source].get(topic_name)
    if not config or not config.get("rating_fields"):
        return None
    return config["rating_fields"][0].removeprefix("sternebewertung_")


def topic_for_dimension_key(dimension: str, source: str = "employee") -> str | None:
    """Topic-Anzeigename zu einem Dimensionsschlüssel (Umkehrung)."""
    for topic_name in TOPIC_DEFINITIONS_BY_SOURCE[source]:
        if dimension_key_for_topic(topic_name, source) == dimension:
            return topic_name
    return None
