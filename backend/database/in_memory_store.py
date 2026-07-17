"""
In-memory data store with Demo 1 data.
Provides a Supabase-compatible client API so all existing routes work unchanged.
"""

import random
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

random.seed(42)

# ---------------------------------------------------------------------------
# Demo data generation (mirrors scripts/seed_demo1.py)
# ---------------------------------------------------------------------------

def _rand_rating(mu, sigma=0.6, lo=1.0, hi=5.0):
    v = random.gauss(mu, sigma)
    return round(max(lo, min(hi, v)), 2)


def _date_between(start: datetime, end: datetime) -> str:
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.date().isoformat()


_START = datetime(2022, 1, 1)
_MID = datetime(2023, 6, 1)
_END = datetime(2025, 4, 30)

_GUT_POOL = [
    "Das Team ist sehr kollegial und hilfsbereit. Man fühlt sich vom ersten Tag an willkommen.",
    "Flexible Arbeitszeiten und die Möglichkeit zum Homeoffice sind ein großer Pluspunkt.",
    "Interessante und abwechslungsreiche Aufgaben, die wirklich fordern und fördern.",
    "Modernes Büro mit sehr guter technischer Ausstattung. Die Arbeitsumgebung macht Spaß.",
    "Offene Fehlerkultur – Fehler werden als Lernchance gesehen, nicht bestraft.",
    "Regelmäßige Weiterbildungen werden aktiv angeboten und auch finanziert.",
    "Sehr gutes Betriebsklima, Teamevents und gemeinsame Mittagessen stärken den Zusammenhalt.",
    "Flache Hierarchien ermöglichen schnelle Entscheidungen und direkten Kontakt zur Führungsebene.",
    "Faire und pünktliche Gehaltszahlung, gute Sozialleistungen wie Jobticket und Essenszuschuss.",
    "Nachhaltigkeitsprojekte und soziales Engagement werden großgeschrieben.",
    "Die Produkte sind technisch anspruchsvoll – man lernt täglich etwas Neues.",
    "Gute Kantine mit gesunden Optionen zu günstigen Preisen.",
    "Vertrauensarbeitszeit ohne Stechuhr, das gibt wirklich Autonomie.",
    "Ehrliche und transparente Kommunikation von der Geschäftsführung.",
    "Regelmäßige 1:1-Gespräche mit dem Vorgesetzten. Man fühlt sich wahrgenommen.",
    "Kindergartenzuschuss und Elternzeitregelung sind sehr familienfreundlich.",
    "Sehr gutes Onboarding-Programm – ich war schnell produktiv.",
    "Das Unternehmen investiert sichtbar in seine Mitarbeiter.",
    "Freie Wahl des Betriebssystems und der Entwicklungstools.",
    "Offene Büroküche, kostenloser Kaffee und Obst – kleine Dinge, die zählen.",
]

_SCHLECHT_POOL = [
    "Die interne Kommunikation zwischen den Abteilungen lässt manchmal zu wünschen übrig.",
    "Gehalt liegt leicht unter dem Marktdurchschnitt, Verhandlungsspielraum war begrenzt.",
    "Homeoffice-Regelung war lange Zeit unklar und hat sich mehrfach geändert.",
    "Zu viele parallele Projekte gleichzeitig – Priorisierung fehlt oft.",
    "Bürokratie bei kleinen Entscheidungen bremst die Umsetzungsgeschwindigkeit.",
    "Parkplatzsituation ist schwierig, öffentliche Anbindung könnte besser sein.",
    "Klimaanlage im Großraumbüro ist oft Streitthema, zu kalt im Sommer.",
    "Beförderungsprozesse sind intransparent und nicht klar kommuniziert.",
    "Schichtarbeit an Wochenenden wird nicht ausreichend vergütet.",
    "Die technischen Systeme sind teilweise veraltet und bremsen den Workflow.",
    "Abteilungsübergreifende Projekte scheitern oft an unklarer Verantwortlichkeit.",
    "Hohe Fluktuation in manchen Abteilungen sorgt für Wissensverlust.",
    "Überstunden werden erwartet aber nicht immer transparent kommuniziert.",
    "Meeting-Kultur ist überladen – zu viele Besprechungen ohne klare Agenda.",
    "Feedbackgespräche finden nicht regelmäßig statt.",
]

_VERBESSERUNG_POOL = [
    "Mehr Transparenz bei Gehaltsstrukturen und Karrierepfaden wäre wünschenswert.",
    "Regelmäßigere All-Hands-Meetings würden die abteilungsübergreifende Kommunikation verbessern.",
    "Ein strukturiertes Mentoring-Programm für neue Mitarbeiter würde helfen.",
    "Homeoffice-Budget für ergonomische Ausstattung zu Hause wäre ein gutes Signal.",
    "Mehr Einbindung der Mitarbeiter in strategische Entscheidungen.",
    "Kürzere und effizientere Meetings durch klare Agenda und Timebox.",
    "Überarbeitung der Schichtplanung zur besseren Work-Life-Balance.",
    "Modernisierung der internen Softwaresysteme ist dringend überfällig.",
    "Klarere Feedback-Kultur und strukturierte Mitarbeiterjahresgespräche.",
    "Stärkere Förderung von Frauen in Führungspositionen.",
    "Flexiblere Teilzeitmodelle auch für Führungskräfte anbieten.",
    "Bessere Kantine mit mehr vegetarischen und veganen Optionen.",
    "Ausbau des betrieblichen Gesundheitsmanagements.",
    "Mehr Weiterbildungsbudget pro Mitarbeiter pro Jahr.",
    "Klare Eskalationswege bei Konflikten im Team einführen.",
]

_TOPIC_TEXTS = {
    "arbeitsatmosphaere": [
        "Die Atmosphäre im Team ist offen und vertrauensvoll. Man hilft sich gegenseitig.",
        "Kollegiales Miteinander auf Augenhöhe – keine Ellbogenmentalität.",
        "Das Arbeitsklima ist insgesamt positiv, gelegentlich gibt es Spannungen unter Druck.",
        "Wertschätzende Atmosphäre, Erfolge werden gefeiert.",
        "Manchmal hektisch, aber das Team hält zusammen.",
        "Entspannte und produktive Atmosphäre dank flacher Hierarchien.",
        "Gelegentliche Spannungen durch Ressourcenengpässe, aber grundsätzlich gut.",
        "Sehr angenehmes Arbeitsumfeld mit viel gegenseitigem Respekt.",
        "Der Teamgeist ist ausgezeichnet, auch in stressigen Phasen.",
    ],
    "image": [
        "Das Unternehmen hat einen guten Ruf in der Branche und wird von Kunden geschätzt.",
        "Image nach außen sehr professionell, intern manchmal Diskrepanz zur Realität.",
        "Bekannte Marke – man ist stolz, hier zu arbeiten.",
        "Hohes Ansehen bei Partnern und Kunden, stärkt die eigene Motivation.",
        "Positives Image hilft bei der Kundenakquise.",
        "Marke könnte in der Tech-Community sichtbarer sein.",
        "Sehr guter Ruf als Arbeitgeber in der Region.",
    ],
    "work_life_balance": [
        "Flexible Gleitzeit und echte Möglichkeit zum Homeoffice ermöglichen gute Balance.",
        "Urlaub kann problemlos genommen werden, kein schlechtes Gewissen.",
        "Work-Life-Balance hängt stark vom Projekt und Team ab.",
        "Überstunden fallen an, werden aber ausgeglichen oder bezahlt.",
        "In Stoßzeiten leidet die Balance, grundsätzlich aber vertretbar.",
        "32-Stunden-Woche als Option wäre wünschenswert.",
        "Sehr gute Balance durch klare Trennung von Arbeitszeit und Freizeit.",
        "Keine Erwartung, abends oder am Wochenende erreichbar zu sein.",
        "Teilzeit ist problemlos möglich und wird unterstützt.",
    ],
    "karriere_weiterbildung": [
        "Regelmäßige Schulungen und externe Konferenzen werden finanziert.",
        "Klarer Karrierepfad mit definierten Zwischenzielen.",
        "Interne Beförderungen werden bevorzugt – das ist motivierend.",
        "Weiterbildungsbudget vorhanden, aber manchmal schwer freizubekommen.",
        "Zertifizierungen werden unterstützt und honoriert.",
        "Karrieregespräche finden statt, könnten aber strukturierter sein.",
        "Aufstiegsmöglichkeiten hängen von Unternehmenswachstum ab.",
        "Zugang zu Online-Lernplattformen wie Udemy und LinkedIn Learning.",
        "Mentoring durch erfahrene Kollegen wird aktiv gefördert.",
    ],
    "gehalt_sozialleistungen": [
        "Gehalt entspricht dem Marktdurchschnitt, Boni sind fair kalkuliert.",
        "Betriebliche Altersvorsorge, Jobticket und Essenszuschuss als gute Extras.",
        "Gehaltserhöhungen sind möglich, erfordern aber Eigeninitiative.",
        "Transparente Vergütungsstruktur nach internen Bändern.",
        "Gehalt liegt leicht unter Großkonzernen, wird durch Benefits ausgeglichen.",
        "Jahresbonus abhängig von Unternehmens- und Individualziel.",
        "Gute Sozialleistungen, inkl. privater Krankenversicherungszuschuss.",
        "Gehaltsverhandlung wird ernst genommen und fair geführt.",
    ],
    "kollegenzusammenhalt": [
        "Starker Zusammenhalt im Team – man unterstützt sich gegenseitig.",
        "Teamevents und gemeinsame Aktivitäten stärken das Miteinander.",
        "Neuen Kollegen wird geholfen, schnell anzukommen.",
        "Informeller Austausch über Kaffeepause und Slack hält das Team verbunden.",
        "Auch remote bleibt der Zusammenhalt durch regelmäßige Video-Calls gut.",
        "Kleine Reibungen gibt es immer, aber keine toxische Dynamik.",
        "Offene Türen – auch Führungskräfte sind ansprechbar.",
        "Vertrauen ist die Basis, auf der alles aufbaut.",
    ],
    "umwelt_sozialbewusstsein": [
        "Nachhaltigkeitsziele sind Teil der Unternehmensstrategie und werden gemessen.",
        "Papierloses Büro und CO2-Kompensation für Dienstreisen.",
        "Soziales Engagement durch Freiwilligentage und Spendenaktionen.",
        "Energieeffizienz und erneuerbare Energien im Bürobetrieb.",
        "Umweltbewusstsein vorhanden, könnte in der Produktion stärker sein.",
        "Fahrradleasing und ÖPNV-Ticket zeigen ökologisches Bewusstsein.",
        "Kooperation mit lokalen sozialen Einrichtungen.",
    ],
    "vorgesetztenverhalten": [
        "Vorgesetzte führen auf Augenhöhe und geben konstruktives Feedback.",
        "Vertrauen in die Selbstständigkeit der Mitarbeiter wird vorgelebt.",
        "Regelmäßige 1:1s und Jahresgespräche strukturieren die Zusammenarbeit.",
        "Lob wird ausgesprochen, Kritik konstruktiv formuliert.",
        "Klare Zielvereinbarungen schaffen Orientierung.",
        "Manchmal fehlt es an Klarheit bei strategischen Entscheidungen.",
        "Offene Tür-Politik wird wirklich gelebt.",
        "Führungskräfte sind berechenbar und verlässlich.",
        "Coaching-Ansatz statt Mikromanagement.",
    ],
    "kommunikation": [
        "Transparente Kommunikation aus dem Management über Unternehmensziele.",
        "Wöchentliche Team-Standups halten alle auf dem Laufenden.",
        "Slack und Confluence als Kommunikations-Tools funktionieren gut.",
        "Manchmal kommen Entscheidungen ohne ausreichende Vorankündigung.",
        "Regelmäßige Newsletter und All-Hands helfen bei der Einordnung.",
        "Direkte Ansprache von Problemen wird erwartet und geschätzt.",
        "Kommunikation zwischen Abteilungen könnte verbessert werden.",
        "Feedback-Kanal für Ideen und Verbesserungen ist vorhanden.",
    ],
    "interessante_aufgaben": [
        "Abwechslungsreiche Projekte mit echtem Business-Impact.",
        "Technisch herausfordernde Aufgaben, die Wachstum fördern.",
        "Man kann eigene Ideen einbringen und umsetzen.",
        "Ownership über eigene Produkte und Features.",
        "Gelegentlich Routineaufgaben, aber der Großteil ist spannend.",
        "Interdisziplinäre Projekte fördern breit gefächertes Lernen.",
        "Innovationszeit für eigene Projekte ist gelegentlich möglich.",
        "Kundenkontakt macht die Arbeit greifbar und sinnvoll.",
    ],
    "umgang_mit_aelteren_kollegen": [
        "Erfahrene Kollegen werden respektiert und ihre Expertise genutzt.",
        "Generationenübergreifendes Arbeiten funktioniert sehr gut.",
        "Ältere Kollegen werden bei Restrukturierungen fair behandelt.",
        "Wissenstransfer zwischen Jung und Alt ist strukturiert.",
        "Keine Diskriminierung aufgrund von Alter wahrnehmbar.",
        "Teilzeitmodelle für ältere Kollegen vorhanden.",
        "Kompetenzen zählen, nicht das Alter.",
    ],
    "arbeitsbedingungen": [
        "Ergonomische Arbeitsplätze mit höhenverstellbaren Schreibtischen.",
        "Moderne Hardware – jährliche Geräteerneuerung.",
        "Ruhige Arbeitsbereiche neben offenen Kollaborationszonen.",
        "Gute Belüftung und Beleuchtung im Büro.",
        "Parkplätze begrenzt, ÖPNV-Anbindung aber gut.",
        "Klimaanlage im Sommer gelegentlich Diskussionsthema.",
        "Home-Office-Ausstattung wird vom Unternehmen bereitgestellt.",
        "Saubere Küche und Gemeinschaftsbereiche.",
    ],
    "gleichberechtigung": [
        "Diversity und Inklusion sind keine Floskeln – es gibt messbare Ziele.",
        "Frauen in Führungspositionen sind sichtbar und werden gefördert.",
        "Gehaltsgleichheit wird aktiv überprüft und sichergestellt.",
        "Internationales Team mit gelebter Vielfalt.",
        "LGBTQ+-freundliche Unternehmenskultur.",
        "Gleichbehandlung unabhängig von Herkunft und Hintergrund.",
        "Barrierefreiheit im Büro ist gegeben.",
        "Mutterschutz und Elternzeit ohne Karrierenachteile.",
    ],
}

_JOB_TITLES = [
    "Software Engineer", "Senior Software Engineer", "Product Manager",
    "Data Scientist", "DevOps Engineer", "UX Designer", "Marketing Manager",
    "Vertriebsleiter", "HR Business Partner", "Finance Analyst",
    "Scrum Master", "Technical Lead", "Projektmanager", "Kundenberater",
    "Business Analyst", "Backend Developer", "Frontend Developer",
    "QA Engineer", "IT-Systemadministrator", "Sales Manager",
    "Content Manager", "Recruiter", "Operations Manager", "Controller",
]

_CANDIDATE_TITEL_POOL = [
    "Bewerbungsprozess für Junior Developer", "Interview als Product Manager",
    "Vorstellungsgespräch für Data Scientist", "Assessment Center Erfahrung",
    "Telefon-Interview für UX Designer", "Mehrstufiger Auswahlprozess",
    "Praktikumsbewerbung – sehr professionell", "Werkstudentenstelle Bewerbung",
    "Erfahrung als externer Bewerber", "Online-Assessment sehr strukturiert",
    "Video-Interview für Remote-Stelle", "Bewerbung für Führungsposition",
    "Schneller und effizienter Prozess", "Detaillierter technischer Test",
    "Persönliches Gespräch sehr angenehm", "Transparenter Bewerbungsprozess",
    "HR war sehr kommunikativ", "Feedback nach Absage sehr wertvoll",
]

_STELLENBESCHREIBUNG_POOL = [
    "Ich habe mich für eine Stelle als Software Engineer beworben. Der Prozess war gut strukturiert.",
    "Die Bewerbung lief über zwei Runden: HR-Interview und technisches Gespräch.",
    "Ein Assessment Center mit Gruppenaufgaben und Einzelinterviews wurde durchgeführt.",
    "Der gesamte Prozess dauerte etwa vier Wochen von Bewerbung bis Entscheidung.",
    "Erstes Kennenlernen per Telefon, danach persönliches Gespräch vor Ort.",
    "Der Prozess umfasste einen Online-Test, zwei Interviews und eine Fallstudie.",
    "Bewerbung für eine Werkstudentenstelle im Bereich Marketing.",
    "Praktikumsstelle im Bereich Data Science – moderner Bewerbungsprozess.",
    "Fachinterview mit zukünftigem Team und HR-Gespräch liefen parallel.",
    "Video-Interview war gut vorbereitet, technische Fragen waren angemessen.",
]

_CANDIDATE_VERBESSERUNG_POOL = [
    "Schnelleres Feedback nach den Gesprächen wäre wünschenswert.",
    "Die Zeitplanung könnte transparenter kommuniziert werden.",
    "Mehr Informationen über die Unternehmenskultur vorab wären hilfreich.",
    "Ein Feedback nach Ablehnung würde sehr helfen.",
    "Die technische Aufgabe war etwas zu zeitaufwändig für eine unbezahlte Übung.",
    "Klare Kommunikation über die nächsten Schritte fehlt manchmal.",
    "Mehrere Gesprächsrunden könnten auf eine reduziert werden.",
    "Bessere Erreichbarkeit der HR-Abteilung per Telefon.",
    "Gehaltsvorstellungen früher im Prozess besprechen.",
    "Mehr Einblick in den Arbeitsalltag, z.B. durch Schnuppertag.",
]

_STATUS_EMPLOYEE = ["Angestellt", "Ex-Angestellt", "Angestellt", "Angestellt", "Ex-Angestellt"]
_STATUS_CANDIDATE = ["Bewerber", "Bewerber", "Bewerber"]

_EMPLOYEE_CATS = [
    "arbeitsatmosphaere", "image", "work_life_balance", "karriere_weiterbildung",
    "gehalt_sozialleistungen", "kollegenzusammenhalt", "umwelt_sozialbewusstsein",
    "vorgesetztenverhalten", "kommunikation", "interessante_aufgaben",
    "umgang_mit_aelteren_kollegen", "arbeitsbedingungen", "gleichberechtigung",
]

_CANDIDATE_CATS = [
    "erklaerung_der_weiteren_schritte", "zufriedenstellende_reaktion",
    "vollstaendigkeit_der_infos", "zufriedenstellende_antworten",
    "angenehme_atmosphaere", "professionalitaet_des_gespraechs",
    "wertschaetzende_behandlung", "erwartbarkeit_des_prozesses",
    "zeitgerechte_zu_oder_absage", "schnelle_antwort",
]

# Demo 1: steigender Trend, stark in Atmosphäre & Zusammenhalt
_CAT_OFFSETS_D1 = {
    "arbeitsatmosphaere": +0.3, "image": 0.0, "work_life_balance": -0.2,
    "karriere_weiterbildung": -0.1, "gehalt_sozialleistungen": -0.3,
    "kollegenzusammenhalt": +0.4, "umwelt_sozialbewusstsein": +0.1,
    "vorgesetztenverhalten": -0.1, "kommunikation": -0.2,
    "interessante_aufgaben": +0.2, "umgang_mit_aelteren_kollegen": +0.1,
    "arbeitsbedingungen": 0.0, "gleichberechtigung": +0.2,
}

# Demo 2: sinkender Trend, stark in Work-Life-Balance & Arbeitsbedingungen,
#          schwach in Kommunikation, Karriere & Führung
_CAT_OFFSETS_D2 = {
    "arbeitsatmosphaere": -0.1, "image": +0.2, "work_life_balance": +0.4,
    "karriere_weiterbildung": -0.5, "gehalt_sozialleistungen": -0.4,
    "kollegenzusammenhalt": +0.1, "umwelt_sozialbewusstsein": +0.3,
    "vorgesetztenverhalten": -0.3, "kommunikation": -0.5,
    "interessante_aufgaben": -0.1, "umgang_mit_aelteren_kollegen": +0.2,
    "arbeitsbedingungen": +0.3, "gleichberechtigung": +0.1,
}

_CAT_OFFSETS = _CAT_OFFSETS_D1  # kept for backwards compat

_CAND_OFFSETS_D1 = {
    "erklaerung_der_weiteren_schritte": 0.0, "zufriedenstellende_reaktion": +0.1,
    "vollstaendigkeit_der_infos": -0.1, "zufriedenstellende_antworten": 0.0,
    "angenehme_atmosphaere": +0.3, "professionalitaet_des_gespraechs": +0.2,
    "wertschaetzende_behandlung": +0.2, "erwartbarkeit_des_prozesses": -0.2,
    "zeitgerechte_zu_oder_absage": -0.1, "schnelle_antwort": 0.0,
}

# Demo 2 Kandidaten: schwächerer Prozess, weniger Transparenz
_CAND_OFFSETS_D2 = {
    "erklaerung_der_weiteren_schritte": -0.3, "zufriedenstellende_reaktion": -0.2,
    "vollstaendigkeit_der_infos": -0.3, "zufriedenstellende_antworten": -0.1,
    "angenehme_atmosphaere": +0.1, "professionalitaet_des_gespraechs": 0.0,
    "wertschaetzende_behandlung": +0.1, "erwartbarkeit_des_prozesses": -0.4,
    "zeitgerechte_zu_oder_absage": -0.4, "schnelle_antwort": -0.3,
}

_CAND_OFFSETS = _CAND_OFFSETS_D1  # kept for backwards compat

# Bulk balanced: alle Kategorien leicht positiv, gut bis akzeptabel
_BALANCED_OFFSETS = {
    "arbeitsatmosphaere": +0.1, "image": +0.1, "work_life_balance": +0.1,
    "karriere_weiterbildung": 0.0, "gehalt_sozialleistungen": 0.0,
    "kollegenzusammenhalt": +0.1, "umwelt_sozialbewusstsein": +0.1,
    "vorgesetztenverhalten": 0.0, "kommunikation": 0.0,
    "interessante_aufgaben": +0.1, "umgang_mit_aelteren_kollegen": 0.0,
    "arbeitsbedingungen": +0.1, "gleichberechtigung": +0.1,
}

_BALANCED_CAND_OFFSETS = {
    "erklaerung_der_weiteren_schritte": +0.1, "zufriedenstellende_reaktion": +0.1,
    "vollstaendigkeit_der_infos": 0.0, "zufriedenstellende_antworten": +0.1,
    "angenehme_atmosphaere": +0.2, "professionalitaet_des_gespraechs": +0.1,
    "wertschaetzende_behandlung": +0.1, "erwartbarkeit_des_prozesses": 0.0,
    "zeitgerechte_zu_oder_absage": 0.0, "schnelle_antwort": +0.1,
}


def _make_employee(company_id: int, period: str, eid: int, offsets: dict = None, ranges: dict = None) -> dict:
    if offsets is None:
        offsets = _CAT_OFFSETS_D1
    if ranges is None:
        ranges = {"early": (2.8, 3.5), "mid": (3.2, 3.9), "late": (3.6, 4.5)}

    lo, hi = ranges[period]
    base = random.uniform(lo, hi)
    if period == "early":
        date = _date_between(_START, datetime(2022, 12, 31))
    elif period == "mid":
        date = _date_between(datetime(2023, 1, 1), datetime(2023, 12, 31))
    else:
        date = _date_between(datetime(2024, 1, 1), _END)

    cats = {cat: _rand_rating(base + offsets[cat]) for cat in _EMPLOYEE_CATS}
    avg = round(sum(cats.values()) / len(cats), 2)

    row: dict = {
        "id": eid,
        "company_id": company_id,
        "titel": random.choice(_JOB_TITLES),
        "status": random.choice(_STATUS_EMPLOYEE),
        "datum": date,
        "durchschnittsbewertung": avg,
        "gerundete_durchschnittsbewertung": round(round(avg * 2) / 2, 1),
        "jobbeschreibung": random.choice(_JOB_TITLES) + " im Bereich Produktentwicklung.",
        "gut_am_arbeitgeber_finde_ich": random.choice(_GUT_POOL),
        "schlecht_am_arbeitgeber_finde_ich": random.choice(_SCHLECHT_POOL),
        "verbesserungsvorschlaege": random.choice(_VERBESSERUNG_POOL),
    }
    for cat in _EMPLOYEE_CATS:
        row[f"sternebewertung_{cat}"] = cats[cat]
        row[cat] = random.choice(_TOPIC_TEXTS[cat])
    return row


def _make_candidate(company_id: int, period: str, cid: int, offsets: dict = None, ranges: dict = None) -> dict:
    if offsets is None:
        offsets = _CAND_OFFSETS_D1
    if ranges is None:
        ranges = {"early": (2.9, 3.6), "mid": (3.3, 4.0), "late": (3.7, 4.6)}

    lo, hi = ranges[period]
    base = random.uniform(lo, hi)
    if period == "early":
        date = _date_between(_START, datetime(2022, 12, 31))
    elif period == "mid":
        date = _date_between(datetime(2023, 1, 1), datetime(2023, 12, 31))
    else:
        date = _date_between(datetime(2024, 1, 1), _END)

    cats = {cat: _rand_rating(base + offsets[cat]) for cat in _CANDIDATE_CATS}
    avg = round(sum(cats.values()) / len(cats), 2)

    row: dict = {
        "id": cid,
        "company_id": company_id,
        "titel": random.choice(_CANDIDATE_TITEL_POOL),
        "status": random.choice(_STATUS_CANDIDATE),
        "datum": date,
        "durchschnittsbewertung": avg,
        "gerundete_durchschnittsbewertung": round(round(avg * 2) / 2, 1),
        "stellenbeschreibung": random.choice(_STELLENBESCHREIBUNG_POOL),
        "verbesserungsvorschlaege": random.choice(_CANDIDATE_VERBESSERUNG_POOL),
    }
    for cat in _CANDIDATE_CATS:
        row[f"sternebewertung_{cat}"] = cats[cat]
    return row


_D2_EMP_RANGES  = {"early": (4.0, 4.8), "mid": (3.3, 4.2), "late": (2.5, 3.5)}
_D2_CAND_RANGES = {"early": (3.8, 4.6), "mid": (3.1, 4.0), "late": (2.4, 3.3)}

# Demo 3: V-Form — Einbruch 2023 (Restrukturierung), danach Erholung
# Stark in: Gleichberechtigung, Umwelt, Arbeitsbedingungen
# Schwach während Krise: Kommunikation, Vorgesetztenverhalten, Atmosphäre
_CAT_OFFSETS_D3 = {
    "arbeitsatmosphaere": -0.1, "image": +0.1, "work_life_balance": 0.0,
    "karriere_weiterbildung": +0.1, "gehalt_sozialleistungen": 0.0,
    "kollegenzusammenhalt": +0.2, "umwelt_sozialbewusstsein": +0.3,
    "vorgesetztenverhalten": -0.2, "kommunikation": -0.3,
    "interessante_aufgaben": +0.2, "umgang_mit_aelteren_kollegen": +0.1,
    "arbeitsbedingungen": +0.2, "gleichberechtigung": +0.3,
}

_CAND_OFFSETS_D3 = {
    "erklaerung_der_weiteren_schritte": -0.1, "zufriedenstellende_reaktion": 0.0,
    "vollstaendigkeit_der_infos": -0.1, "zufriedenstellende_antworten": +0.1,
    "angenehme_atmosphaere": +0.2, "professionalitaet_des_gespraechs": +0.1,
    "wertschaetzende_behandlung": +0.2, "erwartbarkeit_des_prozesses": -0.2,
    "zeitgerechte_zu_oder_absage": -0.1, "schnelle_antwort": 0.0,
}

# V-Form: früh gut → Krise mitte → Erholung spät
_D3_EMP_RANGES  = {"early": (3.8, 4.4), "mid": (2.3, 3.1), "late": (3.5, 4.3)}
_D3_CAND_RANGES = {"early": (3.6, 4.2), "mid": (2.2, 3.0), "late": (3.4, 4.1)}


def _generate_data():
    companies = [
        {"id": 1, "name": "Demo 1", "ticker": "DEMO1.DE", "isin": "DE000DEMO101"},
        {"id": 2, "name": "Demo 2", "ticker": "DEMO2.DE", "isin": "DE000DEMO202"},
        {"id": 3, "name": "Demo 3", "ticker": "DEMO3.DE", "isin": "DE000DEMO303"},
    ]
    employees = []
    candidates = []

    # Demo 1: steigender Trend
    eid = 1
    for period, count in [("early", 40), ("mid", 50), ("late", 60)]:
        for _ in range(count):
            employees.append(_make_employee(1, period, eid, _CAT_OFFSETS_D1))
            eid += 1

    # Demo 2: sinkender Trend
    for period, count in [("early", 45), ("mid", 55), ("late", 50)]:
        for _ in range(count):
            employees.append(_make_employee(2, period, eid, _CAT_OFFSETS_D2, _D2_EMP_RANGES))
            eid += 1

    # Demo 3: V-Form (Krise 2023, Erholung 2024+)
    for period, count in [("early", 40), ("mid", 60), ("late", 50)]:
        for _ in range(count):
            employees.append(_make_employee(3, period, eid, _CAT_OFFSETS_D3, _D3_EMP_RANGES))
            eid += 1

    # Demo 1 candidates
    cid = 1
    for period, count in [("early", 20), ("mid", 25), ("late", 30)]:
        for _ in range(count):
            candidates.append(_make_candidate(1, period, cid, _CAND_OFFSETS_D1))
            cid += 1

    # Demo 2 candidates
    for period, count in [("early", 22), ("mid", 28), ("late", 25)]:
        for _ in range(count):
            candidates.append(_make_candidate(2, period, cid, _CAND_OFFSETS_D2, _D2_CAND_RANGES))
            cid += 1

    # Demo 3 candidates
    for period, count in [("early", 18), ("mid", 30), ("late", 22)]:
        for _ in range(count):
            candidates.append(_make_candidate(3, period, cid, _CAND_OFFSETS_D3, _D3_CAND_RANGES))
            cid += 1

    # ── Bulk balanced reviews (500 Mitarbeiter + 150 Bewerber pro Firma) ────
    for company_id in [1, 2, 3]:
        for _ in range(500):
            base = random.uniform(3.2, 4.5)
            cats = {cat: _rand_rating(base + _BALANCED_OFFSETS[cat]) for cat in _EMPLOYEE_CATS}
            avg = round(sum(cats.values()) / len(cats), 2)
            row: dict = {
                "id": eid, "company_id": company_id,
                "titel": random.choice(_JOB_TITLES),
                "status": random.choice(_STATUS_EMPLOYEE),
                "datum": _date_between(_START, _END),
                "durchschnittsbewertung": avg,
                "gerundete_durchschnittsbewertung": round(round(avg * 2) / 2, 1),
                "jobbeschreibung": random.choice(_JOB_TITLES) + " in der Produktentwicklung.",
                "gut_am_arbeitgeber_finde_ich": random.choice(_GUT_POOL),
                "schlecht_am_arbeitgeber_finde_ich": random.choice(_SCHLECHT_POOL),
                "verbesserungsvorschlaege": random.choice(_VERBESSERUNG_POOL),
            }
            for cat in _EMPLOYEE_CATS:
                row[f"sternebewertung_{cat}"] = cats[cat]
                row[cat] = random.choice(_TOPIC_TEXTS[cat])
            employees.append(row)
            eid += 1

        for _ in range(150):
            base = random.uniform(3.3, 4.5)
            cats = {cat: _rand_rating(base + _BALANCED_CAND_OFFSETS[cat]) for cat in _CANDIDATE_CATS}
            avg = round(sum(cats.values()) / len(cats), 2)
            row = {
                "id": cid, "company_id": company_id,
                "titel": random.choice(_CANDIDATE_TITEL_POOL),
                "status": random.choice(_STATUS_CANDIDATE),
                "datum": _date_between(_START, _END),
                "durchschnittsbewertung": avg,
                "gerundete_durchschnittsbewertung": round(round(avg * 2) / 2, 1),
                "stellenbeschreibung": random.choice(_STELLENBESCHREIBUNG_POOL),
                "verbesserungsvorschlaege": random.choice(_CANDIDATE_VERBESSERUNG_POOL),
            }
            for cat in _CANDIDATE_CATS:
                row[f"sternebewertung_{cat}"] = cats[cat]
            candidates.append(row)
            cid += 1

    return companies, employees, candidates


_COMPANIES, _EMPLOYEES, _CANDIDATES = _generate_data()

# ---------------------------------------------------------------------------
# Demo-Kontextdaten (2. Design-Zyklus): externe Ereignisse, Kurse, Kennzahlen
# Abgestimmt auf die Bewertungsverläufe: Demo 1 steigend, Demo 2 sinkend,
# Demo 3 V-Form (Krise ab Anfang 2023, Erholung ab Anfang 2024).
# ---------------------------------------------------------------------------

_DEMO_CONTEXT_ITEMS = [
    # Demo 3: Krise + Erholung
    {"id": 1, "company_id": 3, "source_type": "adhoc", "provider": "manual",
     "titel": "Demo 3 AG kündigt umfassendes Restrukturierungsprogramm an",
     "zusammenfassung": "Der Vorstand beschließt ein Sparprogramm: Stellenabbau von rund 800 Stellen und die Schließung des Standorts Nord sind geplant.",
     "url": "https://example.com/demo3/adhoc-restrukturierung",
     "published_at": "2023-01-12T08:00:00+00:00", "raw": None},
    {"id": 2, "company_id": 3, "source_type": "news", "provider": "manual",
     "titel": "Stellenabbau bei Demo 3: 800 Stellen betroffen",
     "zusammenfassung": "Das Unternehmen reagiert mit Entlassungen und Kurzarbeit auf den anhaltenden Umsatzrückgang. Die Belegschaft reagiert verunsichert.",
     "url": "https://example.com/demo3/news-stellenabbau",
     "published_at": "2023-02-03T10:30:00+00:00", "raw": None},
    {"id": 3, "company_id": 3, "source_type": "news", "provider": "manual",
     "titel": "Gewinnwarnung: Demo 3 senkt Prognose für 2023",
     "zusammenfassung": "Nach einem schwachen zweiten Quartal senkt Demo 3 die Umsatz- und Ergebnisprognose deutlich.",
     "url": "https://example.com/demo3/news-gewinnwarnung",
     "published_at": "2023-06-20T07:15:00+00:00", "raw": None},
    {"id": 4, "company_id": 3, "source_type": "adhoc", "provider": "manual",
     "titel": "Demo 3 AG: Vorstandsvorsitzender verlässt das Unternehmen",
     "zusammenfassung": "Der CEO legt sein Amt zum Jahresende nieder. Der Aufsichtsrat hat die Nachfolge eingeleitet.",
     "url": "https://example.com/demo3/adhoc-ceo-wechsel",
     "published_at": "2023-11-10T18:00:00+00:00", "raw": None},
    {"id": 5, "company_id": 3, "source_type": "news", "provider": "manual",
     "titel": "Führungswechsel bei Demo 3: Neuer CEO übernimmt",
     "zusammenfassung": "Der neue Vorstandsvorsitzende kündigt einen Kulturwandel und mehr interne Kommunikation an.",
     "url": "https://example.com/demo3/news-neuer-ceo",
     "published_at": "2023-12-05T09:00:00+00:00", "raw": None},
    {"id": 6, "company_id": 3, "source_type": "news", "provider": "manual",
     "titel": "Demo 3 kehrt in die Gewinnzone zurück",
     "zusammenfassung": "Rekordauftragseingang und erfolgreiche Expansion: Demo 3 plant Neueinstellungen und investiert in Weiterbildung.",
     "url": "https://example.com/demo3/news-gewinnzone",
     "published_at": "2024-02-08T08:45:00+00:00", "raw": None},
    {"id": 7, "company_id": 3, "source_type": "news", "provider": "manual",
     "titel": "Demo 3 startet Neueinstellungsprogramm",
     "zusammenfassung": "Nach der Restrukturierung wächst Demo 3 wieder: 300 neue Stellen in Entwicklung und Vertrieb.",
     "url": "https://example.com/demo3/news-neueinstellungen",
     "published_at": "2024-03-15T11:00:00+00:00", "raw": None},
    {"id": 8, "company_id": 3, "source_type": "news", "provider": "manual",
     "titel": "Tarifabschluss: Gehaltserhöhung für Demo-3-Beschäftigte",
     "zusammenfassung": "Nach Warnstreiks einigen sich Tarifparteien auf eine Gehaltserhöhung von 5,2 Prozent und einen Bonus.",
     "url": "https://example.com/demo3/news-tarifabschluss",
     "published_at": "2024-06-01T14:00:00+00:00", "raw": None},
    # Demo 1: positiver Verlauf
    {"id": 9, "company_id": 1, "source_type": "news", "provider": "manual",
     "titel": "Demo 1 eröffnet neuen Standort und stellt ein",
     "zusammenfassung": "Expansion: Demo 1 wächst und sucht 150 neue Mitarbeitende.",
     "url": "https://example.com/demo1/news-expansion",
     "published_at": "2023-05-10T09:00:00+00:00", "raw": None},
    {"id": 10, "company_id": 1, "source_type": "news", "provider": "manual",
     "titel": "Demo 1 erweitert Homeoffice-Regelung dauerhaft",
     "zusammenfassung": "Mitarbeitende können künftig bis zu vier Tage pro Woche remote arbeiten.",
     "url": "https://example.com/demo1/news-homeoffice",
     "published_at": "2024-01-20T08:00:00+00:00", "raw": None},
    # Demo 2: negativer Verlauf
    {"id": 11, "company_id": 2, "source_type": "adhoc", "provider": "manual",
     "titel": "Demo 2 AG: Umsatzrückgang im dritten Quartal",
     "zusammenfassung": "Der Umsatz sinkt um 12 Prozent, das Unternehmen prüft ein Sparprogramm.",
     "url": "https://example.com/demo2/adhoc-umsatzrueckgang",
     "published_at": "2023-10-12T17:30:00+00:00", "raw": None},
    {"id": 12, "company_id": 2, "source_type": "news", "provider": "manual",
     "titel": "Demo 2 kündigt Sparprogramm und Stellenabbau an",
     "zusammenfassung": "Restrukturierung: Bis zu 400 Stellen sollen sozialverträglich abgebaut werden.",
     "url": "https://example.com/demo2/news-sparprogramm",
     "published_at": "2023-11-02T10:00:00+00:00", "raw": None},
]


def _interp_monthly(anchors: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Lineare Interpolation zwischen (YYYY-MM, Preis)-Ankern, ein Wert je Monat."""
    def to_idx(period: str) -> int:
        y, m = period.split("-")
        return int(y) * 12 + int(m) - 1

    out: list[tuple[str, float]] = []
    for (p0, v0), (p1, v1) in zip(anchors, anchors[1:]):
        i0, i1 = to_idx(p0), to_idx(p1)
        for i in range(i0, i1):
            frac = (i - i0) / (i1 - i0)
            y, m = divmod(i, 12)
            out.append((f"{y:04d}-{m + 1:02d}", v0 + (v1 - v0) * frac))
    last_p, last_v = anchors[-1]
    out.append((last_p, last_v))
    return out


def _make_stock_prices() -> list[dict]:
    anchors_by_company = {
        # Demo 1: milder Aufwärtstrend
        1: [("2022-01", 31.0), ("2023-01", 34.0), ("2024-01", 38.5), ("2025-04", 44.0)],
        # Demo 2: Abwärtstrend
        2: [("2022-01", 52.0), ("2023-01", 47.0), ("2024-01", 38.0), ("2025-04", 31.5)],
        # Demo 3: V-Form — Einbruch ab Anfang 2023, Erholung ab 2024
        3: [("2022-01", 48.0), ("2022-12", 45.0), ("2023-07", 27.0),
            ("2023-12", 28.5), ("2024-12", 41.0), ("2025-04", 43.0)],
    }
    rows: list[dict] = []
    sid = 1
    for company_id, anchors in anchors_by_company.items():
        for period, value in _interp_monthly(anchors):
            for day, wiggle in (("01", -0.4), ("15", +0.4)):
                rows.append({
                    "id": sid,
                    "company_id": company_id,
                    "date": f"{period}-{day}",
                    "close": round(value + wiggle, 2),
                    "volume": 120_000 + (sid % 7) * 15_000,
                    "currency": "EUR",
                })
                sid += 1
    return rows


_DEMO_STOCK_PRICES = _make_stock_prices()

# Analystenempfehlungen (Monatsverteilung, Stil Yahoo Finance)
_DEMO_ANALYST_RECOMMENDATIONS = [
    # Demo 1: überwiegend Buy, stabil
    {"id": 1, "company_id": 1, "month": "2026-04", "strong_buy": 6, "buy": 11, "hold": 5, "sell": 1, "strong_sell": 0, "fetched_at": "2026-07-01T00:00:00+00:00"},
    {"id": 2, "company_id": 1, "month": "2026-05", "strong_buy": 7, "buy": 11, "hold": 4, "sell": 1, "strong_sell": 0, "fetched_at": "2026-07-01T00:00:00+00:00"},
    {"id": 3, "company_id": 1, "month": "2026-06", "strong_buy": 7, "buy": 12, "hold": 4, "sell": 0, "strong_sell": 0, "fetched_at": "2026-07-01T00:00:00+00:00"},
    {"id": 4, "company_id": 1, "month": "2026-07", "strong_buy": 8, "buy": 12, "hold": 3, "sell": 0, "strong_sell": 0, "fetched_at": "2026-07-01T00:00:00+00:00"},
    # Demo 2: kippt Richtung Hold/Sell
    {"id": 5, "company_id": 2, "month": "2026-04", "strong_buy": 2, "buy": 6, "hold": 10, "sell": 3, "strong_sell": 1, "fetched_at": "2026-07-01T00:00:00+00:00"},
    {"id": 6, "company_id": 2, "month": "2026-05", "strong_buy": 1, "buy": 5, "hold": 11, "sell": 4, "strong_sell": 1, "fetched_at": "2026-07-01T00:00:00+00:00"},
    {"id": 7, "company_id": 2, "month": "2026-06", "strong_buy": 1, "buy": 4, "hold": 11, "sell": 5, "strong_sell": 2, "fetched_at": "2026-07-01T00:00:00+00:00"},
    {"id": 8, "company_id": 2, "month": "2026-07", "strong_buy": 1, "buy": 4, "hold": 10, "sell": 6, "strong_sell": 2, "fetched_at": "2026-07-01T00:00:00+00:00"},
    # Demo 3: Erholung — von Hold zu Buy drehend
    {"id": 9, "company_id": 3, "month": "2026-04", "strong_buy": 3, "buy": 8, "hold": 9, "sell": 2, "strong_sell": 0, "fetched_at": "2026-07-01T00:00:00+00:00"},
    {"id": 10, "company_id": 3, "month": "2026-05", "strong_buy": 4, "buy": 9, "hold": 8, "sell": 1, "strong_sell": 0, "fetched_at": "2026-07-01T00:00:00+00:00"},
    {"id": 11, "company_id": 3, "month": "2026-06", "strong_buy": 5, "buy": 10, "hold": 7, "sell": 1, "strong_sell": 0, "fetched_at": "2026-07-01T00:00:00+00:00"},
    {"id": 12, "company_id": 3, "month": "2026-07", "strong_buy": 6, "buy": 11, "hold": 6, "sell": 0, "strong_sell": 0, "fetched_at": "2026-07-01T00:00:00+00:00"},
]

_DEMO_FINANCIAL_KPIS = [
    {"id": 1, "company_id": 1, "ticker": "DEMO1.DE", "market_cap": 2_400_000_000,
     "trailing_pe": 21.5, "revenue": 1_900_000_000, "employees": 8_500,
     "dividend_yield": 0.018, "profit_margin": 0.071, "currency": "EUR",
     "raw": None, "fetched_at": "2026-07-01T00:00:00+00:00"},
    {"id": 2, "company_id": 2, "ticker": "DEMO2.DE", "market_cap": 1_100_000_000,
     "trailing_pe": 14.2, "revenue": 2_600_000_000, "employees": 12_500,
     "dividend_yield": 0.032, "profit_margin": 0.028, "currency": "EUR",
     "raw": None, "fetched_at": "2026-07-01T00:00:00+00:00"},
    {"id": 3, "company_id": 3, "ticker": "DEMO3.DE", "market_cap": 1_800_000_000,
     "trailing_pe": 17.8, "revenue": 3_100_000_000, "employees": 10_200,
     "dividend_yield": 0.0, "profit_margin": 0.041, "currency": "EUR",
     "raw": None, "fetched_at": "2026-07-01T00:00:00+00:00"},
]

_TABLES: dict[str, list] = {
    "companies": _COMPANIES,
    "employee": _EMPLOYEES,
    "candidates": _CANDIDATES,
    "items": [],
    "anomalies": [],
    "context_items": _DEMO_CONTEXT_ITEMS,
    "stock_prices": _DEMO_STOCK_PRICES,
    "financial_kpis": _DEMO_FINANCIAL_KPIS,
    "analyst_recommendations": _DEMO_ANALYST_RECOMMENDATIONS,
    "explanations": [],
}

# ---------------------------------------------------------------------------
# Supabase-compatible in-memory client
# ---------------------------------------------------------------------------

_EMPLOYEE_AVG_COLS = {
    "avg_arbeitsatmosphaere": "sternebewertung_arbeitsatmosphaere",
    "avg_image": "sternebewertung_image",
    "avg_work_life_balance": "sternebewertung_work_life_balance",
    "avg_karriere_weiterbildung": "sternebewertung_karriere_weiterbildung",
    "avg_gehalt_sozialleistungen": "sternebewertung_gehalt_sozialleistungen",
    "avg_kollegenzusammenhalt": "sternebewertung_kollegenzusammenhalt",
    "avg_umwelt_sozialbewusstsein": "sternebewertung_umwelt_sozialbewusstsein",
    "avg_vorgesetztenverhalten": "sternebewertung_vorgesetztenverhalten",
    "avg_kommunikation": "sternebewertung_kommunikation",
    "avg_interessante_aufgaben": "sternebewertung_interessante_aufgaben",
    "avg_umgang_aelteren_kollegen": "sternebewertung_umgang_mit_aelteren_kollegen",
    "avg_arbeitsbedingungen": "sternebewertung_arbeitsbedingungen",
    "avg_gleichberechtigung": "sternebewertung_gleichberechtigung",
}


class Response:
    def __init__(self, data: list, count: Optional[int] = None):
        self.data = data
        self.count = count if count is not None else len(data)


class _NotProxy:
    def __init__(self, qb: "QueryBuilder"):
        self._qb = qb

    def is_(self, col: str, val: Any) -> "QueryBuilder":
        if val is None:
            self._qb._rows = [r for r in self._qb._rows if r.get(col) is not None]
        else:
            self._qb._rows = [r for r in self._qb._rows if r.get(col) is not val]
        return self._qb


class QueryBuilder:
    def __init__(self, rows: list, table_name: str):
        self._store = rows                # Referenz auf die Tabelle (fuer Mutationen)
        self._rows = list(rows)           # gefilterte Sicht (geteilte Dict-Referenzen)
        self._table_name = table_name
        self._select_cols: Optional[list[str]] = None
        self._count_mode: Optional[str] = None
        self._insert_rows: Optional[list] = None
        self._upsert_rows: Optional[list] = None
        self._on_conflict: Optional[list[str]] = None
        self._update_data: Optional[dict] = None
        self._is_delete = False
        self._prelimit_count: Optional[int] = None  # PostgREST: count zaehlt VOR limit/range

    # ---- filtering ----

    def select(self, cols: str, count: Optional[str] = None) -> "QueryBuilder":
        self._count_mode = count
        if cols.strip() != "*":
            self._select_cols = [c.strip() for c in cols.split(",")]
        return self

    def eq(self, col: str, val: Any) -> "QueryBuilder":
        self._rows = [r for r in self._rows if r.get(col) == val]
        return self

    def gte(self, col: str, val: Any) -> "QueryBuilder":
        self._rows = [r for r in self._rows if r.get(col) is not None and str(r.get(col)) >= str(val)]
        return self

    def lte(self, col: str, val: Any) -> "QueryBuilder":
        self._rows = [r for r in self._rows if r.get(col) is not None and str(r.get(col)) <= str(val)]
        return self

    def lt(self, col: str, val: Any) -> "QueryBuilder":
        self._rows = [r for r in self._rows if r.get(col) is not None and str(r.get(col)) < str(val)]
        return self

    def gt(self, col: str, val: Any) -> "QueryBuilder":
        self._rows = [r for r in self._rows if r.get(col) is not None and str(r.get(col)) > str(val)]
        return self

    def ilike(self, col: str, pattern: str) -> "QueryBuilder":
        needle = pattern.lower().replace("%", "")
        self._rows = [r for r in self._rows if needle in str(r.get(col, "")).lower()]
        return self

    # ---- sorting / paging ----

    def order(self, col: str, desc: bool = False) -> "QueryBuilder":
        self._rows = sorted(
            self._rows,
            key=lambda r: (r.get(col) is None, r.get(col) or ""),
            reverse=desc,
        )
        return self

    def limit(self, n: int) -> "QueryBuilder":
        if self._prelimit_count is None:
            self._prelimit_count = len(self._rows)
        self._rows = self._rows[:n]
        return self

    def range(self, start: int, end: int) -> "QueryBuilder":
        if self._prelimit_count is None:
            self._prelimit_count = len(self._rows)
        self._rows = self._rows[start: end + 1]
        return self

    # ---- not_ proxy ----

    @property
    def not_(self) -> _NotProxy:
        return _NotProxy(self)

    # ---- mutations ----

    def insert(self, data: Any) -> "QueryBuilder":
        self._insert_rows = data if isinstance(data, list) else [data]
        return self

    def upsert(self, data: Any, on_conflict: Optional[str] = None) -> "QueryBuilder":
        self._upsert_rows = data if isinstance(data, list) else [data]
        self._on_conflict = (
            [c.strip() for c in on_conflict.split(",")] if on_conflict else ["id"]
        )
        return self

    def update(self, data: dict) -> "QueryBuilder":
        self._update_data = dict(data)
        return self

    def delete(self) -> "QueryBuilder":
        self._is_delete = True
        return self

    def _next_id(self) -> int:
        return max((int(r.get("id") or 0) for r in self._store), default=0) + 1

    # ---- terminal ----

    def execute(self) -> Response:
        if self._insert_rows is not None:
            inserted = []
            for row in self._insert_rows:
                new_row = dict(row)
                if new_row.get("id") is None:
                    new_row["id"] = self._next_id()
                self._store.append(new_row)
                inserted.append(new_row)
            return Response(inserted)

        if self._upsert_rows is not None:
            written = []
            for row in self._upsert_rows:
                match = next(
                    (r for r in self._store
                     if all(r.get(c) == row.get(c) for c in self._on_conflict)),
                    None,
                )
                if match is not None:
                    match.update(row)
                    written.append(match)
                else:
                    new_row = dict(row)
                    if new_row.get("id") is None:
                        new_row["id"] = self._next_id()
                    self._store.append(new_row)
                    written.append(new_row)
            return Response(written)

        if self._update_data is not None:
            for r in self._rows:
                r.update(self._update_data)
            return Response(self._rows)

        if self._is_delete:
            doomed = {id(r) for r in self._rows}
            self._store[:] = [r for r in self._store if id(r) not in doomed]
            return Response(self._rows)

        result = self._rows
        if self._select_cols:
            result = [{col: r.get(col) for col in self._select_cols} for r in result]

        if self._count_mode == "exact":
            total = self._prelimit_count if self._prelimit_count is not None else len(result)
            return Response(result, count=total)
        return Response(result)


class _RpcBuilder:
    def __init__(self, func: str, params: dict):
        self._func = func
        self._params = params

    def execute(self) -> Response:
        if self._func == "get_employee_ratings_avg":
            return self._employee_ratings_avg()
        if self._func == "get_employee_ratings_avg_range":
            return self._employee_ratings_avg_range()
        return Response([])

    def _employee_ratings_avg(self) -> Response:
        company_id = self._params.get("p_company_id")
        rows = [r for r in _EMPLOYEES if r.get("company_id") == company_id]
        result: dict = {}
        for avg_key, col in _EMPLOYEE_AVG_COLS.items():
            vals = [float(r[col]) for r in rows if r.get(col) is not None]
            result[avg_key] = round(sum(vals) / len(vals), 4) if vals else None
        return Response([result] if result else [])

    def _employee_ratings_avg_range(self) -> Response:
        company_id = self._params.get("p_company_id")
        p_from = str(self._params.get("p_from", ""))
        p_to = str(self._params.get("p_to", ""))
        rows = [
            r for r in _EMPLOYEES
            if r.get("company_id") == company_id
            and r.get("datum") is not None
            and (not p_from or str(r["datum"]) >= p_from[:10])
            and (not p_to or str(r["datum"]) < p_to[:10])
        ]
        result: dict = {}
        for avg_key, col in _EMPLOYEE_AVG_COLS.items():
            vals = [float(r[col]) for r in rows if r.get(col) is not None]
            result[avg_key] = round(sum(vals) / len(vals), 4) if vals else None
        return Response([result] if result else [])


class InMemoryClient:
    def table(self, name: str) -> QueryBuilder:
        rows = _TABLES.setdefault(name, [])
        return QueryBuilder(rows, name)

    def rpc(self, func: str, params: dict) -> _RpcBuilder:
        return _RpcBuilder(func, params)


_client = InMemoryClient()


def get_in_memory_client() -> InMemoryClient:
    return _client
