"""
Tests der Erklärungsgenerierung: Kategorien-Matching, Scoring,
Erklärungstext, Coverage (In-Memory-Store, Demo-Firma 3).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.anomaly_detection_service import AnomalyParams, detect_and_persist
from services.explanation_service import (
    analyze_review_window,
    build_stock_move_candidates,
    compute_coverage,
    format_erklaerungstext,
    generate_explanations_for_company,
    get_explanations_grouped,
    match_event_categories,
    score_context_item,
)


# ── Ereigniskategorien (DE/EN) ───────────────────────────────────────────────

def test_match_event_categories_german():
    cats = match_event_categories("Konzern kündigt Stellenabbau und Sparprogramm an")
    assert "restrukturierung" in cats


def test_match_event_categories_english_and_umlaut_normalization():
    assert "restrukturierung" in match_event_categories("Company announces layoffs")
    # Umlaut-Transliteration: 'Übernahme' matcht Keyword 'uebernahme'
    assert "uebernahme" in match_event_categories("Übernahme durch Wettbewerber")
    assert "finanzlage_negativ" in match_event_categories("Gewinnwarnung veröffentlicht")


def test_match_event_categories_no_match():
    assert match_event_categories("Wetterbericht für Essen") == []


# ── Scoring ──────────────────────────────────────────────────────────────────

_ANOMALY = {
    "id": 999, "company_id": 3, "source": "employee",
    "dimension": "durchschnittsbewertung", "period": "2023-01",
    "window_start": "2022-11-01", "window_end": "2023-03-31",
    "direction": "fall", "magnitude": -0.46, "method": "pelt",
}

_WINDOW_TOPICS = {
    "review_count": 20,
    "topics": [
        {"topic": "Kommunikation", "frequency": 12, "avg_rating": 2.6},
        {"topic": "Arbeitsatmosphäre", "frequency": 9, "avg_rating": 2.7},
        {"topic": "Image", "frequency": 5, "avg_rating": 2.9},
        {"topic": "Gehalt & Sozialleistungen", "frequency": 0, "avg_rating": 3.0},
    ],
    "sentiment": {"positive": 5, "neutral": 5, "negative": 10},
}


def _item(titel, published, source_type="news"):
    return {"id": 1, "source_type": source_type, "provider": "manual",
            "titel": titel, "zusammenfassung": None, "url": "https://example.com/x",
            "published_at": published}


def test_score_temporal_peaks_at_anomaly_month():
    near = score_context_item(_item("Restrukturierung", "2023-01-15T00:00:00+00:00"),
                              _ANOMALY, _WINDOW_TOPICS)
    far = score_context_item(_item("Restrukturierung", "2022-11-05T00:00:00+00:00"),
                             _ANOMALY, _WINDOW_TOPICS)
    assert near["temporal_score"] == 1.0
    assert far["temporal_score"] < near["temporal_score"]
    assert near["score"] > far["score"]


def test_score_thematic_overlap_and_direction():
    scored = score_context_item(
        _item("Stellenabbau angekündigt", "2023-01-10T00:00:00+00:00"),
        _ANOMALY, _WINDOW_TOPICS,
    )
    # restrukturierung → topics enthalten Kommunikation/Arbeitsatmosphäre/Image (salient)
    assert "Kommunikation" in scored["matched_topics"]
    assert scored["thematic_score"] > 0.5
    assert scored["direction_consistent"] is True
    assert scored["score"] > 0.8


def test_score_direction_mismatch_penalized():
    rise_anomaly = dict(_ANOMALY, direction="rise")
    scored = score_context_item(
        _item("Stellenabbau angekündigt", "2023-01-10T00:00:00+00:00"),
        rise_anomaly, _WINDOW_TOPICS,
    )
    assert scored["direction_consistent"] is False
    assert scored["direction_score"] == 0.0


def test_score_unmatched_item_low():
    scored = score_context_item(
        _item("Wetterbericht", "2023-01-15T00:00:00+00:00"),
        _ANOMALY, _WINDOW_TOPICS,
    )
    assert scored["thematic_score"] == 0.0
    assert scored["matched_topics"] == []
    assert scored["score"] <= 0.5  # nur zeitliche Nähe + neutrale Richtung


def test_score_dimension_anomaly_direct_hit():
    dim_anomaly = dict(_ANOMALY, dimension="kommunikation")
    scored = score_context_item(
        _item("Führungswechsel: neuer CEO", "2023-01-15T00:00:00+00:00"),
        dim_anomaly, _WINDOW_TOPICS,
    )
    # fuehrungswechsel mappt u.a. auf Kommunikation = Anomalie-Dimension → voller Themen-Score
    assert scored["thematic_score"] == 1.0
    assert "Kommunikation" in scored["matched_topics"]


# ── Erklärungstext ───────────────────────────────────────────────────────────

def test_format_erklaerungstext_contains_source_and_month():
    item = _item("Demo 3 AG kündigt Restrukturierung an", "2023-01-12T08:00:00+00:00",
                 source_type="adhoc")
    scored = {"matched_topics": ["Kommunikation"], "direction_consistent": True}
    text = format_erklaerungstext(_ANOMALY, item, scored)
    assert "Januar 2023" in text
    assert "Ad-hoc-Meldung" in text
    assert "Demo 3 AG kündigt Restrukturierung an" in text
    assert "12.01.2023" in text
    assert "Kommunikation" in text
    assert "−0,46" in text


def test_format_erklaerungstext_dimension_grammar():
    dim_anomaly = dict(_ANOMALY, dimension="image", magnitude=0.4, direction="rise")
    item = _item("Rekordgewinn", "2023-01-12T08:00:00+00:00")
    text = format_erklaerungstext(dim_anomaly, item, {"matched_topics": []})
    assert "Anstieg der Dimension „Image“" in text


# ── Fenster-Analyse & Kursbewegungen (In-Memory-Demo) ────────────────────────

def test_analyze_review_window_demo3_crisis():
    result = analyze_review_window(3, "employee", "2023-01-01", "2023-03-31",
                                   with_sentiment=False)
    assert result["review_count"] > 10
    by_name = {t["topic"]: t for t in result["topics"]}
    assert by_name["Kommunikation"]["frequency"] > 0
    assert by_name["Kommunikation"]["avg_rating"] is not None


def test_build_stock_move_candidates_threshold():
    # Demo-Kurse fallen ~5-6 %/Monat → unterhalb der 10-%-Schwelle: keine Kandidaten
    candidates = build_stock_move_candidates(3, "2022-11-01", "2023-03-31")
    assert candidates == []


# ── Ende-zu-Ende + Coverage (DZ2) ────────────────────────────────────────────

def test_generate_and_coverage_demo3():
    detect_and_persist(3, "employee", "all", AnomalyParams())
    result = generate_explanations_for_company(3, with_sentiment=False)
    assert result["anomalies_processed"] > 0
    assert result["explanations_created"] > 0
    cov = result["coverage"]
    assert cov["total_anomalies"] == result["anomalies_processed"]
    assert 0 < cov["coverage"] <= 1.0

    grouped = get_explanations_grouped(3)
    overall = [g for g in grouped
               if g["anomaly"]["dimension"] == "durchschnittsbewertung"
               and g["anomaly"]["direction"] == "fall"]
    assert overall, "Gesamtbewertungs-Einbruch 2023 muss vorhanden sein"
    explanations = overall[0]["explanations"]
    assert explanations, "Der Einbruch 2023 muss erklärbar sein"
    top = explanations[0]
    assert top["rank"] == 1
    assert top["quelle"]["titel"]
    assert "Restrukturierung" in top["erklaerungstext"] or "Stellenabbau" in top["erklaerungstext"]
    # Ranking absteigend nach Score
    scores = [e["correspondence_score"] for e in explanations]
    assert scores == sorted(scores, reverse=True)


def test_coverage_empty_company():
    cov = compute_coverage(999_999)
    assert cov == {"total_anomalies": 0, "anomalies_with_explanation": 0, "coverage": None}
