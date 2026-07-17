"""
Tests der Kontextsammlung: Adapter-Normalisierung, manueller Import,
Dedupe beim Persistieren und Kursaggregation (In-Memory-Store).
"""

import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.context_sources.yfinance_source import (
    _normalize_news_item,
    fetch_kpis,
    fetch_recommendations,
)
from services.context_sources.manual_import import parse_manual_file
from services import context_service


# ── yfinance-News-Normalisierung ─────────────────────────────────────────────

def test_normalize_news_nested_schema():
    item = {
        "id": "abc",
        "content": {
            "title": "SAP kündigt Restrukturierung an",
            "summary": "Konzernumbau betrifft 8000 Stellen.",
            "pubDate": "2024-01-23T08:00:00Z",
            "canonicalUrl": {"url": "https://news.example.com/sap"},
        },
    }
    norm = _normalize_news_item(item)
    assert norm["titel"] == "SAP kündigt Restrukturierung an"
    assert norm["zusammenfassung"] == "Konzernumbau betrifft 8000 Stellen."
    assert norm["url"] == "https://news.example.com/sap"
    assert norm["published_at"].startswith("2024-01-23T08:00:00")
    assert norm["source_type"] == "news" and norm["provider"] == "yfinance"


def test_normalize_news_flat_legacy_schema():
    item = {
        "title": "Quartalszahlen veröffentlicht",
        "link": "https://news.example.com/q3",
        "providerPublishTime": 1706000400,
        "summary": "Umsatz gestiegen.",
    }
    norm = _normalize_news_item(item)
    assert norm["titel"] == "Quartalszahlen veröffentlicht"
    assert norm["url"] == "https://news.example.com/q3"
    assert norm["published_at"].startswith("2024-01-23")


def test_normalize_news_without_title_is_dropped():
    assert _normalize_news_item({"content": {"summary": "ohne Titel"}}) is None
    assert _normalize_news_item({}) is None


# ── KPI-Extraktion ───────────────────────────────────────────────────────────

def test_fetch_kpis_with_missing_fields():
    fake = MagicMock()
    fake.info = {"marketCap": 12_000_000_000, "currency": "EUR"}  # Rest fehlt
    with patch("services.context_sources.yfinance_source.yf.Ticker", return_value=fake):
        kpis = fetch_kpis("SAP.DE")
    assert kpis["market_cap"] == 12_000_000_000
    assert kpis["currency"] == "EUR"
    assert kpis["trailing_pe"] is None
    assert kpis["employees"] is None
    assert kpis["ticker"] == "SAP.DE"


def test_fetch_kpis_survives_info_failure():
    fake = MagicMock()
    type(fake).info = property(lambda self: (_ for _ in ()).throw(RuntimeError("401")))
    with patch("services.context_sources.yfinance_source.yf.Ticker", return_value=fake):
        kpis = fetch_kpis("SAP.DE")
    assert kpis["market_cap"] is None


# ── Analystenempfehlungen ────────────────────────────────────────────────────

def test_fetch_recommendations_resolves_relative_periods():
    import pandas as pd
    from datetime import datetime, timezone
    fake = MagicMock()
    fake.recommendations = pd.DataFrame([
        {"period": "0m", "strongBuy": 3, "buy": 19, "hold": 4, "sell": 0, "strongSell": 0},
        {"period": "-1m", "strongBuy": 3, "buy": 20, "hold": 4, "sell": 0, "strongSell": 0},
    ])
    with patch("services.context_sources.yfinance_source.yf.Ticker", return_value=fake):
        rows = fetch_recommendations("SAP.DE")
    assert len(rows) == 2
    now = datetime.now(timezone.utc)
    assert rows[0]["month"] == f"{now.year:04d}-{now.month:02d}"
    assert rows[0]["strong_buy"] == 3 and rows[0]["buy"] == 19
    # -1m liegt genau einen Monat zurück
    prev_idx = now.year * 12 + (now.month - 1) - 1
    assert rows[1]["month"] == f"{prev_idx // 12:04d}-{prev_idx % 12 + 1:02d}"


def test_fetch_recommendations_handles_failure():
    fake = MagicMock()
    type(fake).recommendations = property(lambda self: (_ for _ in ()).throw(RuntimeError("429")))
    with patch("services.context_sources.yfinance_source.yf.Ticker", return_value=fake):
        assert fetch_recommendations("SAP.DE") == []


def test_get_analyst_recommendations_demo3():
    rows = context_service.get_analyst_recommendations(3)
    assert len(rows) == 4
    months = [r["month"] for r in rows]
    assert months == sorted(months)
    # Demo 3: Erholungs-Story — Strong-Buy-Anteil steigt
    assert rows[-1]["strong_buy"] > rows[0]["strong_buy"]
    assert set(rows[0].keys()) >= {"month", "strong_buy", "buy", "hold", "sell", "strong_sell"}


# ── Manueller Import ─────────────────────────────────────────────────────────

CSV_OK = (
    "titel;datum;url;quelle_typ;zusammenfassung\n"
    "Restrukturierung angekündigt;2023-02-15;https://example.com/a;adhoc;Sparprogramm\n"
    "Neuer Standort;2023-05-10;;news;\n"
)

CSV_BAD = (
    "titel;datum;url;quelle_typ;zusammenfassung\n"
    ";2023-02-15;;adhoc;fehlender Titel\n"
    "Kaputtes Datum;15.02.2023;;news;\n"
    "Falscher Typ;2023-02-15;;pressemitteilung;\n"
)


def test_parse_manual_csv_ok():
    items, errors = parse_manual_file(CSV_OK.encode(), "events.csv")
    assert errors == []
    assert len(items) == 2
    assert items[0]["source_type"] == "adhoc"
    assert items[0]["published_at"].startswith("2023-02-15")
    assert items[1]["url"] is None and items[1]["zusammenfassung"] is None


def test_parse_manual_csv_reports_bad_rows():
    items, errors = parse_manual_file(CSV_BAD.encode(), "events.csv")
    assert items == []
    assert len(errors) == 3
    assert "Zeile 1" in errors[0] and "titel" in errors[0]
    assert "Zeile 2" in errors[1] and "datum" in errors[1]
    assert "Zeile 3" in errors[2] and "quelle_typ" in errors[2]


def test_parse_manual_json():
    raw = b'[{"titel": "Adhoc X", "datum": "2023-06-01", "quelle_typ": "adhoc"}]'
    items, errors = parse_manual_file(raw, "events.json")
    assert errors == [] and len(items) == 1
    assert items[0]["provider"] == "manual"


def test_parse_manual_json_invalid():
    items, errors = parse_manual_file(b"{nicht json", "events.json")
    assert items == [] and len(errors) == 1


# ── Persistierung / Dedupe (In-Memory-Store) ─────────────────────────────────

def _item(titel, url=None, date="2023-03-01"):
    return {
        "source_type": "news", "provider": "manual", "titel": titel,
        "zusammenfassung": None, "url": url,
        "published_at": f"{date}T00:00:00+00:00", "raw": None,
    }


def test_insert_context_items_dedupes_by_url_and_title():
    base = context_service._insert_context_items(1, [
        _item("A", url="https://example.com/dedupe-a"),
        _item("B"),
    ])
    assert base == 2
    again = context_service._insert_context_items(1, [
        _item("A", url="https://example.com/dedupe-a"),   # URL-Duplikat
        _item("B"),                                        # Titel+Datum-Duplikat
        _item("C", url="https://example.com/dedupe-c"),   # neu
    ])
    assert again == 1


def test_get_stock_series_monthly_last_close():
    series = context_service.get_stock_series(3)
    assert series["ticker"] == "DEMO3.DE"
    assert series["currency"] == "EUR"
    monthly = {m["period"]: m["close"] for m in series["monthly"]}
    # Demo-Daten: je Monat Kurse am 01. und 15. → Monatswert = Wert vom 15.
    assert "2023-07" in monthly
    # V-Form: Mitte 2023 deutlich unter Anfang 2022
    assert monthly["2023-07"] < monthly["2022-01"] - 10
    # Erholung bis Ende 2024
    assert monthly["2024-12"] > monthly["2023-07"] + 8


def test_refresh_requires_ticker():
    # Firma ohne Ticker anlegen und Refresh anfordern
    created = context_service.supabase.table("companies").insert({"name": "Ohne Ticker"}).execute()
    cid = created.data[0]["id"]
    try:
        try:
            context_service.refresh_context(cid, {"prices"})
            assert False, "sollte ValueError werfen"
        except ValueError as e:
            assert "Ticker" in str(e)
    finally:
        context_service.supabase.table("companies").delete().eq("id", cid).execute()


def test_context_overview_counts():
    overview = context_service.get_context_overview(3)
    assert overview["ticker"] == "DEMO3.DE"
    assert overview["news_count"] >= 5
    assert overview["adhoc_count"] >= 2
    assert overview["price_points"] >= 60
    assert overview["kpis"] is not None
    assert overview["kpis"]["market_cap"] == 1_800_000_000
