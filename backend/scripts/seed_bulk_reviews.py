"""
Bulk seed: adds ~500 employee + ~150 candidate reviews per Demo company,
all with ratings in the "gut bis akzeptabel" range (3.0–4.5).

Supabase IDs: Demo 1 = 10, Demo 2 = 17, Demo 3 = 18

Run from the backend directory: python scripts/seed_bulk_reviews.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import get_supabase_client
from datetime import datetime, timedelta
import random

random.seed(2025)
supabase = get_supabase_client()

START = datetime(2022, 1, 1)
END   = datetime(2025, 4, 30)

# ── Helpers ───────────────────────────────────────────────────────────────────

def rand_rating(mu, sigma=0.5, lo=1.0, hi=5.0):
    return round(max(lo, min(hi, random.gauss(mu, sigma))), 2)

def rand_date() -> str:
    delta = (END - START).days
    return (START + timedelta(days=random.randint(0, delta))).date().isoformat()

# ── Text pools (gut bis akzeptabel) ──────────────────────────────────────────

GUT_POOL = [
    "Das Team ist hilfsbereit und der Zusammenhalt stimmt.",
    "Flexible Arbeitszeiten und gute Homeoffice-Möglichkeiten.",
    "Interessante Aufgaben mit echtem Gestaltungsspielraum.",
    "Offene Fehlerkultur und konstruktives Miteinander.",
    "Regelmäßige Weiterbildungen werden aktiv unterstützt.",
    "Faire Bezahlung mit guten Sozialleistungen.",
    "Modernes Büro, gute technische Ausstattung.",
    "Flache Hierarchien ermöglichen kurze Entscheidungswege.",
    "Gute Work-Life-Balance, Urlaub kein Problem.",
    "Transparente Kommunikation aus dem Management.",
    "Stabiles Unternehmen mit klarer Zukunftsperspektive.",
    "Kollegenzusammenhalt ist auf einem hohen Niveau.",
    "Führungskräfte geben konstruktives Feedback.",
    "Sinnvolle Aufgaben mit echtem Business-Impact.",
    "Gutes Onboarding, man fühlt sich vom ersten Tag willkommen.",
    "Nachhaltigkeitsprojekte werden ernsthaft vorangetrieben.",
    "Betriebliche Altersvorsorge und Jobticket sind gute Extras.",
    "Regelmäßige Teamevents stärken den Zusammenhalt.",
    "Vertrauensarbeitszeit – man wird als Erwachsener behandelt.",
    "Entwicklungsgespräche finden regelmäßig statt.",
    "Gehalt ist marktgerecht und wird fair verhandelt.",
    "Gute Kantine mit gesunden Optionen.",
    "Karrieremöglichkeiten sind vorhanden und transparent.",
    "Vorgesetzte sind ansprechbar und unterstützen aktiv.",
    "Gute ÖPNV-Anbindung und Fahrradleasing als Option.",
]

SCHLECHT_POOL = [
    "Interne Kommunikation zwischen Abteilungen könnte besser sein.",
    "Beförderungsprozesse sind nicht immer transparent.",
    "Meetings könnten kürzer und fokussierter sein.",
    "Gehalt liegt leicht unter dem Marktdurchschnitt.",
    "Homeoffice-Regelung hat sich mehrfach geändert.",
    "Bürokratie bei kleinen Entscheidungen bremst manchmal.",
    "Parkplatzsituation ist schwierig.",
    "Technische Systeme sind teilweise veraltet.",
    "Feedback-Gespräche finden nicht immer regelmäßig statt.",
    "Abteilungsübergreifende Zusammenarbeit hat Potenzial.",
    "Weiterbildungsbudget könnte großzügiger sein.",
    "Überstunden fallen gelegentlich an.",
    "Karrierepfade sind nicht immer klar definiert.",
    "Klimaanlage im Sommer ist oft Diskussionsthema.",
    "Fluktuation in manchen Teams ist etwas hoch.",
]

VERBESSERUNG_POOL = [
    "Mehr Transparenz bei Gehaltsstrukturen.",
    "Strukturiertere Mitarbeiterjahresgespräche.",
    "Kürzere, effizientere Meetings durch klare Agenda.",
    "Mehr Weiterbildungsbudget pro Mitarbeiter.",
    "Bessere abteilungsübergreifende Kommunikation.",
    "Modernisierung einzelner IT-Systeme.",
    "Klarere Karrierepfade kommunizieren.",
    "Flexiblere Teilzeitmodelle auch für Führungskräfte.",
    "Mehr Einbindung der Mitarbeiter bei Entscheidungen.",
    "Regelmäßigere All-Hands-Meetings einführen.",
    "Homeoffice-Budget für ergonomische Ausstattung.",
    "Stärkere Förderung von Frauen in Führungspositionen.",
    "Mentoring-Programm für neue Mitarbeiter aufbauen.",
    "Feedbackkultur weiter stärken.",
    "Ausbau des betrieblichen Gesundheitsmanagements.",
]

TOPIC_TEXT_POOL = {
    "arbeitsatmosphaere": [
        "Offene und freundliche Atmosphäre, man hilft sich gegenseitig.",
        "Angenehmes Klima, gelegentlich Druck aber grundsätzlich positiv.",
        "Wertschätzende Atmosphäre, Erfolge werden anerkannt.",
        "Team hält zusammen, auch in stressigen Phasen.",
        "Entspannte Arbeitsatmosphäre mit kurzen Entscheidungswegen.",
    ],
    "image": [
        "Bekannte Marke, man ist gerne Teil davon.",
        "Guter Ruf in der Branche, hilft bei Kundenkontakten.",
        "Angesehener Arbeitgeber in der Region.",
        "Image nach außen sehr solide und professionell.",
        "Starke Marke, die Stabilität ausstrahlt.",
    ],
    "work_life_balance": [
        "Gute Balance, Überstunden sind eher die Ausnahme.",
        "Flexible Gleitzeit und echte Homeoffice-Option.",
        "Urlaub kann problemlos genommen werden.",
        "Keine Erwartung zur Erreichbarkeit außerhalb der Arbeitszeit.",
        "Teilzeitmodelle sind möglich und werden akzeptiert.",
    ],
    "karriere_weiterbildung": [
        "Klarer Karrierepfad mit definierten Meilensteinen.",
        "Weiterbildungsbudget vorhanden und gut nutzbar.",
        "Interne Beförderungen werden bevorzugt.",
        "Zugang zu Online-Lernplattformen und Konferenzen.",
        "Mentoring durch erfahrene Kollegen wird gefördert.",
    ],
    "gehalt_sozialleistungen": [
        "Marktgerechtes Gehalt mit fairen Boni.",
        "Gute Sozialleistungen: Altersvorsorge, Jobticket, Essenszuschuss.",
        "Transparente Vergütungsstruktur.",
        "Jahresbonus ist fair kalkuliert.",
        "Gehaltsverhandlung wird ernst genommen.",
    ],
    "kollegenzusammenhalt": [
        "Starker Zusammenhalt, man unterstützt sich.",
        "Teamevents stärken das Miteinander.",
        "Neue Kollegen werden gut integriert.",
        "Auch remote bleibt der Kontakt durch regelmäßige Calls gut.",
        "Vertrauen ist die Basis der Zusammenarbeit.",
    ],
    "umwelt_sozialbewusstsein": [
        "Nachhaltigkeitsziele sind konkret und messbar.",
        "Soziales Engagement durch Freiwilligentage.",
        "CO2-Neutralität wird aktiv angestrebt.",
        "Fahrradleasing und ÖPNV-Ticket zeigen ökologisches Bewusstsein.",
        "Energieeffizienz wird im Büroalltag gelebt.",
    ],
    "vorgesetztenverhalten": [
        "Führung auf Augenhöhe mit konstruktivem Feedback.",
        "Vertrauen in die Selbstständigkeit der Mitarbeiter.",
        "Regelmäßige 1:1s und klare Zielvereinbarungen.",
        "Lob und Kritik werden ausgewogen kommuniziert.",
        "Coaching-Ansatz statt Mikromanagement.",
    ],
    "kommunikation": [
        "Transparente Updates aus dem Management.",
        "Wöchentliche Stand-ups halten alle informiert.",
        "Direkte Kommunikation wird erwartet und gelebt.",
        "Regelmäßige All-Hands-Meetings geben Orientierung.",
        "Feedback-Kanäle für Ideen sind vorhanden und werden genutzt.",
    ],
    "interessante_aufgaben": [
        "Abwechslungsreiche Projekte mit echtem Mehrwert.",
        "Technisch herausfordernde Aufgaben, die fordern.",
        "Eigene Ideen können eingebracht und umgesetzt werden.",
        "Ownership über Features und Produkte.",
        "Interdisziplinäre Projekte fördern breites Lernen.",
    ],
    "umgang_mit_aelteren_kollegen": [
        "Erfahrung wird respektiert und aktiv eingebunden.",
        "Generationenübergreifende Zusammenarbeit funktioniert gut.",
        "Keine Altersdiskriminierung wahrnehmbar.",
        "Wissenstransfer zwischen Jung und Alt ist strukturiert.",
        "Teilzeitmodelle für ältere Kollegen sind vorhanden.",
    ],
    "arbeitsbedingungen": [
        "Ergonomische Arbeitsplätze, moderne Hardware.",
        "Gute Büroausstattung und ruhige Arbeitsbereiche.",
        "Home-Office-Ausstattung wird unterstützt.",
        "Saubere Küche und angenehme Gemeinschaftsbereiche.",
        "Gute ÖPNV-Anbindung, Fahrradabstellplätze vorhanden.",
    ],
    "gleichberechtigung": [
        "Diversity und Inklusion werden aktiv gelebt.",
        "Frauen in Führungspositionen sind sichtbar.",
        "Gehaltsgleichheit wird überprüft und sichergestellt.",
        "LGBTQ+-freundliche Unternehmenskultur.",
        "Chancengleichheit unabhängig von Herkunft und Hintergrund.",
    ],
}

CANDIDATE_TITEL_POOL = [
    "Professioneller Bewerbungsprozess", "Schnelle und transparente Kommunikation",
    "Angenehmes Vorstellungsgespräch", "Strukturierter Auswahlprozess",
    "Gute Erfahrung als Bewerber", "Effizientes Interview-Verfahren",
    "Wertschätzende Behandlung im Prozess", "Klare Kommunikation über nächste Schritte",
    "Interview verlief professionell", "Angenehme Atmosphäre im Gespräch",
    "Faire technische Aufgabe", "Schnelle Rückmeldung nach dem Gespräch",
    "Gut vorbereitete Gesprächspartner", "Transparenter Prozess mit fairem Feedback",
    "Angemessene Anzahl an Runden",
]

STELLENBESCHREIBUNG_POOL = [
    "Bewerbung auf eine Fachstelle mit gut strukturiertem Prozess.",
    "Zwei Runden: HR-Interview und Fachgespräch – überschaubar und effizient.",
    "Online-Test gefolgt von einem persönlichen Gespräch vor Ort.",
    "Video-Interview war gut vorbereitet, technische Fragen fair.",
    "Gesamter Prozess dauerte drei Wochen – angemessen.",
    "Assessment Center mit klaren Aufgaben und kompetenten Beobachtern.",
    "Schnelles erstes Gespräch, danach zügige Entscheidung.",
    "Bewerbung auf eine Führungsposition mit mehrstufigem Verfahren.",
    "Fachinterview und Kulturfit-Gespräch gut kombiniert.",
    "Transparente Kommunikation über Gehalt und Rolle von Anfang an.",
]

CANDIDATE_VERBESSERUNG_POOL = [
    "Feedback nach Gespräch etwas früher wäre hilfreich.",
    "Zeitplanung könnte transparenter kommuniziert werden.",
    "Mehr Infos über Unternehmenskultur vorab wären schön.",
    "Gehaltsrahmen früher ansprechen.",
    "Weniger Runden oder gebündelter wäre effizienter.",
    "HR war gut erreichbar – bitte so beibehalten.",
    "Mehr Einblick in den Arbeitsalltag, z.B. Schnuppertag.",
    "Konstruktives Feedback auch bei Absage wäre wertvoll.",
    "Technik für Video-Interviews vorab testen.",
    "Proaktive Updates bei Verzögerungen im Prozess.",
]

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

# Balanced offsets — alle Kategorien nahe 0, leicht positiv
BALANCED_CAT_OFFSETS = {
    "arbeitsatmosphaere": +0.1, "image": +0.1, "work_life_balance": +0.1,
    "karriere_weiterbildung": 0.0, "gehalt_sozialleistungen": 0.0,
    "kollegenzusammenhalt": +0.1, "umwelt_sozialbewusstsein": +0.1,
    "vorgesetztenverhalten": 0.0, "kommunikation": 0.0,
    "interessante_aufgaben": +0.1, "umgang_mit_aelteren_kollegen": 0.0,
    "arbeitsbedingungen": +0.1, "gleichberechtigung": +0.1,
}

BALANCED_CAND_OFFSETS = {
    "erklaerung_der_weiteren_schritte": +0.1, "zufriedenstellende_reaktion": +0.1,
    "vollstaendigkeit_der_infos": 0.0, "zufriedenstellende_antworten": +0.1,
    "angenehme_atmosphaere": +0.2, "professionalitaet_des_gespraechs": +0.1,
    "wertschaetzende_behandlung": +0.1, "erwartbarkeit_des_prozesses": 0.0,
    "zeitgerechte_zu_oder_absage": 0.0, "schnelle_antwort": +0.1,
}

JOB_TITLES = [
    "Software Engineer", "Senior Analyst", "Projektmanager", "Data Scientist",
    "HR Manager", "Controller", "DevOps Engineer", "UX Designer",
    "Marketing Manager", "Vertriebsleiter", "Scrum Master", "Technical Lead",
    "Kundenberater", "Business Analyst", "Backend Developer", "Frontend Developer",
    "QA Engineer", "Einkäufer", "Nachhaltigkeitsmanager", "Compliance Officer",
    "Operations Manager", "Produktmanager", "Qualitätsmanager", "IT-Architekt",
]

STATUS_EMPLOYEE = ["Angestellt", "Ex-Angestellt", "Angestellt", "Angestellt", "Ex-Angestellt"]
STATUS_CANDIDATE = ["Bewerber", "Bewerber", "Bewerber"]


def make_employee(company_id: int) -> dict:
    base = random.uniform(3.2, 4.5)
    cats = {cat: rand_rating(base + BALANCED_CAT_OFFSETS[cat]) for cat in EMPLOYEE_CATS}
    avg = round(sum(cats.values()) / len(cats), 2)
    row = {
        "company_id": company_id,
        "titel": random.choice(JOB_TITLES),
        "status": random.choice(STATUS_EMPLOYEE),
        "datum": rand_date(),
        "durchschnittsbewertung": avg,
        "gerundete_durchschnittsbewertung": round(round(avg * 2) / 2, 1),
        "jobbeschreibung": random.choice(JOB_TITLES) + " in der Produktentwicklung.",
        "gut_am_arbeitgeber_finde_ich": random.choice(GUT_POOL),
        "schlecht_am_arbeitgeber_finde_ich": random.choice(SCHLECHT_POOL),
        "verbesserungsvorschlaege": random.choice(VERBESSERUNG_POOL),
    }
    for cat in EMPLOYEE_CATS:
        row[f"sternebewertung_{cat}"] = cats[cat]
        row[cat] = random.choice(TOPIC_TEXT_POOL[cat])
    return row


def make_candidate(company_id: int) -> dict:
    base = random.uniform(3.3, 4.5)
    cats = {cat: rand_rating(base + BALANCED_CAND_OFFSETS[cat]) for cat in CANDIDATE_CATS}
    avg = round(sum(cats.values()) / len(cats), 2)
    row = {
        "company_id": company_id,
        "titel": random.choice(CANDIDATE_TITEL_POOL),
        "status": random.choice(STATUS_CANDIDATE),
        "datum": rand_date(),
        "durchschnittsbewertung": avg,
        "gerundete_durchschnittsbewertung": round(round(avg * 2) / 2, 1),
        "stellenbeschreibung": random.choice(STELLENBESCHREIBUNG_POOL),
        "verbesserungsvorschlaege": random.choice(CANDIDATE_VERBESSERUNG_POOL),
    }
    for cat in CANDIDATE_CATS:
        row[f"sternebewertung_{cat}"] = cats[cat]
    return row


def seed_company(company_id: int, name: str, n_emp: int = 500, n_cand: int = 150):
    print(f"\n── {name} (id={company_id}) ──")

    employees = [make_employee(company_id) for _ in range(n_emp)]
    print(f"Inserting {n_emp} employee reviews ...")
    batch = 50
    for i in range(0, len(employees), batch):
        supabase.table("employee").insert(employees[i:i + batch]).execute()
        print(f"  {i+batch if i+batch < n_emp else n_emp}/{n_emp}", end="\r")
    print(f"  {n_emp}/{n_emp} employees done")

    candidates = [make_candidate(company_id) for _ in range(n_cand)]
    print(f"Inserting {n_cand} candidate reviews ...")
    for i in range(0, len(candidates), batch):
        supabase.table("candidates").insert(candidates[i:i + batch]).execute()
        print(f"  {i+batch if i+batch < n_cand else n_cand}/{n_cand}", end="\r")
    print(f"  {n_cand}/{n_cand} candidates done")


def main():
    # Supabase IDs der Demo-Firmen
    companies = [
        (10, "Demo 1"),
        (17, "Demo 2"),
        (18, "Demo 3"),
    ]
    for company_id, name in companies:
        seed_company(company_id, name, n_emp=500, n_cand=150)

    print("\n✓ Fertig: 500 Mitarbeiter + 150 Bewerber pro Demo-Firma eingefügt.")


if __name__ == "__main__":
    main()
