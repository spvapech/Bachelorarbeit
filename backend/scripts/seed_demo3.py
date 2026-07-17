"""
Seed script: Creates "Demo 3" company with V-shaped trend data.
Profile: Good start (2022) → Crisis/restructuring dip (2023) → Recovery (2024+)
Strengths: Gleichberechtigung, Umwelt, Arbeitsbedingungen, Kollegenzusammenhalt
Weaknesses during crisis: Kommunikation, Vorgesetztenverhalten, Atmosphäre

Run from the backend directory: python scripts/seed_demo3.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import get_supabase_client
from datetime import datetime, timedelta
import random

random.seed(77)
supabase = get_supabase_client()

COMPANY_NAME = "Demo 3"

def rand_rating(mu, sigma=0.6, lo=1.0, hi=5.0):
    v = random.gauss(mu, sigma)
    return round(max(lo, min(hi, v)), 2)

def date_between(start: datetime, end: datetime) -> str:
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.date().isoformat()

START = datetime(2022, 1, 1)
END   = datetime(2026, 5, 15)

# V-Form: früh gut → Krise mitte → Erholung spät
EMP_RANGES  = {"early": (3.8, 4.4), "mid": (2.3, 3.1), "late": (3.5, 4.3), "recent": (3.9, 4.7)}
CAND_RANGES = {"early": (3.6, 4.2), "mid": (2.2, 3.0), "late": (3.4, 4.1), "recent": (3.7, 4.5)}

CAT_OFFSETS = {
    "arbeitsatmosphaere": -0.1, "image": +0.1, "work_life_balance": 0.0,
    "karriere_weiterbildung": +0.1, "gehalt_sozialleistungen": 0.0,
    "kollegenzusammenhalt": +0.2, "umwelt_sozialbewusstsein": +0.3,
    "vorgesetztenverhalten": -0.2, "kommunikation": -0.3,
    "interessante_aufgaben": +0.2, "umgang_mit_aelteren_kollegen": +0.1,
    "arbeitsbedingungen": +0.2, "gleichberechtigung": +0.3,
}

CAND_OFFSETS = {
    "erklaerung_der_weiteren_schritte": -0.1, "zufriedenstellende_reaktion": 0.0,
    "vollstaendigkeit_der_infos": -0.1, "zufriedenstellende_antworten": +0.1,
    "angenehme_atmosphaere": +0.2, "professionalitaet_des_gespraechs": +0.1,
    "wertschaetzende_behandlung": +0.2, "erwartbarkeit_des_prozesses": -0.2,
    "zeitgerechte_zu_oder_absage": -0.1, "schnelle_antwort": 0.0,
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

JOB_TITLES = [
    "Produktionsleiter", "Qualitätsingenieur", "HR Business Partner",
    "IT-Projektmanager", "Finance Controller", "Operations Manager",
    "Vertriebsingenieur", "R&D Engineer", "Supply Chain Analyst",
    "Werkstudent Ingenieurwesen", "Teamleiter Fertigung", "Prozessingenieur",
    "Einkaufsmanager", "Lean Manager", "Digitalisierungsmanager",
    "Nachhaltigkeitsmanager", "Compliance Officer", "Data Analyst",
    "Technischer Einkäufer", "Projektkoordinator",
]

# Phase-spezifische Texte für authentische V-Form-Narrative

GUT_POOL_EARLY = [
    "Das Unternehmen war in einer starken Wachstumsphase – viel Aufbruchsstimmung.",
    "Gute Kommunikation und klare Ziele machten das Arbeiten angenehm.",
    "Starkes Team, das gemeinsam an einem Strang gezogen hat.",
    "Führungsebene hatte eine klare Vision und hat diese gut kommuniziert.",
    "Investitionen in Mitarbeiterentwicklung waren spürbar.",
    "Offene Fehlerkultur und konstruktives Miteinander prägten den Alltag.",
]

GUT_POOL_CRISIS = [
    "Trotz schwieriger Zeit haben Kollegen zusammengehalten – das war wertvoll.",
    "Work-Life-Balance blieb erstaunlicherweise erhalten, auch in der Krise.",
    "Arbeitsbedingungen wurden trotz Einsparmaßnahmen nicht schlechter.",
    "Einige direkte Vorgesetzte haben vorbildlich durch die Krise geführt.",
    "Der Umwelt- und Sozialeinsatz des Unternehmens blieb konstant.",
    "Gleichberechtigung wurde auch in der Krise nicht geopfert.",
]

GUT_POOL_RECOVERY = [
    "Die Erholung nach der Restrukturierung ist spürbar – neue Energie.",
    "Neues Management hat frischen Wind gebracht und kommuniziert besser.",
    "Investitionen in Teams und Weiterbildung nehmen wieder zu.",
    "Die Krise hat das Unternehmen in einigen Bereichen stärker gemacht.",
    "Transparentere Kommunikation als in der Krisenzeit – positiver Wandel.",
    "Teamstimmung hat sich deutlich erholt, Vertrauen wächst wieder.",
    "Neue Prozesse und klare Ziele geben wieder Orientierung.",
]

SCHLECHT_POOL_EARLY = [
    "Wachstum war manchmal zu schnell – Strukturen kamen nicht hinterher.",
    "Onboarding war in der Wachstumsphase chaotisch.",
    "Gehalt blieb trotz gutem Geschäft unter Markt.",
]

SCHLECHT_POOL_CRISIS = [
    "Restrukturierung wurde schlecht kommuniziert – viele Gerüchte, wenig Fakten.",
    "Führungswechsel auf breiter Front sorgte für massive Verunsicherung.",
    "Entlassungswellen ohne klare Erklärung haben das Vertrauen erschüttert.",
    "Kommunikation aus dem Vorstand war in der Krise quasi nicht existent.",
    "Vorgesetzte haben unter Druck autoritär geführt statt zu unterstützen.",
    "Die Unternehmenskultur hat in der Krisenzeit stark gelitten.",
    "Keine klare Zukunftsperspektive kommuniziert – Unsicherheit überall.",
    "Karrieremöglichkeiten wurden eingefroren, Beförderungen gestoppt.",
]

SCHLECHT_POOL_RECOVERY = [
    "Nicht alle Führungskräfte aus der Krisenzeit passen zur neuen Kultur.",
    "Vertrauen wurde beschädigt – Erholung braucht mehr Zeit als erwartet.",
    "Einige Strukturschäden aus der Restrukturierung sind noch spürbar.",
    "Gehalt wurde in der Krise nicht angepasst und ist noch nicht normalisiert.",
]

VERBESSERUNG_POOL = [
    "Offenere Kommunikation auch in schwierigen Phasen – Gerüchte aktiv begegnen.",
    "Führungskräfte in Krisenmanagement schulen – nicht jeder ist darauf vorbereitet.",
    "Restrukturierungen besser vorbereiten und transparenter durchführen.",
    "Vertrauensaufbau nach Krise aktiv gestalten, nicht passiv abwarten.",
    "Gehälter auch in Erholungsphasen schneller anpassen.",
    "Lehren aus der Krise institutionalisieren – was hat funktioniert, was nicht?",
    "Mitarbeiterfeedback systematischer einholen und darauf reagieren.",
    "Karrierepfade nach Restrukturierung neu definieren und kommunizieren.",
    "Kulturarbeit aktiv angehen – Vertrauen wächst nicht von selbst.",
    "Bewerbern gegenüber transparenter über die vergangenen Herausforderungen sein.",
]

TOPIC_TEXTS = {
    "arbeitsatmosphaere": [
        "In der Krise war die Stimmung auf dem Tiefpunkt – inzwischen erholt sie sich.",
        "Innerhalb des Teams gut, aber das große Bild war zeitweise sehr angespannt.",
        "Die Restrukturierung hat Narben hinterlassen, die langsam heilen.",
        "Jetzt deutlich besser als 2023 – man merkt dass die Erholung läuft.",
        "Kollegialer Zusammenhalt hat die schwere Phase erträglich gemacht.",
        "Früher sehr gut, dann schwierig, jetzt auf dem Weg zurück.",
    ],
    "image": [
        "Das Unternehmen hat trotz Krise seinen Ruf in der Branche halten können.",
        "Bekannte Marke – hat geholfen, die Krise nach außen abzufedern.",
        "Image nach innen und außen war lange Zeit auseinander – wird besser.",
        "Starke Marke gibt Stabilität, auch wenn es intern turbulent war.",
        "Kunden schätzen das Unternehmen, was Sicherheit gegeben hat.",
        "Reputationsmanagement in der Krise war professionell.",
    ],
    "work_life_balance": [
        "Auch in der Krisenphase wurde Work-Life-Balance nicht geopfert.",
        "Homeoffice-Regelungen blieben stabil, kein Rückschritt.",
        "Urlaub konnte auch in schwierigen Zeiten genommen werden.",
        "Flexible Arbeitszeiten sind ein verlässlicher Anker geblieben.",
        "Kein Druck zu Überstunden, selbst als es schwierig wurde.",
        "Balance ist eine der wenigen Konstanten durch alle Phasen.",
    ],
    "karriere_weiterbildung": [
        "Karriere war in der Krisenphase eingefroren, erholt sich aber.",
        "Weiterbildungsbudget wurde in der Krise gestrichen, kommt jetzt zurück.",
        "Neue Karrierepfade werden gerade neu definiert – positiver Ausblick.",
        "Interne Beförderungen werden wieder möglich, das ist ermutigend.",
        "Lernkultur war vor der Krise stark und wird wieder aufgebaut.",
        "Klarere Entwicklungsperspektiven als noch vor einem Jahr.",
    ],
    "gehalt_sozialleistungen": [
        "Gehalt wurde in der Krise eingefroren, Normalisierung läuft schleppend.",
        "Benefits blieben erhalten – das war ein positives Signal in der Krise.",
        "Marktanpassung steht aus, wird aber kommuniziert für dieses Jahr.",
        "Für die Branche im Mittelfeld – könnte besser sein nach der Krise.",
        "Betriebliche Altersvorsorge und Jobticket blieben unangetastet.",
        "Gehaltserhöhungen kommen langsam zurück – ermutigend aber noch nicht ausreichend.",
    ],
    "kollegenzusammenhalt": [
        "Der Zusammenhalt in der Krise war beeindruckend – ein starker Kitt.",
        "Kollegen haben sich gegenseitig durch schwere Zeiten getragen.",
        "Team hat in der Krisenphase besonders gut funktioniert.",
        "Informelle Netzwerke haben formale Strukturen in der Krise ersetzt.",
        "Gemeinsame schwere Erfahrung hat Teams enger zusammengebracht.",
        "Vertrauen unter Kollegen ist geblieben, auch wenn das in die Führung erschüttert war.",
    ],
    "umwelt_sozialbewusstsein": [
        "Nachhaltigkeitsstrategie wurde nicht geopfert – auch in der Krise nicht.",
        "Umwelt-Commitment ist ein verlässlicher Wert des Unternehmens.",
        "Soziales Engagement blieb konstant – ein gutes Signal in schwierigen Zeiten.",
        "CO2-Ziele werden weiter verfolgt, keine Abstriche trotz Druck.",
        "Fahrradleasing und ÖPNV-Ticket blieben als Benefits erhalten.",
        "Nachhaltigkeits-Reporting wird transparenter und ambitionierter.",
    ],
    "vorgesetztenverhalten": [
        "In der Krise haben viele Führungskräfte versagt – zu wenig Kommunikation.",
        "Neues Management nach der Restrukturierung ist deutlich besser.",
        "Manche direkten Vorgesetzten waren Anker, die Führungsebene nicht.",
        "Vertrauen in Führung war auf dem Tiefpunkt 2023, erholt sich langsam.",
        "Coaching-Ansatz setzt sich jetzt durch – besser als das Krisenmanagement.",
        "Es gibt große Unterschiede: manche Führungskräfte sehr gut, andere nicht.",
    ],
    "kommunikation": [
        "Die Krise hat die Kommunikationsschwäche schonungslos offengelegt.",
        "Heute deutlich transparenter als auf dem Tiefpunkt 2023.",
        "Regelmäßige Updates vom Management sind seit der Erholung Standard.",
        "Gerüchteküche war in der Krisenzeit das einzige Informationsmedium.",
        "Neue Kommunikationsformate werden eingeführt – positiver Wandel.",
        "Noch nicht auf dem Niveau vor der Krise, aber auf dem richtigen Weg.",
    ],
    "interessante_aufgaben": [
        "Aufgaben waren immer interessant – das hat viele durch die Krise gebracht.",
        "Technisch herausfordernde Projekte gab es auch in schwierigen Zeiten.",
        "Innovationskraft wird gerade reaktiviert – spannende Projekte entstehen.",
        "Die Krise hat neue, interessante Transformationsprojekte hervorgebracht.",
        "Ownership über Aufgaben wurde durch die Krise nicht wesentlich beschränkt.",
        "Diverse Projekte machen die Arbeit nach wie vor bedeutsam.",
    ],
    "umgang_mit_aelteren_kollegen": [
        "Ältere Kollegen wurden in der Restrukturierung fair behandelt.",
        "Erfahrung wurde auch in der Krise wertgeschätzt.",
        "Wissenstransfer hat geholfen, Verluste durch Abgänge abzufedern.",
        "Keine altersbezogene Diskriminierung – auch unter Druck nicht.",
        "Flexible Modelle für ältere Mitarbeiter wurden beibehalten.",
        "Generationenmix hat in der Krise Stabilität gegeben.",
    ],
    "arbeitsbedingungen": [
        "Büro und Ausstattung wurden trotz Einsparungen nicht verschlechtert.",
        "Moderne Hardware bleibt Standard – kein Rückschritt.",
        "Ergonomische Arbeitsplätze blieben erhalten, auch im Homeoffice.",
        "Physische Arbeitsbedingungen als Konstante in turbulenten Zeiten.",
        "Investitionen in Infrastruktur wurden priorisiert – kluge Entscheidung.",
        "Arbeitsbedingungen sind eine der Stärken, die nie in Frage gestellt wurden.",
    ],
    "gleichberechtigung": [
        "Diversity-Commitment blieb auch in der Krise unangetastet – respektabel.",
        "Gehaltsgleichheit wird weiter aktiv überprüft.",
        "Frauen in Führungspositionen wurden nicht reduziert in der Restrukturierung.",
        "Inklusion ist ein echter Wert und kein PR-Thema.",
        "LGBTQ+-Unterstützung blieb konstant durch alle Phasen.",
        "Gleichberechtigung ist eine der verlässlichsten Stärken des Unternehmens.",
    ],
}

CANDIDATE_TITEL_POOL = [
    "Bewerbungsprozess während Unternehmensumbruch", "Interview in unsicherer Phase",
    "Transparenter Prozess trotz interner Krise", "Professionelles Gespräch, ehrliche Antworten",
    "Langer Prozess durch interne Restrukturierung", "Eindruck vom Unternehmen im Wandel",
    "Bewerbung auf neugeschaffene Stelle nach Krise", "Vorstellungsgespräch mit neuem Management",
    "Positiver Eindruck trotz bekannter Krisengeschichte", "Ehrlicher Umgang mit Vergangenheit",
    "Schneller Prozess in der Erholungsphase", "Assessment in transformiertem Unternehmen",
    "Interview – Unternehmen gibt sich transparent", "Gutes Gespräch, Zukunftsperspektive unklar",
    "Prozess professionell, Fragen zur Stabilität offen",
]

STELLENBESCHREIBUNG_POOL = [
    "Bewerbung auf eine Ingenieurstelle nach bekannter Restrukturierungsphase des Unternehmens.",
    "Interview verlief sehr offen – HR war ehrlich über die vergangenen Herausforderungen.",
    "Neues Management hat frischen Wind – im Gespräch sehr motivierend.",
    "Prozess war länger als erwartet, intern noch viel in Bewegung.",
    "Gespräch mit Team und zukünftigem Vorgesetzten sehr positiv.",
    "Unternehmen befindet sich in Erholungsphase – interessanter Zeitpunkt einzusteigen.",
    "Bewerbungsunterlagen sehr schnell gesichtet, Rückmeldung kam prompt.",
    "Mehrere Runden mit verschiedenen Stakeholdern – gründlicher Prozess.",
    "HR kommunizierte offen über aktuelle Transformation – das hat Vertrauen geschaffen.",
    "Technisches Interview sehr kompetent, Soft-Skills-Runde etwas unstrukturiert.",
]

CANDIDATE_VERBESSERUNG_POOL = [
    "Mehr Klarheit über die Zukunftsstrategie während des Gesprächs wäre hilfreich.",
    "Transparenz über die vergangene Krise war gut – bitte beibehalten.",
    "Zeitplan des Prozesses klarer kommunizieren.",
    "Gehaltsrahmen früher besprechen – spart Zeit auf beiden Seiten.",
    "Mehr Einblick in das neue Management und seine Pläne.",
    "Feedback nach Assessment wäre auch bei Zusage hilfreich.",
    "Virtuelle und physische Interviewoptionen flexibler gestalten.",
    "Rückmeldung nach Gespräch kam etwas spät – 2 Wochen ist lang.",
    "Mehr Informationen über die neue Unternehmenskultur vorab.",
    "Nachfolgegespräch mit zukünftigem Team wäre wünschenswert gewesen.",
]

STATUS_EMPLOYEE = ["Angestellt", "Ex-Angestellt", "Angestellt", "Angestellt", "Ex-Angestellt"]
STATUS_CANDIDATE = ["Bewerber", "Bewerber", "Bewerber"]


def make_employee(company_id: int, period: str) -> dict:
    lo, hi = EMP_RANGES[period]
    base = random.gauss((lo + hi) / 2, 0.35)
    base = max(lo, min(hi, base))

    if period == "early":
        date = date_between(START, datetime(2022, 12, 31))
        gut_pool = GUT_POOL_EARLY
        schlecht_pool = SCHLECHT_POOL_EARLY
    elif period == "mid":
        date = date_between(datetime(2023, 1, 1), datetime(2023, 12, 31))
        gut_pool = GUT_POOL_CRISIS
        schlecht_pool = SCHLECHT_POOL_CRISIS
    elif period == "late":
        date = date_between(datetime(2024, 1, 1), datetime(2024, 12, 31))
        gut_pool = GUT_POOL_RECOVERY
        schlecht_pool = SCHLECHT_POOL_RECOVERY
    else:  # recent
        date = date_between(datetime(2025, 1, 1), END)
        gut_pool = GUT_POOL_RECOVERY
        schlecht_pool = SCHLECHT_POOL_RECOVERY

    cats = {cat: rand_rating(base + CAT_OFFSETS[cat]) for cat in EMPLOYEE_CATS}
    avg = round(sum(cats.values()) / len(cats), 2)

    row = {
        "company_id": company_id,
        "titel": random.choice(JOB_TITLES),
        "status": random.choice(STATUS_EMPLOYEE),
        "datum": date,
        "durchschnittsbewertung": avg,
        "gerundete_durchschnittsbewertung": round(round(avg * 2) / 2, 1),
        "jobbeschreibung": random.choice(JOB_TITLES) + " im Bereich Transformation & Operations.",
        "gut_am_arbeitgeber_finde_ich": random.choice(gut_pool),
        "schlecht_am_arbeitgeber_finde_ich": random.choice(schlecht_pool),
        "verbesserungsvorschlaege": random.choice(VERBESSERUNG_POOL),
    }
    for cat in EMPLOYEE_CATS:
        row[f"sternebewertung_{cat}"] = cats[cat]
        row[cat] = random.choice(TOPIC_TEXTS[cat])
    return row


def make_candidate(company_id: int, period: str) -> dict:
    lo, hi = CAND_RANGES[period]
    base = random.gauss((lo + hi) / 2, 0.35)
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
        supabase.table("employee").insert(employees[i:i + batch]).execute()
        print(f"  Inserted employees {i+1}–{min(i+batch, len(employees))}")

    # Build candidate records: 66 per year × 4 years = 264 total
    candidates = []
    for period in ("early", "mid", "late", "recent"):
        for _ in range(66):
            candidates.append(make_candidate(company_id, period))

    print(f"Inserting {len(candidates)} candidate reviews ...")
    for i in range(0, len(candidates), batch):
        supabase.table("candidates").insert(candidates[i:i + batch]).execute()
        print(f"  Inserted candidates {i+1}–{min(i+batch, len(candidates))}")

    print(f"\nDone! Company: {COMPANY_NAME} (id={company_id})")
    print(f"  Employee reviews: {len(employees)}")
    print(f"  Candidate reviews: {len(candidates)}")


if __name__ == "__main__":
    main()
