"""
Seed script: Creates "Demo 2" company with comprehensive dummy data.
Characteristics: declining trend, strong Work-Life-Balance & Arbeitsbedingungen,
weak Kommunikation, Karriere & Vorgesetztenverhalten.

Run from the backend directory: python scripts/seed_demo2.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import get_supabase_client
from datetime import datetime, timedelta
import random

random.seed(99)
supabase = get_supabase_client()

COMPANY_NAME = "Demo 2"

# ── Helpers ──────────────────────────────────────────────────────────────────

def rand_rating(mu, sigma=0.6, lo=1.0, hi=5.0):
    v = random.gauss(mu, sigma)
    return round(max(lo, min(hi, v)), 2)


def date_between(start: datetime, end: datetime) -> str:
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.date().isoformat()


START = datetime(2022, 1, 1)
END   = datetime(2026, 5, 15)

# ── Text pools ────────────────────────────────────────────────────────────────

GUT_POOL = [
    "Die Work-Life-Balance ist vorbildlich – Überstunden sind wirklich die Ausnahme.",
    "Modernes Büro mit sehr guter technischer Ausstattung und ergonomischen Arbeitsplätzen.",
    "Das Unternehmen ist bekannt und angesehen – man ist gerne Teil davon.",
    "Nachhaltigkeit wird ernsthaft betrieben, nicht nur als PR-Maßnahme.",
    "Flexible Arbeitszeiten und echte Möglichkeit zum Homeoffice.",
    "Die Arbeitsbedingungen sind wirklich gut – höhenverstellbare Tische, neue Hardware.",
    "Kollegenzusammenhalt im eigenen Team ist stark, man unterstützt sich.",
    "Gute Kantine mit vielfältigem Angebot zu fairen Preisen.",
    "Ältere Kollegen werden respektiert und ihre Erfahrung geschätzt.",
    "Gleichberechtigung wird offiziell groß geschrieben und weitgehend gelebt.",
    "Homeoffice-Budget wurde bereitgestellt – das war eine positive Überraschung.",
    "Jobticket und Fahrradleasing als Benefits sind ein echter Pluspunkt.",
    "Attraktive Lage mit guter ÖPNV-Anbindung.",
    "Betriebliche Altersvorsorge mit Arbeitgeberzuschuss ist vorhanden.",
    "Urlaub kann problemlos genommen werden, kein Druck dagegen.",
]

SCHLECHT_POOL = [
    "Kommunikation aus dem Management ist chaotisch – Entscheidungen kommen oft überraschend.",
    "Karrieremöglichkeiten sind sehr begrenzt, Aufstieg fast nicht möglich.",
    "Vorgesetzte führen durch Kontrolle statt durch Vertrauen.",
    "Gehalt ist seit Jahren eingefroren, Inflation wird nicht ausgeglichen.",
    "Interne Prozesse sind extrem bürokratisch und bremsen jede Initiative.",
    "Feedback-Kultur existiert kaum – Kritik wird nicht gerne gehört.",
    "Mitarbeitergespräche finden selten statt, meist nur wenn Probleme da sind.",
    "Weiterbildungsbudget ist nominell vorhanden, aber in der Praxis schwer zu bekommen.",
    "Hohe Fluktuation in Führungspositionen sorgt für ständige Unsicherheit.",
    "Entscheidungen werden top-down getroffen ohne Einbeziehung der Mitarbeiter.",
    "IT-Systeme sind veraltet und bremsen die tägliche Arbeit erheblich.",
    "Abteilungssilos verhindern effektive Zusammenarbeit über Teams hinweg.",
    "Beförderungen passieren nach Betriebszugehörigkeit, nicht nach Leistung.",
    "Überstunden werden stillschweigend erwartet, selten explizit kommuniziert.",
    "Die Unternehmenskultur hat sich in den letzten Jahren deutlich verschlechtert.",
]

VERBESSERUNG_POOL = [
    "Transparentere Kommunikation aus dem Vorstand – Entscheidungen besser erklären.",
    "Führungskräfte-Training dringend notwendig, moderne Führungsansätze fehlen.",
    "Gehaltsstrukturen überarbeiten und an Markt anpassen.",
    "Klare Karrierepfade definieren und kommunizieren.",
    "Feedbackkultur aufbauen – regelmäßige 1:1s einführen.",
    "Weiterbildungsbudget erhöhen und Nutzung vereinfachen.",
    "Abteilungsübergreifende Zusammenarbeit aktiv fördern.",
    "IT-Infrastruktur modernisieren – das kostet Produktivität.",
    "Mitarbeiter in Entscheidungsprozesse einbinden.",
    "Flachere Hierarchien und kürzere Entscheidungswege schaffen.",
    "Anerkennungskultur etablieren – gute Arbeit wird zu selten gewürdigt.",
    "Change-Management-Prozesse einführen bei Umstrukturierungen.",
    "Onboarding-Prozess verbessern – neue Kollegen sind oft auf sich allein gestellt.",
    "Interne Mobilität ermöglichen – Abteilungswechsel sollte leichter sein.",
    "Work-Life-Balance auch für Führungskräfte als Vorbild leben.",
]

TOPIC_TEXTS = {
    "arbeitsatmosphaere": [
        "Die Atmosphäre hat sich in letzter Zeit leider verschlechtert – Druck ist spürbar.",
        "Innerhalb des eigenen Teams gut, abteilungsübergreifend angespannt.",
        "Wertschätzung durch Vorgesetzte lässt zu wünschen übrig.",
        "Früher war die Stimmung deutlich besser, Veränderungen haben das Klima belastet.",
        "Es gibt Inseln mit guter Atmosphäre, aber kein einheitliches Bild.",
        "Viele gute Kollegen, aber die Unternehmenskultur drückt auf die Stimmung.",
        "Teamzusammenhalt im direkten Umfeld ist gut, strukturell aber Probleme.",
    ],
    "image": [
        "Nach außen hin hat das Unternehmen einen guten Ruf, der intern nicht immer bestätigt wird.",
        "Bekannte Marke – man ist stolz, hier zu arbeiten, trotz interner Schwächen.",
        "Image in der Branche ist gut, was die Jobsuche danach erleichtern wird.",
        "Öffentliches Bild und gelebte Realität klaffen auseinander.",
        "Kunden schätzen das Unternehmen, intern könnte mehr daraus gemacht werden.",
        "Solider Ruf in der Region – hilft bei der Kundengewinnung.",
        "Gutes Image als Arbeitgeber nach außen, interne Mitarbeiterzufriedenheit lässt nach.",
    ],
    "work_life_balance": [
        "Work-Life-Balance ist eindeutig die größte Stärke – Urlaub ist kein Problem.",
        "Homeoffice wird wirklich unterstützt, keine schiefen Blicke.",
        "Klare Trennung von Arbeitszeit und Freizeit – Abends wird nicht mehr erwartet.",
        "Flexible Gleitzeit funktioniert in der Praxis sehr gut.",
        "Teilzeitmodelle sind möglich und werden nicht schief angeschaut.",
        "Überstunden sind wirklich selten – das ist der große Vorteil hier.",
        "Familienfreundliche Kultur, Elternzeit wird unterstützt.",
        "Man kann abschalten – das ist nicht selbstverständlich.",
    ],
    "karriere_weiterbildung": [
        "Karrierechancen sind sehr begrenzt – Positionen bleiben besetzt, Aufstieg kaum möglich.",
        "Weiterbildungsbudget vorhanden, aber in der Praxis schwer freizubekommen.",
        "Karrierepfade sind unklar und wenig transparent kommuniziert.",
        "Beförderungen nach Betriebszugehörigkeit, nicht nach Leistung.",
        "Wer Karriere machen will, muss das Unternehmen verlassen.",
        "Interne Mobilität ist de facto nicht möglich.",
        "Online-Kurse werden genehmigt, aber strategische Weiterentwicklung fehlt.",
    ],
    "gehalt_sozialleistungen": [
        "Gehalt wurde seit Jahren nicht an Inflation angepasst – realer Rückgang.",
        "Benefits wie Jobticket und Altersvorsorge sind gut, das Grundgehalt aber zu niedrig.",
        "Gehaltsverhandlungen verlaufen oft enttäuschend.",
        "Für die Branche unterdurchschnittliches Gehalt, keine klare Struktur.",
        "Boni sind vorhanden aber intransparent berechnet.",
        "Sozialleistungen sind ordentlich, das Gehalt ist der Schwachpunkt.",
        "Marktanpassungen finden kaum statt.",
    ],
    "kollegenzusammenhalt": [
        "Direktes Team hält zusammen und unterstützt sich – das ist der Anker hier.",
        "Kollegialität auf Teamebene ist gut, über Abteilungen hinweg weniger.",
        "Viele nette Kollegen machen den Alltag erträglich.",
        "Informelle Netzwerke funktionieren, formale Strukturen weniger.",
        "In Krisenzeiten hält das Team zusammen – das ist positiv.",
        "Guter Zusammenhalt auf unterer Ebene, oben eher Ellbogen.",
        "Neue Kollegen werden aufgenommen, Einarbeitung läuft durch Kollegen.",
    ],
    "umwelt_sozialbewusstsein": [
        "Nachhaltigkeitsstrategie ist ambitioniert und wird tatsächlich umgesetzt.",
        "CO2-Reduktionsziele werden ernst genommen und gemessen.",
        "Soziales Engagement durch Spendenmatching und Freiwilligentage.",
        "Papierloses Büro wird aktiv vorangetrieben.",
        "Fahrradleasing und ÖPNV-Ticket zeigen ökologisches Bewusstsein.",
        "Energieverbrauch wird aktiv gesenkt – Erneuerbare Energien im Einsatz.",
        "Lieferketten-Transparenz wird verbessert – echter Fortschritt.",
    ],
    "vorgesetztenverhalten": [
        "Führungsstil ist kontrollierend statt fördernd – Mikromanagement ist verbreitet.",
        "Konstruktives Feedback ist selten, Kritik kommt einseitig von oben.",
        "Vorgesetzte sind häufig wechselnd – Kontinuität fehlt.",
        "1:1-Gespräche finden unregelmäßig statt, oft nur bei Problemen.",
        "Vertrauen in Mitarbeiter wird nicht vorgelebt, alles muss abgesegnet werden.",
        "Manche Führungskräfte sind gut, aber das System belohnt einen anderen Stil.",
        "Entscheidungen werden selten erklärt – Richtungswechsel kommen überraschend.",
        "Führungskräfte-Rotation ist hoch, was zu ständiger Neuorientierung zwingt.",
    ],
    "kommunikation": [
        "Kommunikation aus dem Management ist das größte Problem – unvorhersehbar.",
        "Entscheidungen werden getroffen ohne die Betroffenen zu informieren.",
        "Gerüchte verbreiten sich schneller als offizielle Infos – das ist symptomatisch.",
        "All-Hands-Meetings finden statt, sind aber oft wenig informativ.",
        "Zwischen Abteilungen kommuniziert man aneinander vorbei.",
        "E-Mail-Kultur ist überwältigend, wichtige Infos gehen unter.",
        "Townhalls haben aufgehört – seitdem weiß niemand mehr was strategisch läuft.",
        "Feedback nach oben verpufft meist wirkungslos.",
    ],
    "interessante_aufgaben": [
        "Aufgaben sind solide, aber selten wirklich herausfordernd oder innovativ.",
        "Routinetätigkeiten überwiegen, eigene Ideen werden kaum aufgegriffen.",
        "In manchen Teams gibt es spannende Projekte, aber nicht flächendeckend.",
        "Die Branche ist interessant, die konkreten Aufgaben könnten es mehr sein.",
        "Interdisziplinäre Arbeit wäre wünschenswert, bleibt aber die Ausnahme.",
        "Ownership über Aufgaben fehlt häufig – vieles wird von oben diktiert.",
        "Innovationskultur ist kaum vorhanden, Status quo wird bevorzugt.",
    ],
    "umgang_mit_aelteren_kollegen": [
        "Erfahrene Kollegen werden respektiert, ihr Wissen aktiv eingebunden.",
        "Altersdiversität ist vorhanden und wird nicht zum Thema gemacht.",
        "Ältere Mitarbeiter profitieren von stabilen Arbeitsbedingungen.",
        "Wissenstransfer zwischen Generationen funktioniert im Großen und Ganzen.",
        "Keine spürbare Altersdiskriminierung – Leistung zählt.",
        "Flexible Arbeitsmodelle für ältere Kollegen sind vorhanden.",
        "Seniorität wird respektiert, auch wenn Karriere kaum möglich ist.",
    ],
    "arbeitsbedingungen": [
        "Arbeitsplätze sind modern und ergonomisch – höhenverstellbare Schreibtische überall.",
        "Neue Hardware wird regelmäßig bereitgestellt, keine veralteten Geräte.",
        "Büro ist gut ausgestattet, Küche sauber, ruhige Zonen vorhanden.",
        "Home-Office-Ausstattung wurde vollständig vom Unternehmen bezahlt.",
        "Klimaanlage und Beleuchtung funktionieren einwandfrei.",
        "Gute ÖPNV-Anbindung, Parkplätze für Fahrräder vorhanden.",
        "Ruhige Arbeitsbereiche neben Kollaborationszonen – gute Balance.",
        "Technische Infrastruktur ist der Highlight des Unternehmens.",
    ],
    "gleichberechtigung": [
        "Diversity-Initiativen sind vorhanden und werden ernsthaft verfolgt.",
        "Frauen in Führungspositionen sind präsent und sichtbar.",
        "Gehaltsgleichheit wird regelmäßig geprüft und korrigiert.",
        "Internationales Team – Vielfalt wird als Stärke gesehen.",
        "LGBTQ+-freundliche Kultur ohne große Vorbehalte.",
        "Barrierefreiheit ist gewährleistet, auch für Mobilitätseingeschränkte.",
        "Elternzeit wird für alle Geschlechter unterstützt.",
    ],
}

JOB_TITLES = [
    "Projektingenieur", "Senior Analyst", "Compliance Manager",
    "IT-Architekt", "HR Manager", "Controlling Specialist",
    "Prozessmanager", "Legal Counsel", "Risk Manager",
    "Supply Chain Manager", "Einkäufer", "Technischer Redakteur",
    "Qualitätsmanager", "Vertriebsmanager", "Strategy Consultant",
    "Data Engineer", "IT-Security Analyst", "Change Manager",
    "Kommunikationsmanager", "Nachhaltigkeitsbeauftragter",
]

CANDIDATE_TITEL_POOL = [
    "Bewerbungsprozess sehr intransparent", "Langer Prozess ohne klares Feedback",
    "Mehrere Runden ohne Rückmeldung", "Assessment Center wenig strukturiert",
    "Video-Interview sehr unprofessionell vorbereitet", "Absage kam sehr spät",
    "Keine Rückmeldung nach Gespräch", "Prozess dauerte über 3 Monate",
    "HR kaum erreichbar", "Technischer Test unverhältnismäßig aufwändig",
    "Gespräch war angenehm, Prozess drum herum nicht", "Gehalt erst sehr spät besprochen",
    "Bewerbung für Fachposition gut, Logistik schlecht", "Feedback nach Absage sehr allgemein",
    "Erster Eindruck positiv, Prozess dann enttäuschend",
]

STELLENBESCHREIBUNG_POOL = [
    "Bewerbung auf eine Stelle als Projektingenieur. Der Prozess dauerte über zwei Monate.",
    "Mehrere Gespräche ohne klare Kommunikation über nächste Schritte.",
    "Assessment Center mit wenig Strukturierung und unklaren Erwartungen.",
    "HR-Kontakt war schwierig zu erreichen, Rückmeldungen kamen verzögert.",
    "Technisches Interview war gut, der Rest des Prozesses weniger professionell.",
    "Bewerbung auf eine Managementstelle mit umfangreichem Auswahlprozess.",
    "Online-Test war fair, aber Feedback danach ließ lange auf sich warten.",
    "Gespräch mit zukünftigem Team verlief gut, HR-Seite war wenig vorbereitet.",
    "Drei Runden plus Case Study – Aufwand stand nicht im Verhältnis.",
    "Prozess war insgesamt in Ordnung, aber Kommunikation deutlich verbesserungswürdig.",
]

CANDIDATE_VERBESSERUNG_POOL = [
    "Zeitnahe Rückmeldung nach jeder Runde wäre sehr hilfreich gewesen.",
    "Klarere Kommunikation über den Zeitplan und die nächsten Schritte.",
    "Konstruktives Feedback nach Absage würde sehr helfen.",
    "Gehalt früher im Prozess ansprechen spart beiden Seiten Zeit.",
    "Weniger Runden oder gebündelte Interviews wären effizienter.",
    "HR sollte besser erreichbar sein und schneller antworten.",
    "Case Study für eine unbezahlte Bewerbungsrunde war zu aufwändig.",
    "Mehr Informationen über die Rolle und das Team vorab bereitstellen.",
    "Technik für Video-Interviews vorab testen – Verbindungsprobleme vermeiden.",
    "Proaktive Updates auch wenn sich der Prozess verzögert.",
]

STATUS_EMPLOYEE = ["Angestellt", "Ex-Angestellt", "Angestellt", "Ex-Angestellt", "Ex-Angestellt"]
STATUS_CANDIDATE = ["Bewerber", "Bewerber", "Bewerber"]

# Demo 2: sinkender Trend – frühe Werte hoch, späte niedrig
EMP_RANGES  = {"early": (4.0, 4.8), "mid": (3.3, 4.2), "late": (2.5, 3.5), "recent": (1.8, 2.8)}
CAND_RANGES = {"early": (3.8, 4.6), "mid": (3.1, 4.0), "late": (2.4, 3.3), "recent": (1.7, 2.7)}

CAT_OFFSETS = {
    "arbeitsatmosphaere": -0.1, "image": +0.2, "work_life_balance": +0.4,
    "karriere_weiterbildung": -0.5, "gehalt_sozialleistungen": -0.4,
    "kollegenzusammenhalt": +0.1, "umwelt_sozialbewusstsein": +0.3,
    "vorgesetztenverhalten": -0.3, "kommunikation": -0.5,
    "interessante_aufgaben": -0.1, "umgang_mit_aelteren_kollegen": +0.2,
    "arbeitsbedingungen": +0.3, "gleichberechtigung": +0.1,
}

CAND_OFFSETS = {
    "erklaerung_der_weiteren_schritte": -0.3, "zufriedenstellende_reaktion": -0.2,
    "vollstaendigkeit_der_infos": -0.3, "zufriedenstellende_antworten": -0.1,
    "angenehme_atmosphaere": +0.1, "professionalitaet_des_gespraechs": 0.0,
    "wertschaetzende_behandlung": +0.1, "erwartbarkeit_des_prozesses": -0.4,
    "zeitgerechte_zu_oder_absage": -0.4, "schnelle_antwort": -0.3,
}

EMPLOYEE_CATS = [
    "arbeitsatmosphaere", "image", "work_life_balance", "karriere_weiterbildung",
    "gehalt_sozialleistungen", "kollegenzusammenhalt", "umwelt_sozialbewusstsein",
    "vorgesetztenverhalten", "kommunikation", "interessante_aufgaben",
    "umgang_mit_aelteren_kollegen", "arbeitsbedingungen", "gleichberechtigung",
]

CANDIDATE_CATS = [
    "erklaerung_der_weiteren_schritte", "zufriedenstellende_reaktion",
    "vollstaendigkeit_der_infos", "zufriedenstellende_antworten",
    "angenehme_atmosphaere", "professionalitaet_des_gespraechs",
    "wertschaetzende_behandlung", "erwartbarkeit_des_prozesses",
    "zeitgerechte_zu_oder_absage", "schnelle_antwort",
]


def make_employee(company_id: int, period: str) -> dict:
    lo, hi = EMP_RANGES[period]
    base = random.gauss((lo + hi) / 2, 0.4)
    base = max(lo, min(hi, base))

    if period == "early":
        date = date_between(START, datetime(2022, 12, 31))
    elif period == "mid":
        date = date_between(datetime(2023, 1, 1), datetime(2023, 12, 31))
    elif period == "late":
        date = date_between(datetime(2024, 1, 1), datetime(2024, 12, 31))
    else:  # recent
        date = date_between(datetime(2025, 1, 1), END)

    cats = {cat: rand_rating(base + CAT_OFFSETS[cat]) for cat in EMPLOYEE_CATS}
    avg = round(sum(cats.values()) / len(cats), 2)

    row = {
        "company_id": company_id,
        "titel": random.choice(JOB_TITLES),
        "status": random.choice(STATUS_EMPLOYEE),
        "datum": date,
        "durchschnittsbewertung": avg,
        "gerundete_durchschnittsbewertung": round(round(avg * 2) / 2, 1),
        "jobbeschreibung": random.choice(JOB_TITLES) + " im Bereich Unternehmensstrategie.",
        "gut_am_arbeitgeber_finde_ich": random.choice(GUT_POOL),
        "schlecht_am_arbeitgeber_finde_ich": random.choice(SCHLECHT_POOL),
        "verbesserungsvorschlaege": random.choice(VERBESSERUNG_POOL),
    }
    for cat in EMPLOYEE_CATS:
        row[f"sternebewertung_{cat}"] = cats[cat]
        row[cat] = random.choice(TOPIC_TEXTS[cat])
    return row


def make_candidate(company_id: int, period: str) -> dict:
    lo, hi = CAND_RANGES[period]
    base = random.gauss((lo + hi) / 2, 0.4)
    base = max(lo, min(hi, base))

    if period == "early":
        date = date_between(START, datetime(2022, 12, 31))
    elif period == "mid":
        date = date_between(datetime(2023, 1, 1), datetime(2023, 12, 31))
    elif period == "late":
        date = date_between(datetime(2024, 1, 1), datetime(2024, 12, 31))
    else:  # recent
        date = date_between(datetime(2025, 1, 1), END)

    cats = {cat: rand_rating(base + CAND_OFFSETS[cat]) for cat in CANDIDATE_CATS}
    avg = round(sum(cats.values()) / len(cats), 2)

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
    for cat in CANDIDATE_CATS:
        row[f"sternebewertung_{cat}"] = cats[cat]
    return row


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

    print(f"\nDone! Company: {COMPANY_NAME} (id={company_id})")
    print(f"  Employee reviews: {len(employees)}")
    print(f"  Candidate reviews: {len(candidates)}")


if __name__ == "__main__":
    main()
