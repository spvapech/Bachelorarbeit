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
        {"id": 1, "name": "Demo 1"},
        {"id": 2, "name": "Demo 2"},
        {"id": 3, "name": "Demo 3"},
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

_TABLES: dict[str, list] = {
    "companies": _COMPANIES,
    "employee": _EMPLOYEES,
    "candidates": _CANDIDATES,
    "items": [],
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
        self._rows = list(rows)
        self._table_name = table_name
        self._select_cols: Optional[list[str]] = None
        self._count_mode: Optional[str] = None
        self._insert_rows: Optional[list] = None
        self._is_delete = False

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
        self._rows = self._rows[:n]
        return self

    def range(self, start: int, end: int) -> "QueryBuilder":
        self._rows = self._rows[start: end + 1]
        return self

    # ---- not_ proxy ----

    @property
    def not_(self) -> _NotProxy:
        return _NotProxy(self)

    # ---- mutations (no-op in demo mode) ----

    def insert(self, data: Any) -> "QueryBuilder":
        self._insert_rows = data if isinstance(data, list) else [data]
        return self

    def delete(self) -> "QueryBuilder":
        self._is_delete = True
        return self

    # ---- terminal ----

    def execute(self) -> Response:
        if self._insert_rows is not None:
            return Response([])
        if self._is_delete:
            return Response([])

        result = self._rows
        if self._select_cols:
            result = [{col: r.get(col) for col in self._select_cols} for r in result]

        if self._count_mode == "exact":
            return Response(result, count=len(result))
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
        rows = _TABLES.get(name, [])
        return QueryBuilder(rows, name)

    def rpc(self, func: str, params: dict) -> _RpcBuilder:
        return _RpcBuilder(func, params)


_client = InMemoryClient()


def get_in_memory_client() -> InMemoryClient:
    return _client
