"""
Kontextsammlung (2. Design-Zyklus): Orchestrierung der Quell-Adapter
und persistenter Zugriff auf externe Kontextdaten.

Externe Daten werden bewusst in der Datenbank persistiert
(Reproduzierbarkeit der Auswertung, Offline-Demo, keine wiederholten
API-Aufrufe bei jedem Dashboard-Aufruf). Aktualisierung erfolgt nur über
explizite Refresh-Aufrufe.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from database.supabase_client import get_supabase_client
from services.context_sources import eqs_source, manual_import, yfinance_source
from services.ticker_mapping import resolve_ticker_from_map

supabase = get_supabase_client()

ALL_SOURCES: Set[str] = {"news", "adhoc", "prices", "kpis", "recommendations"}
TICKER_SOURCES: Set[str] = {"news", "prices", "kpis", "recommendations"}  # benötigen companies.ticker


def get_company(company_id: int) -> Optional[Dict[str, Any]]:
    rows = supabase.table("companies").select("*").eq("id", company_id).execute().data or []
    return rows[0] if rows else None


def set_company_ticker(company_id: int, ticker: str, isin: Optional[str] = None) -> Dict[str, Any]:
    update: Dict[str, Any] = {"ticker": ticker.strip() or None}
    if isin is not None:
        update["isin"] = isin.strip() or None
    supabase.table("companies").update(update).eq("id", company_id).execute()
    company = get_company(company_id)
    if company is None:
        raise ValueError(f"Unternehmen {company_id} nicht gefunden")
    return company


def resolve_and_set_ticker(company_id: int) -> Dict[str, Any]:
    """
    Ticker automatisch anhand des Firmennamens auflösen und speichern:
    zuerst über die statische DAX/MDAX-Liste, dann über die
    Yahoo-Finance-Suche (Präferenz: deutsche Börse).
    """
    company = get_company(company_id)
    if company is None:
        raise ValueError(f"Unternehmen {company_id} nicht gefunden")

    if company.get("ticker"):
        return {"ticker": company["ticker"], "matched_name": company["name"],
                "source": "existing"}

    hit = resolve_ticker_from_map(company["name"])
    if hit is None:
        hit = yfinance_source.search_ticker(company["name"])
    if not hit or not hit.get("ticker"):
        raise LookupError(
            f"Kein Ticker für '{company['name']}' gefunden — "
            "vermutlich nicht börsennotiert. Ticker kann manuell gesetzt werden."
        )

    set_company_ticker(company_id, hit["ticker"])
    return {"ticker": hit["ticker"], "matched_name": hit.get("name") or company["name"],
            "source": hit.get("source", "map")}


def set_company_isin(company_id: int, isin: str) -> Dict[str, Any]:
    supabase.table("companies").update({"isin": isin.strip() or None}).eq("id", company_id).execute()
    company = get_company(company_id)
    if company is None:
        raise ValueError(f"Unternehmen {company_id} nicht gefunden")
    return company


def resolve_and_set_isin(company_id: int) -> Dict[str, Any]:
    """
    ISIN automatisch über die EQS-Meldungssuche auflösen und speichern.

    Die ISIN ist der Schlüssel für den trennscharfen Abruf von
    Ad-hoc-Mitteilungen; ohne sie bleibt diese Quelle leer.
    """
    company = get_company(company_id)
    if company is None:
        raise ValueError(f"Unternehmen {company_id} nicht gefunden")

    if company.get("isin"):
        return {"isin": company["isin"], "matched_name": company["name"], "source": "existing"}

    hit = eqs_source.resolve_isin(company["name"])
    if not hit or not hit.get("isin"):
        raise LookupError(
            f"Keine ISIN für '{company['name']}' gefunden — bei EQS liegen keine "
            "Meldungen unter diesem Namen vor (vermutlich nicht börsennotiert). "
            "Die ISIN kann manuell gesetzt werden."
        )

    set_company_isin(company_id, hit["isin"])
    return {"isin": hit["isin"], "matched_name": hit.get("name") or company["name"],
            "source": hit.get("source", "eqs")}


def _existing_urls(company_id: int) -> Set[str]:
    rows = supabase.table("context_items").select("url").eq("company_id", company_id).execute().data or []
    return {r["url"] for r in rows if r.get("url")}


def _insert_context_items(company_id: int, items: List[Dict[str, Any]]) -> int:
    """Items einfügen; Dedupe über URL (bzw. Titel+Datum, falls keine URL)."""
    known_urls = _existing_urls(company_id)
    existing = supabase.table("context_items").select("titel, published_at") \
        .eq("company_id", company_id).execute().data or []
    known_keys = {(r.get("titel"), str(r.get("published_at") or "")[:10]) for r in existing}

    inserted = 0
    for item in items:
        url = item.get("url")
        key = (item.get("titel"), str(item.get("published_at") or "")[:10])
        if url and url in known_urls:
            continue
        if not url and key in known_keys:
            continue
        row = dict(item)
        row["company_id"] = company_id
        row["created_at"] = datetime.now(timezone.utc).isoformat()
        supabase.table("context_items").insert(row).execute()
        inserted += 1
        if url:
            known_urls.add(url)
        known_keys.add(key)
    return inserted


def refresh_context(company_id: int, sources: Optional[Set[str]] = None,
                    years: int = 3) -> Dict[str, Any]:
    """
    Externe Quellen abrufen und persistieren.

    Rückgabe: {"fetched": {quelle: anzahl}, "errors": [meldungen]} — Fehler
    einzelner Quellen brechen den Refresh nicht ab.
    """
    requested = sources or set(ALL_SOURCES)
    unknown = requested - ALL_SOURCES
    if unknown:
        raise ValueError(f"Unbekannte Quellen: {', '.join(sorted(unknown))}")

    company = get_company(company_id)
    if company is None:
        raise ValueError(f"Unternehmen {company_id} nicht gefunden")

    ticker = company.get("ticker")
    if requested & TICKER_SOURCES and not ticker:
        raise ValueError(
            "Für dieses Unternehmen ist kein Ticker hinterlegt "
            "(PUT /api/context/company/{id}/ticker)"
        )

    fetched: Dict[str, Any] = {}
    errors: List[str] = []

    # Erhebungszeitraum für die historisch abfragbaren Quellen — identisch zum
    # Kurszeitraum, damit Ereignisse und Kursverlauf denselben Horizont abdecken.
    today = datetime.now(timezone.utc).date()
    window_end = today.isoformat()
    window_start = (today - timedelta(days=365 * years)).isoformat()

    if "news" in requested:
        try:
            items = yfinance_source.fetch_news(ticker)
            fetched["news"] = _insert_context_items(company_id, items)
        except Exception as e:
            fetched["news"] = 0
            errors.append(f"yfinance news: {e}")

    if "adhoc" in requested:
        try:
            # Ohne ISIN ist kein trennscharfer EQS-Abruf möglich; sie wird
            # einmalig aufgelöst und am Unternehmen persistiert.
            isin = company.get("isin")
            if not isin:
                try:
                    isin = resolve_and_set_isin(company_id)["isin"]
                except LookupError as e:
                    isin = None
                    errors.append(f"eqs adhoc: {e}")
            if isin:
                items, adhoc_errors = eqs_source.fetch_adhoc(
                    company["name"], isin, start=window_start, end=window_end,
                )
                fetched["adhoc"] = _insert_context_items(company_id, items)
                errors.extend(adhoc_errors)
            else:
                fetched["adhoc"] = 0
        except Exception as e:
            fetched["adhoc"] = 0
            errors.append(f"eqs adhoc: {e}")

    if "prices" in requested:
        try:
            result = yfinance_source.fetch_prices(ticker, years=years)
            rows = [
                {"company_id": company_id, **p}
                for p in result["prices"]
            ]
            for i in range(0, len(rows), 500):
                supabase.table("stock_prices").upsert(
                    rows[i:i + 500], on_conflict="company_id,date"
                ).execute()
            fetched["prices"] = len(rows)
        except Exception as e:
            fetched["prices"] = 0
            errors.append(f"yfinance prices: {e}")

    if "recommendations" in requested:
        try:
            recs = yfinance_source.fetch_recommendations(ticker)
            now_iso = datetime.now(timezone.utc).isoformat()
            for rec in recs:
                supabase.table("analyst_recommendations").upsert(
                    {"company_id": company_id, **rec, "fetched_at": now_iso},
                    on_conflict="company_id,month",
                ).execute()
            fetched["recommendations"] = len(recs)
        except Exception as e:
            fetched["recommendations"] = 0
            errors.append(f"yfinance recommendations: {e}")

    if "kpis" in requested:
        try:
            kpis = yfinance_source.fetch_kpis(ticker)
            row = {
                "company_id": company_id,
                **kpis,
                "raw": None,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            supabase.table("financial_kpis").upsert(row, on_conflict="company_id").execute()
            fetched["kpis"] = bool(any(
                kpis.get(k) is not None
                for k in ("market_cap", "trailing_pe", "revenue", "employees")
            ))
        except Exception as e:
            fetched["kpis"] = False
            errors.append(f"yfinance kpis: {e}")

    return {"fetched": fetched, "errors": errors}


def import_manual_items(company_id: int, raw: bytes, filename: str) -> Dict[str, Any]:
    """Manuelle CSV/JSON-Datei importieren (provider 'manual')."""
    if get_company(company_id) is None:
        raise ValueError(f"Unternehmen {company_id} nicht gefunden")
    items, errors = manual_import.parse_manual_file(raw, filename)
    inserted = _insert_context_items(company_id, items)
    return {
        "imported": inserted,
        "skipped": len(items) - inserted,
        "errors": errors,
    }


def get_context_items(company_id: int, start: Optional[str] = None,
                      end: Optional[str] = None,
                      source_type: Optional[str] = None) -> List[Dict[str, Any]]:
    q = supabase.table("context_items").select("*").eq("company_id", company_id)
    if start:
        q = q.gte("published_at", start)
    if end:
        q = q.lte("published_at", f"{end}T23:59:59+00:00" if len(end) == 10 else end)
    if source_type:
        q = q.eq("source_type", source_type)
    return q.order("published_at").execute().data or []


def get_stock_series(company_id: int, start: Optional[str] = None,
                     end: Optional[str] = None) -> Dict[str, Any]:
    """Kursverlauf: Tageswerte plus Monatsaggregat (letzter Close je Monat)."""
    q = supabase.table("stock_prices").select("*").eq("company_id", company_id)
    if start:
        q = q.gte("date", start)
    if end:
        q = q.lte("date", end)
    rows = q.order("date").execute().data or []

    monthly: Dict[str, float] = {}
    currency = None
    for row in rows:
        if row.get("close") is None:
            continue
        monthly[str(row["date"])[:7]] = float(row["close"])  # letzter Wert gewinnt
        currency = row.get("currency") or currency

    company = get_company(company_id) or {}
    return {
        "ticker": company.get("ticker"),
        "currency": currency,
        "prices": [
            {"date": r["date"], "close": float(r["close"])}
            for r in rows if r.get("close") is not None
        ],
        "monthly": [
            {"period": period, "close": round(close, 2)}
            for period, close in sorted(monthly.items())
        ],
    }


def get_analyst_recommendations(company_id: int) -> List[Dict[str, Any]]:
    """Analystenempfehlungen je Monat, aufsteigend sortiert."""
    rows = supabase.table("analyst_recommendations").select("*") \
        .eq("company_id", company_id).order("month").execute().data or []
    return rows


def get_financial_kpis(company_id: int) -> Optional[Dict[str, Any]]:
    rows = supabase.table("financial_kpis").select("*").eq("company_id", company_id).execute().data or []
    return rows[0] if rows else None


def get_context_overview(company_id: int) -> Dict[str, Any]:
    """Statusübersicht der Kontextdaten eines Unternehmens."""
    company = get_company(company_id)
    if company is None:
        raise ValueError(f"Unternehmen {company_id} nicht gefunden")

    items = supabase.table("context_items").select("source_type, created_at") \
        .eq("company_id", company_id).execute().data or []
    prices = supabase.table("stock_prices").select("id", count="exact") \
        .eq("company_id", company_id).execute()
    kpis = get_financial_kpis(company_id)

    last_refresh = max(
        [str(i.get("created_at")) for i in items if i.get("created_at")]
        + ([str(kpis["fetched_at"])] if kpis and kpis.get("fetched_at") else []),
        default=None,
    )

    return {
        "ticker": company.get("ticker"),
        "isin": company.get("isin"),
        "kpis": kpis,
        "news_count": sum(1 for i in items if i.get("source_type") == "news"),
        "adhoc_count": sum(1 for i in items if i.get("source_type") == "adhoc"),
        "price_points": prices.count or 0,
        "last_refresh": last_refresh,
    }
