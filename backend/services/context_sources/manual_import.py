"""
Manueller Import externer Ereignisse (CSV oder JSON).

Garantierter Fallback-Pfad der Kontextsammlung: Nachrichten und
Ad-hoc-Mitteilungen können recherchiert und als Datei importiert werden,
unabhängig von der Verfügbarkeit externer APIs.

CSV-Format (Delimiter ';' oder ','), Spalten:
    titel;datum;url;quelle_typ;zusammenfassung
JSON-Format: Array von Objekten mit denselben Schlüsseln.
`quelle_typ` ∈ {news, adhoc}; `datum` als ISO-Datum (z.B. 2023-02-15).
"""

import csv
import io
import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

VALID_SOURCE_TYPES = {"news", "adhoc"}
REQUIRED_FIELDS = {"titel", "datum", "quelle_typ"}


def _normalize_row(row: Dict[str, Any], row_no: int) -> Tuple[Dict[str, Any] | None, str | None]:
    data = {str(k).strip().lower(): (str(v).strip() if v is not None else "")
            for k, v in row.items() if k}

    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        return None, f"Zeile {row_no}: Pflichtfelder fehlen: {', '.join(missing)}"

    source_type = data["quelle_typ"].lower()
    if source_type not in VALID_SOURCE_TYPES:
        return None, (f"Zeile {row_no}: quelle_typ '{data['quelle_typ']}' ungültig "
                      f"(erlaubt: {', '.join(sorted(VALID_SOURCE_TYPES))})")

    try:
        published = datetime.fromisoformat(data["datum"].replace("Z", "+00:00")).isoformat()
    except ValueError:
        return None, f"Zeile {row_no}: datum '{data['datum']}' ist kein gültiges ISO-Datum"

    return {
        "source_type": source_type,
        "provider": "manual",
        "titel": data["titel"],
        "zusammenfassung": data.get("zusammenfassung") or None,
        "url": data.get("url") or None,
        "published_at": published,
        "raw": None,
    }, None


def parse_manual_file(raw: bytes, filename: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Datei parsen; Rückgabe (gültige Items, Fehlermeldungen je Zeile)."""
    text = raw.decode("utf-8-sig", errors="replace")
    rows: List[Dict[str, Any]]

    if filename.lower().endswith(".json"):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            return [], [f"JSON nicht lesbar: {e}"]
        if not isinstance(parsed, list):
            return [], ["JSON muss ein Array von Objekten sein"]
        rows = [r for r in parsed if isinstance(r, dict)]
    else:
        delimiter = ";" if text.count(";") >= text.count(",") else ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)

    items: List[Dict[str, Any]] = []
    errors: List[str] = []
    for i, row in enumerate(rows, start=1):
        item, error = _normalize_row(row, i)
        if error:
            errors.append(error)
        else:
            items.append(item)
    return items, errors
