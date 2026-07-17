"""
Seed script: Creates "Demo 1" company with comprehensive dummy data.
Run from the backend directory: python scripts/seed_demo1.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import get_supabase_client
from datetime import datetime, timedelta
import random

random.seed(42)
supabase = get_supabase_client()

COMPANY_NAME = "Demo 1"

# ── Helpers ──────────────────────────────────────────────────────────────────

def rand_rating(mu, sigma=0.6, lo=1.0, hi=5.0):
    v = random.gauss(mu, sigma)
    return round(max(lo, min(hi, v)), 2)

def date_between(start: datetime, end: datetime) -> str:
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.isoformat()

START = datetime(2022, 1, 1)
MID   = datetime(2023, 6, 1)
END   = datetime(2026, 5, 15)

# ── Employee text pools ───────────────────────────────────────────────────────

GUT_POOL = [
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

SCHLECHT_POOL = [
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
    "Hohe Fluktuation in manchen Abteilungen sorgt für Wissenverlust.",
    "Überstunden werden erwartet aber nicht immer transparent kommuniziert.",
    "Meeting-Kultur ist überladen – zu viele Besprechungen ohne klare Agenda.",
    "Feedbackgespräche finden nicht regelmäßig statt.",
]

VERBESSERUNG_POOL = [
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

TOPIC_TEXTS = {
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

JOB_TITLES = [
    "Software Engineer", "Senior Software Engineer", "Product Manager",
    "Data Scientist", "DevOps Engineer", "UX Designer", "Marketing Manager",
    "Vertriebsleiter", "HR Business Partner", "Finance Analyst",
    "Scrum Master", "Technical Lead", "Projektmanager", "Kundenberater",
    "Business Analyst", "Backend Developer", "Frontend Developer",
    "QA Engineer", "IT-Systemadministrator", "Sales Manager",
    "Content Manager", "Recruiter", "Operations Manager", "Controller",
]

CANDIDATE_TITEL_POOL = [
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

STELLENBESCHREIBUNG_POOL = [
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

CANDIDATE_VERBESSERUNG_POOL = [
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

STATUS_EMPLOYEE = ["Angestellt", "Ex-Angestellt", "Angestellt", "Angestellt", "Ex-Angestellt"]
STATUS_CANDIDATE = ["Bewerber", "Bewerber", "Bewerber"]

# ── Build employee rows ───────────────────────────────────────────────────────

def make_employee(company_id: int, period: str) -> dict:
    """period: 'early' | 'mid' | 'late' — controls rating trend"""
    if period == "early":
        base = random.uniform(2.8, 3.5)
        date = date_between(START, datetime(2022, 12, 31))
    elif period == "mid":
        base = random.uniform(3.2, 3.9)
        date = date_between(datetime(2023, 1, 1), datetime(2023, 12, 31))
    elif period == "late":
        base = random.uniform(3.6, 4.5)
        date = date_between(datetime(2024, 1, 1), datetime(2024, 12, 31))
    else:  # recent
        base = random.uniform(4.0, 4.8)
        date = date_between(datetime(2025, 1, 1), END)

    cats = {
        "arbeitsatmosphaere":         rand_rating(base + 0.3),
        "image":                      rand_rating(base),
        "work_life_balance":          rand_rating(base - 0.2),
        "karriere_weiterbildung":     rand_rating(base - 0.1),
        "gehalt_sozialleistungen":    rand_rating(base - 0.3),
        "kollegenzusammenhalt":       rand_rating(base + 0.4),
        "umwelt_sozialbewusstsein":   rand_rating(base + 0.1),
        "vorgesetztenverhalten":      rand_rating(base - 0.1),
        "kommunikation":              rand_rating(base - 0.2),
        "interessante_aufgaben":      rand_rating(base + 0.2),
        "umgang_mit_aelteren_kollegen": rand_rating(base + 0.1),
        "arbeitsbedingungen":         rand_rating(base),
        "gleichberechtigung":         rand_rating(base + 0.2),
    }
    avg = round(sum(cats.values()) / len(cats), 2)

    row = {
        "company_id": company_id,
        "titel": random.choice(JOB_TITLES),
        "status": random.choice(STATUS_EMPLOYEE),
        "datum": date,
        "durchschnittsbewertung": avg,
        "gerundete_durchschnittsbewertung": round(round(avg * 2) / 2, 1),
        "jobbeschreibung": random.choice(JOB_TITLES) + " im Bereich Produktentwicklung.",
        "gut_am_arbeitgeber_finde_ich": random.choice(GUT_POOL),
        "schlecht_am_arbeitgeber_finde_ich": random.choice(SCHLECHT_POOL),
        "verbesserungsvorschlaege": random.choice(VERBESSERUNG_POOL),
    }

    for cat, val in cats.items():
        row[f"sternebewertung_{cat}"] = val
        row[cat] = random.choice(TOPIC_TEXTS[cat])

    return row


def make_candidate(company_id: int, period: str) -> dict:
    if period == "early":
        base = random.uniform(2.9, 3.6)
        date = date_between(START, datetime(2022, 12, 31))
    elif period == "mid":
        base = random.uniform(3.3, 4.0)
        date = date_between(datetime(2023, 1, 1), datetime(2023, 12, 31))
    elif period == "late":
        base = random.uniform(3.7, 4.6)
        date = date_between(datetime(2024, 1, 1), datetime(2024, 12, 31))
    else:  # recent
        base = random.uniform(4.1, 4.9)
        date = date_between(datetime(2025, 1, 1), END)

    cats_candidate = {
        "erklaerung_der_weiteren_schritte":  rand_rating(base),
        "zufriedenstellende_reaktion":        rand_rating(base + 0.1),
        "vollstaendigkeit_der_infos":         rand_rating(base - 0.1),
        "zufriedenstellende_antworten":       rand_rating(base),
        "angenehme_atmosphaere":              rand_rating(base + 0.3),
        "professionalitaet_des_gespraechs":   rand_rating(base + 0.2),
        "wertschaetzende_behandlung":         rand_rating(base + 0.2),
        "erwartbarkeit_des_prozesses":        rand_rating(base - 0.2),
        "zeitgerechte_zu_oder_absage":        rand_rating(base - 0.1),
        "schnelle_antwort":                   rand_rating(base),
    }
    avg = round(sum(cats_candidate.values()) / len(cats_candidate), 2)

    row = {
        "company_id": company_id,
        "titel": random.choice(CANDIDATE_TITEL_POOL),
        "status": random.choice(STATUS_CANDIDATE),
        "datum": date,
        "durchschnittsbewertung": avg,
        "gerundete_durchschnittsbewertung": round(round(avg * 2) / 2, 1),
        "stellenbeschreibung": random.choice(STELLENBESCHREIBUNG_POOL),
        "verbesserungsvorschlaege": random.choice(CANDIDATE_VERBESSERUNG_POOL),
    }
    for cat, val in cats_candidate.items():
        row[f"sternebewertung_{cat}"] = val

    return row


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Creating company: {COMPANY_NAME} ...")

    existing = supabase.table("companies").select("id,name").ilike("name", COMPANY_NAME).execute()
    if existing.data:
        company_id = existing.data[0]["id"]
        print(f"  Company already exists with id={company_id}")
    else:
        res = supabase.table("companies").insert({"name": COMPANY_NAME}).execute()
        company_id = res.data[0]["id"]
        print(f"  Created company with id={company_id}")

    print("Deleting existing reviews ...")
    supabase.table("employee").delete().eq("company_id", company_id).execute()
    supabase.table("candidates").delete().eq("company_id", company_id).execute()

    # Build employee records: 134 per year × 4 years = 536 total
    employees = []
    for period in ("early", "mid", "late", "recent"):
        for _ in range(134):
            employees.append(make_employee(company_id, period))

    print(f"Inserting {len(employees)} employee reviews ...")
    batch = 50
    for i in range(0, len(employees), batch):
        supabase.table("employee").insert(employees[i:i+batch]).execute()
        print(f"  Inserted employees {i+1}–{min(i+batch, len(employees))}")

    # Build candidate records: 66 per year × 4 years = 264 total
    candidates = []
    for period in ("early", "mid", "late", "recent"):
        for _ in range(66):
            candidates.append(make_candidate(company_id, period))

    print(f"Inserting {len(candidates)} candidate reviews ...")
    for i in range(0, len(candidates), batch):
        supabase.table("candidates").insert(candidates[i:i+batch]).execute()
        print(f"  Inserted candidates {i+1}–{min(i+batch, len(candidates))}")

    print("\nDone!")
    print(f"  Company: {COMPANY_NAME} (id={company_id})")
    print(f"  Employee reviews: {len(employees)}")
    print(f"  Candidate reviews: {len(candidates)}")


if __name__ == "__main__":
    main()
