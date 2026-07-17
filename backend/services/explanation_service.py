"""
Erklärungsgenerierung (2. Design-Zyklus).

Verknüpft erkannte Anomalien mit zeitlich und thematisch korrespondierenden
externen Ereignissen (News, Ad-hoc-Mitteilungen, Kursbewegungen) und erzeugt
je Kandidat einen nachvollziehbaren Erklärungsansatz mit Quellenbeleg.

Bewusste Designentscheidung: Als thematischer Matcher dient die
deterministische Keyword-Topic-Engine (services/topic_definitions.py) plus
Lexikon-Sentiment — beides ohne Modell-Download reproduzierbar. Die
Korrespondenz ist eine Plausibilisierung, keine Kausalaussage (vgl. Exposé
Abschnitt 2.8).

Scoring je Kontext-Ereignis:
    score = 0.4 * zeitliche Nähe + 0.4 * thematische Übereinstimmung
          + 0.2 * Richtungskonsistenz
"""

import re
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List, Optional

from database.supabase_client import get_supabase_client
from services.anomaly_detection_service import dimension_label, get_anomalies
from services.context_service import get_context_items, get_stock_series
from services.topic_definitions import (
    TOPIC_DEFINITIONS_BY_SOURCE,
    topic_for_dimension_key,
)

supabase = get_supabase_client()

# ---------------------------------------------------------------------------
# Ereigniskategorien: Finanzdomänen-Keywords (DE/EN) → betroffene
# Bewertungs-Topics + erwartete Richtung der Bewertungsveränderung
# ---------------------------------------------------------------------------

EVENT_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "restrukturierung": {
        "keywords": ["stellenabbau", "entlassung", "layoff", "restrukturierung",
                     "sparprogramm", "kurzarbeit", "werksschliessung", "standortschliessung",
                     "personalabbau", "abfindung", "sozialplan"],
        "topics": ["Arbeitsatmosphäre", "Kommunikation", "Image", "Umgang mit älteren Kollegen"],
        "expected_direction": "fall",
    },
    "finanzlage_negativ": {
        "keywords": ["gewinnwarnung", "profit warning", "umsatzrueckgang", "verlust",
                     "insolvenz", "prognose gesenkt", "senkt prognose", "abschreibung",
                     "gewinneinbruch"],
        "topics": ["Image", "Gehalt & Sozialleistungen"],
        "expected_direction": "fall",
    },
    "fuehrungswechsel": {
        "keywords": ["ceo", "vorstandsvorsitzende", "vorstandswechsel", "geschaeftsfuehrer",
                     "fuehrungswechsel", "management change", "verlaesst das unternehmen",
                     "neuer chef", "aufsichtsrat"],
        "topics": ["Vorgesetztenverhalten", "Kommunikation"],
        "expected_direction": None,
    },
    "uebernahme": {
        "keywords": ["uebernahme", "fusion", "merger", "acquisition", "zusammenschluss",
                     "kartellamt", "verkauf der sparte"],
        "topics": ["Image", "Kommunikation", "Arbeitsatmosphäre"],
        "expected_direction": None,
    },
    "verguetung": {
        "keywords": ["tarif", "gehaltserhoehung", "bonus", "streik", "warnstreik",
                     "tarifabschluss", "lohnerhoehung", "inflationsausgleich"],
        "topics": ["Gehalt & Sozialleistungen"],
        "expected_direction": None,
    },
    "arbeitsmodell": {
        "keywords": ["homeoffice", "remote", "rueckkehr ins buero", "return to office",
                     "praesenzpflicht", "vier-tage-woche", "arbeitszeitmodell"],
        "topics": ["Work-Life Balance", "Arbeitsbedingungen"],
        "expected_direction": None,
    },
    "wachstum_positiv": {
        "keywords": ["rekordgewinn", "umsatzplus", "expansion", "neueinstellung",
                     "auftragseingang", "gewinnzone", "rekordumsatz", "wachstum",
                     "neuer standort", "stellt ein", "investiert"],
        "topics": ["Image", "Karriere & Weiterbildung", "Arbeitsatmosphäre"],
        "expected_direction": "rise",
    },
}

_MONTHS_DE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
              "August", "September", "Oktober", "November", "Dezember"]

# Kursbewegungen ab dieser Monatsrendite werden als eigener Kontext-Kandidat geführt
STOCK_MOVE_THRESHOLD = 0.10

_SOURCE_TYPE_PHRASES = {
    "adhoc": "der Ad-hoc-Meldung",
    "news": "der Nachricht",
    "stock_move": "der Kursbewegung",
}

_sentiment_analyzer = None


def _get_sentiment_analyzer():
    """Lexikon-Sentiment lazy instanziieren (kein Modell-Download)."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        from models.sentiment_analyzer import SentimentAnalyzer
        _sentiment_analyzer = SentimentAnalyzer(mode="lexicon")
    return _sentiment_analyzer


def _normalize(text: str) -> str:
    """Kleinschreibung + Umlaut-Transliteration für robustes Keyword-Matching."""
    return (text.lower()
            .replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
            .replace("ß", "ss"))


def _month_label(period: str) -> str:
    y, m = int(period[:4]), int(period[5:7])
    return f"{_MONTHS_DE[m - 1]} {y}"


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Review-Analyse im Ereignisfenster
# ---------------------------------------------------------------------------

_EMPLOYEE_TEXT_FIELDS = [
    "gut_am_arbeitgeber_finde_ich", "schlecht_am_arbeitgeber_finde_ich",
    "verbesserungsvorschlaege",
    "arbeitsatmosphaere", "image", "work_life_balance", "karriere_weiterbildung",
    "gehalt_sozialleistungen", "kollegenzusammenhalt", "umwelt_sozialbewusstsein",
    "vorgesetztenverhalten", "kommunikation", "interessante_aufgaben",
    "umgang_mit_aelteren_kollegen", "arbeitsbedingungen", "gleichberechtigung",
]
_CANDIDATE_TEXT_FIELDS = ["titel", "stellenbeschreibung", "verbesserungsvorschlaege"]


def _review_text(review: Dict[str, Any], source: str) -> str:
    fields = _EMPLOYEE_TEXT_FIELDS if source == "employee" else _CANDIDATE_TEXT_FIELDS
    return " ".join(str(review.get(f) or "") for f in fields)


def analyze_review_window(company_id: int, source: str, window_start: str,
                          window_end: str, with_sentiment: bool = True) -> Dict[str, Any]:
    """
    Topic-Frequenzen, Durchschnittsbewertungen und Sentiment der Reviews
    im Ereignisfenster (Basis für die thematische Korrespondenz).
    """
    rows = (
        supabase.table(source).select("*")
        .eq("company_id", company_id)
        .gte("datum", window_start)
        .lte("datum", window_end)
        .execute().data or []
    )

    topic_defs = TOPIC_DEFINITIONS_BY_SOURCE[source]
    compiled = {
        name: [re.compile(k, re.IGNORECASE) for k in config["keywords"]]
        for name, config in topic_defs.items()
    }

    topics: List[Dict[str, Any]] = []
    for name, config in topic_defs.items():
        frequency = 0
        ratings: List[float] = []
        for review in rows:
            text = _review_text(review, source)
            if any(p.search(text) for p in compiled[name]):
                frequency += 1
            for field in config["rating_fields"]:
                value = review.get(field)
                if value is not None:
                    ratings.append(float(value))
        topics.append({
            "topic": name,
            "frequency": frequency,
            "avg_rating": round(mean(ratings), 2) if ratings else None,
        })

    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    if with_sentiment and rows:
        analyzer = _get_sentiment_analyzer()
        for review in rows:
            text = _review_text(review, source).strip()
            if not text:
                continue
            try:
                result = analyzer.analyze_sentiment(text[:2000])
                sentiment_counts[result.get("sentiment", "neutral")] += 1
            except Exception:
                sentiment_counts["neutral"] += 1

    return {
        "review_count": len(rows),
        "topics": sorted(topics, key=lambda t: -t["frequency"]),
        "sentiment": sentiment_counts,
    }


# ---------------------------------------------------------------------------
# Scoring: zeitliche + thematische Korrespondenz + Richtungskonsistenz
# ---------------------------------------------------------------------------

def match_event_categories(text: str) -> List[str]:
    """Ereigniskategorien, deren Keywords im (normalisierten) Text vorkommen."""
    haystack = _normalize(text)
    return [
        name for name, config in EVENT_CATEGORIES.items()
        if any(_normalize(k) in haystack for k in config["keywords"])
    ]


def score_context_item(item: Dict[str, Any], anomaly: Dict[str, Any],
                       window_topics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Korrespondenz-Score eines Kontext-Ereignisses zu einer Anomalie.

    Rückgabe: {"score", "temporal_score", "thematic_score", "direction_score",
               "matched_topics", "matched_categories", "direction_consistent"}
    """
    # 1) Ereigniskategorien im Titel + Zusammenfassung
    text = f"{item.get('titel') or ''} {item.get('zusammenfassung') or ''}"
    categories = match_event_categories(text)
    mapped_topics: List[str] = []
    expected_directions: List[Optional[str]] = []
    for cat in categories:
        mapped_topics.extend(EVENT_CATEGORIES[cat]["topics"])
        expected_directions.append(EVENT_CATEGORIES[cat]["expected_direction"])
    mapped_topics = list(dict.fromkeys(mapped_topics))  # dedupe, Reihenfolge stabil

    # 2) zeitliche Nähe zur Monatsmitte der Anomalie, normiert auf das Fenster
    published = _parse_dt(item.get("published_at"))
    window_start = _parse_dt(anomaly.get("window_start"))
    window_end = _parse_dt(anomaly.get("window_end"))
    anchor = _parse_dt(f"{anomaly['period']}-15T00:00:00+00:00")
    if published is None or anchor is None or window_start is None or window_end is None:
        temporal = 0.0
    else:
        half_span_days = max((window_end - window_start).days / 2, 1)
        distance_days = abs((published - anchor).days)
        temporal = max(0.0, 1.0 - distance_days / half_span_days)

    # 3) thematische Übereinstimmung: Anteil der gemappten Topics, die in den
    #    Reviews des Fensters tatsächlich vorkommen; direkte Treffer auf die
    #    Anomalie-Dimension zählen voll
    salient = {t["topic"] for t in window_topics.get("topics", []) if t["frequency"] > 0}
    overlap = [t for t in mapped_topics if t in salient]
    thematic = len(overlap) / len(mapped_topics) if mapped_topics else 0.0

    anomaly_topic = topic_for_dimension_key(anomaly.get("dimension", ""),
                                            anomaly.get("source", "employee"))
    if anomaly_topic and anomaly_topic in mapped_topics:
        thematic = 1.0
        if anomaly_topic not in overlap:
            overlap.append(anomaly_topic)

    # 4) Richtungskonsistenz (Kursbewegungen: gleiche Richtung wie die Anomalie)
    if item.get("source_type") == "stock_move":
        move_direction = item.get("_direction")
        direction_consistent = move_direction == anomaly.get("direction")
        direction = 1.0 if direction_consistent else 0.0
    elif expected_directions:
        known = [d for d in expected_directions if d is not None]
        if known:
            direction_consistent = anomaly.get("direction") in known
            direction = 1.0 if direction_consistent else 0.0
        else:
            direction_consistent = None  # neutral erwartete Richtung
            direction = 0.5
    else:
        direction_consistent = None
        direction = 0.5

    score = 0.4 * temporal + 0.4 * thematic + 0.2 * direction
    return {
        "score": round(score, 3),
        "temporal_score": round(temporal, 3),
        "thematic_score": round(thematic, 3),
        "direction_score": round(direction, 3),
        "matched_topics": overlap,
        "matched_categories": categories,
        "direction_consistent": direction_consistent,
    }


# ---------------------------------------------------------------------------
# Kursbewegungs-Kandidaten
# ---------------------------------------------------------------------------

def build_stock_move_candidates(company_id: int, window_start: str,
                                window_end: str) -> List[Dict[str, Any]]:
    """Auffällige Monatsrenditen im Fenster als synthetische Kontext-Kandidaten."""
    series = get_stock_series(company_id)
    monthly = series.get("monthly") or []
    if len(monthly) < 2:
        return []

    candidates: List[Dict[str, Any]] = []
    for prev, curr in zip(monthly, monthly[1:]):
        period = curr["period"]
        month_mid = f"{period}-15T00:00:00+00:00"
        if not (window_start <= f"{period}-15" <= window_end):
            continue
        if not prev["close"]:
            continue
        ret = (curr["close"] - prev["close"]) / prev["close"]
        if abs(ret) < STOCK_MOVE_THRESHOLD:
            continue
        sign = "+" if ret > 0 else "−"
        candidates.append({
            "id": None,
            "source_type": "stock_move",
            "provider": "derived",
            "titel": f"Kursbewegung {sign}{abs(ret) * 100:.1f} % im {_month_label(period)}",
            "zusammenfassung": (
                f"Der Aktienkurs veränderte sich von {prev['close']:.2f} auf "
                f"{curr['close']:.2f} {series.get('currency') or ''}".strip() + "."
            ),
            "url": None,
            "published_at": month_mid,
            "_direction": "rise" if ret > 0 else "fall",
            "_return": round(ret, 4),
        })
    return candidates


# ---------------------------------------------------------------------------
# Erklärungstext + Generierung
# ---------------------------------------------------------------------------

def format_erklaerungstext(anomaly: Dict[str, Any], item: Dict[str, Any],
                           scored: Dict[str, Any]) -> str:
    """Deutschsprachiger Erklärungssatz mit Quellenbeleg."""
    richtung = "Rückgang" if anomaly.get("direction") == "fall" else "Anstieg"
    dimension = anomaly.get("dimension", "")
    if dimension == "durchschnittsbewertung":
        dim = "Gesamtbewertung"
    else:
        dim = f"Dimension „{dimension_label(dimension)}“"
    monat = _month_label(anomaly["period"])
    magnitude = anomaly.get("magnitude")
    delta = ""
    if magnitude is not None:
        value = abs(float(magnitude))
        sign = "−" if anomaly.get("direction") == "fall" else "+"
        delta = f" ({sign}{value:.2f} Punkte)".replace(".", ",")

    phrase = _SOURCE_TYPE_PHRASES.get(item.get("source_type"), "dem Ereignis")
    published = _parse_dt(item.get("published_at"))
    datum = f" ({published.strftime('%d.%m.%Y')})" if published else ""

    text = (f"Der {richtung} der {dim} im {monat}{delta} fällt zeitlich mit "
            f"{phrase} „{item.get('titel')}“{datum} zusammen.")

    if scored.get("matched_topics"):
        text += (" Thematisch betroffene Bewertungsdimensionen: "
                 + ", ".join(scored["matched_topics"]) + ".")
    if scored.get("direction_consistent"):
        text += " Die Richtung der Veränderung ist konsistent mit dem Ereignistyp."
    return text


def _quelle(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_type": item.get("source_type"),
        "provider": item.get("provider"),
        "titel": item.get("titel"),
        "url": item.get("url"),
        "published_at": item.get("published_at"),
    }


def generate_explanations_for_anomaly(anomaly: Dict[str, Any], min_score: float = 0.2,
                                      top_n: int = 5,
                                      with_sentiment: bool = True) -> List[Dict[str, Any]]:
    """
    Erklärungsansätze für eine (persistierte) Anomalie erzeugen und speichern.
    Vorhandene Erklärungen der Anomalie werden ersetzt.
    """
    company_id = anomaly["company_id"]
    window_start = str(anomaly["window_start"])[:10]
    window_end = str(anomaly["window_end"])[:10]

    window_topics = analyze_review_window(
        company_id, anomaly.get("source", "employee"),
        window_start, window_end, with_sentiment=with_sentiment,
    )

    items = [
        i for i in get_context_items(company_id, window_start, window_end)
        if i.get("source_type") in ("news", "adhoc")
    ]
    items += build_stock_move_candidates(company_id, window_start, window_end)

    scored_items = []
    for item in items:
        scored = score_context_item(item, anomaly, window_topics)
        if scored["score"] >= min_score:
            scored_items.append((item, scored))
    scored_items.sort(key=lambda pair: -pair[1]["score"])
    scored_items = scored_items[:top_n]

    supabase.table("explanations").delete().eq("anomaly_id", anomaly["id"]).execute()

    evidence = {
        "review_count": window_topics["review_count"],
        "sentiment": window_topics["sentiment"],
        "top_topics": window_topics["topics"][:5],
    }

    stored: List[Dict[str, Any]] = []
    for rank, (item, scored) in enumerate(scored_items, start=1):
        row = {
            "anomaly_id": anomaly["id"],
            "context_item_id": item.get("id"),
            "rank": rank,
            "correspondence_score": scored["score"],
            "matched_topics": scored["matched_topics"],
            "direction_consistent": scored["direction_consistent"],
            "review_evidence": evidence,
            "erklaerungstext": format_erklaerungstext(anomaly, item, scored),
            "quelle": _quelle(item),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        res = supabase.table("explanations").insert(row).execute()
        stored.append((res.data or [row])[0])
    return stored


def generate_explanations_for_company(company_id: int, source: Optional[str] = None,
                                      method: Optional[str] = None,
                                      min_score: float = 0.2, top_n: int = 5,
                                      with_sentiment: bool = True) -> Dict[str, Any]:
    """Erklärungen für alle (gefilterten) Anomalien eines Unternehmens erzeugen."""
    anomalies = get_anomalies(company_id, source=source, method=method)
    created = 0
    for anomaly in anomalies:
        created += len(generate_explanations_for_anomaly(
            anomaly, min_score=min_score, top_n=top_n, with_sentiment=with_sentiment,
        ))
    return {
        "anomalies_processed": len(anomalies),
        "explanations_created": created,
        "coverage": compute_coverage(company_id, source=source, method=method),
    }


def get_explanations_grouped(company_id: int, source: Optional[str] = None,
                             method: Optional[str] = None) -> List[Dict[str, Any]]:
    """Anomalien mit ihren Erklärungen (auch leere Listen), sortiert nach Monat."""
    anomalies = get_anomalies(company_id, source=source, method=method)
    result = []
    for anomaly in anomalies:
        rows = (
            supabase.table("explanations").select("*")
            .eq("anomaly_id", anomaly["id"])
            .order("rank").execute().data or []
        )
        result.append({"anomaly": anomaly, "explanations": rows})
    return result


def compute_coverage(company_id: int, source: Optional[str] = None,
                     method: Optional[str] = None) -> Dict[str, Any]:
    """Erklärungsabdeckung (DZ2): Anteil der Anomalien mit ≥1 Erklärungsansatz."""
    grouped = get_explanations_grouped(company_id, source=source, method=method)
    total = len(grouped)
    covered = sum(1 for g in grouped if g["explanations"])
    return {
        "total_anomalies": total,
        "anomalies_with_explanation": covered,
        "coverage": round(covered / total, 3) if total else None,
    }
