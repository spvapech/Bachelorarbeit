"""
Seed-Skript: Demo-Kontextdaten (2. Design-Zyklus) in die echte Datenbank.

Spiegelt die In-Memory-Demodaten (Kontext-Ereignisse, Aktienkurse,
Kennzahlen, Ticker) nach Supabase/Postgres, damit der DB-Modus ohne
yfinance-Zugriff demonstrierbar ist. Voraussetzungen:

1. Migration 006 ist angewendet (backend/migrations/006_*.sql)
2. Die Demo-Firmen existieren mit Reviews (scripts/seed_demo1..3.py)
3. .env mit SUPABASE_URL + SUPABASE_SERVICE_KEY

Aufruf (aus backend/):  uv run python scripts/seed_demo_context.py

Real-Daten-Pfad (statt Demo-Daten), z.B. für SAP:
1. Firma anlegen + Kununu-Export importieren (Dashboard → Import)
2. Ticker setzen:      PUT  /api/context/company/{id}/ticker   {"ticker": "SAP.DE"}
3. Kontext laden:      POST /api/context/company/{id}/refresh
4. Anomalien erkennen: POST /api/anomalies/company/{id}/detect  (oder Autodetect via GET)
5. Erklärungen:        POST /api/explanations/company/{id}/generate
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.supabase_client import get_supabase_client  # noqa: E402
from database.in_memory_store import (  # noqa: E402
    _DEMO_CONTEXT_ITEMS,
    _DEMO_STOCK_PRICES,
    _DEMO_FINANCIAL_KPIS,
    _DEMO_ANALYST_RECOMMENDATIONS,
)

DEMO_COMPANY_META = {
    1: {"name": "Demo 1", "ticker": "DEMO1.DE", "isin": "DE000DEMO101"},
    2: {"name": "Demo 2", "ticker": "DEMO2.DE", "isin": "DE000DEMO202"},
    3: {"name": "Demo 3", "ticker": "DEMO3.DE", "isin": "DE000DEMO303"},
}


def _strip_id(row: dict) -> dict:
    """SERIAL-ids nicht mitschreiben (Sequenzen sauber halten)."""
    return {k: v for k, v in row.items() if k != "id"}


def main() -> None:
    supabase = get_supabase_client()
    if type(supabase).__name__ == "InMemoryClient":
        print("Abbruch: keine Datenbank konfiguriert (.env mit SUPABASE_URL fehlt) — "
              "der In-Memory-Modus enthält die Demo-Kontextdaten bereits.")
        sys.exit(1)

    # Demo-Firmen-Namen → echte IDs auflösen
    id_map = {}
    for demo_id, meta in DEMO_COMPANY_META.items():
        rows = supabase.table("companies").select("id").eq("name", meta["name"]).execute().data or []
        if not rows:
            print(f"⚠ Firma '{meta['name']}' nicht gefunden — überspringe "
                  f"(zuerst scripts/seed_demo{demo_id}.py ausführen)")
            continue
        real_id = rows[0]["id"]
        id_map[demo_id] = real_id
        supabase.table("companies").update(
            {"ticker": meta["ticker"], "isin": meta["isin"]}
        ).eq("id", real_id).execute()
        print(f"✓ {meta['name']} (id {real_id}): Ticker {meta['ticker']} gesetzt")

    if not id_map:
        print("Keine Demo-Firmen gefunden — nichts zu tun.")
        sys.exit(1)

    # Kontext-Ereignisse (Dedupe über URL)
    inserted_items = 0
    for item in _DEMO_CONTEXT_ITEMS:
        real_id = id_map.get(item["company_id"])
        if real_id is None:
            continue
        existing = supabase.table("context_items").select("id") \
            .eq("company_id", real_id).eq("url", item["url"]).execute().data or []
        if existing:
            continue
        row = _strip_id(item)
        row["company_id"] = real_id
        supabase.table("context_items").insert(row).execute()
        inserted_items += 1
    print(f"✓ context_items: {inserted_items} neu eingefügt")

    # Aktienkurse (Upsert auf company_id+date)
    price_rows = []
    for price in _DEMO_STOCK_PRICES:
        real_id = id_map.get(price["company_id"])
        if real_id is None:
            continue
        row = _strip_id(price)
        row["company_id"] = real_id
        price_rows.append(row)
    for i in range(0, len(price_rows), 500):
        supabase.table("stock_prices").upsert(
            price_rows[i:i + 500], on_conflict="company_id,date"
        ).execute()
    print(f"✓ stock_prices: {len(price_rows)} Kurspunkte upserted")

    # Kennzahlen (Upsert auf company_id)
    for kpi in _DEMO_FINANCIAL_KPIS:
        real_id = id_map.get(kpi["company_id"])
        if real_id is None:
            continue
        row = _strip_id(kpi)
        row["company_id"] = real_id
        supabase.table("financial_kpis").upsert(row, on_conflict="company_id").execute()
    print(f"✓ financial_kpis: {len(id_map)} Datensätze upserted")

    # Analystenempfehlungen (Upsert auf company_id+month)
    rec_count = 0
    for rec in _DEMO_ANALYST_RECOMMENDATIONS:
        real_id = id_map.get(rec["company_id"])
        if real_id is None:
            continue
        row = _strip_id(rec)
        row["company_id"] = real_id
        supabase.table("analyst_recommendations").upsert(
            row, on_conflict="company_id,month"
        ).execute()
        rec_count += 1
    print(f"✓ analyst_recommendations: {rec_count} Monatswerte upserted")

    print("\nFertig. Nächste Schritte: Dashboard öffnen, Anomalien werden beim Laden "
          "der Timeline automatisch erkannt; danach 'Erklärungen generieren' anklicken.")


if __name__ == "__main__":
    main()
