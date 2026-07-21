"""
EQS/DGAP-Adapter für Ad-hoc-Mitteilungen und Corporate News.

EQS betreibt für das eigene Nachrichtenportal eine öffentlich erreichbare
REST-Schnittstelle (`/wp-json/eqsnews/v1/`). Sie wird hier gegenüber dem
RSS-Feed bevorzugt, weil sie die für den Anomalieabgleich entscheidenden
Eigenschaften mitbringt:

- Historie: Abfrage über `start_date`/`end_date` statt nur der letzten
  Meldungen — Voraussetzung, um zurückliegende Anomaliezeiträume überhaupt
  belegen zu können.
- Trennschärfe: Filterung über die ISIN statt über einen Namensabgleich im
  Freitext.
- Quellenbeleg: Die Detailansicht liefert je Meldung eine dauerhafte
  `share_url` sowie den deutschsprachigen Volltext.

Einschränkungen (in der Arbeit als Limitation zu führen): Die Schnittstelle
ist nicht offiziell dokumentiert und nicht versioniert; ihre Antwortstruktur
kann sich ändern. Jeder Fehler führt deshalb zu einer leeren Ergebnisliste
plus Fehlereintrag, nie zu einem Abbruch der Pipeline. Der manuelle Import
(manual_import.py) bleibt der garantierte Fallback-Pfad.
"""

import html
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

EQS_API_BASE = os.getenv("EQS_API_BASE", "https://www.eqs-news.com/wp-json/eqsnews/v1")

_TIMEOUT_SECONDS = 20
_USER_AGENT = "Mozilla/5.0 (compatible; BA-Kununu-Analyse/1.0)"
_PER_PAGE = 100          # von der Schnittstelle erzwungenes Maximum
_MAX_PAGES = 20          # Sicherheitsnetz gegen Endlosschleifen
_MAX_DETAIL_CALLS = 60   # Volltextabruf kostet je Meldung einen Request

# Kategorien der Schnittstelle → source_type in `context_items`.
#
# Bewusst nicht übernommen werden Stimmrechtsmitteilungen (PVR/NVR),
# Directors' Dealings (dd), Finanzterminankündigungen (AFR),
# Kapitalmarktinformationen (CMS) und Hauptversammlungsbekanntmachungen (AGM):
# Sie dominieren die Treffermenge — für Bayer 2022–2024 entfallen 65 von 73
# Meldungen allein auf PVR —, sind aber Formalmeldungen mit festem
# Meldeanlass. Als Erklärungskandidaten würden sie über die zeitliche Nähe
# scoren, ohne inhaltlich auf eine Bewertungsveränderung zu verweisen.
RELEVANT_CATEGORIES: Dict[str, str] = {
    "adhoc": "adhoc",          # Insiderinformationen nach Art. 17 MAR
    "corporate": "news",       # Unternehmensnachrichten / Pressemitteilungen
}

# Jede EQS-Meldung folgt demselben Aufbau: Kopfblock (Emittent, Schlagwort,
# Zeitstempel, Rechtshinweis), Meldungstext, Fußblock (Kontaktdaten,
# Verbreitungshinweis). Kopf- und Fußblock werden über ihre festen
# Schlusssätze abgeschnitten, statt einzelne Bausteine zu ersetzen — Letzteres
# ist auf dem zu einer Zeile normalisierten Volltext nicht trennscharf.
_HEADER_END = [
    re.compile(r"Für den Inhalt der Mitteilung ist der Emittent[^.]{0,80}verantwortlich\.", re.I),
    re.compile(r"übermittelt durch EQS[^.]{0,120}\.", re.I),
    re.compile(r"Veröffentlichung einer Insiderinformation[^.]{0,200}\.", re.I),
]
_FOOTER_START = [
    re.compile(r"Ende der (Ad-hoc-)?(Mitteilung|Pressemitteilung|Meldung)", re.I),
    re.compile(r"\bSprache:\s*Deutsch\b", re.I),
    re.compile(r"Die EQS Group (AG )?ist ein", re.I),
    re.compile(r"Diese Mitteilung enthält (in die Zukunft gerichtete|zukunftsgerichtete)", re.I),
]
# Kopfzeile "<Emittent> / Schlagwort(e): <Schlagwort>" bzw. Zeitstempelzeile
_LEAD_TAGLINE = re.compile(r"^.{0,140}?/\s*Schlagwort\(e\):\s*\S[^/]{0,80}?(?=\s{2}|\s[A-ZÄÖÜ])", re.I)
_TIMESTAMP = re.compile(r"\d{2}\.\d{2}\.\d{4}\s*/\s*\d{1,2}:\d{2}\s*(CE[TS]T|MEZ|MESZ)(\s*/\s*CES?T)?", re.I)


def _api_get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """GET auf die EQS-Schnittstelle; wirft bei Transport- oder Formatfehlern."""
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{EQS_API_BASE}/{path.lstrip('/')}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def _records(payload: Any) -> List[Dict[str, Any]]:
    """`records` ist je Endpunkt eine Liste oder ein einzelnes Objekt."""
    if not isinstance(payload, dict):
        return []
    records = payload.get("records")
    if isinstance(records, list):
        return [r for r in records if isinstance(r, dict)]
    if isinstance(records, dict):
        return [records]
    return []


def _plaintext(markup: Optional[str]) -> str:
    """HTML-Volltext in Fließtext überführen."""
    if not markup:
        return ""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", str(markup), flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _summary(markup: Optional[str], headline: str, limit: int = 700) -> Optional[str]:
    """
    Inhaltliche Zusammenfassung aus dem Volltext: Kopf- und Fußblock der
    EQS-Meldung sowie die im Text wiederholte Überschrift werden entfernt,
    damit die Erklärungsgenerierung auf dem Meldungsinhalt arbeitet und nicht
    auf den in allen Meldungen identischen Formalbausteinen.
    """
    text = _plaintext(markup)
    if not text:
        return None

    # Kopfblock: hinter dem spätesten Rechtshinweis beginnt der Meldungstext
    header_end = 0
    for pattern in _HEADER_END:
        for match in pattern.finditer(text):
            header_end = max(header_end, match.end())
    body = text[header_end:] if header_end else _LEAD_TAGLINE.sub(" ", text, count=1)

    # Fußblock: ab dem frühesten Verbreitungshinweis abschneiden
    footer_start = len(body)
    for pattern in _FOOTER_START:
        match = pattern.search(body)
        if match:
            footer_start = min(footer_start, match.start())
    body = body[:footer_start]

    body = _TIMESTAMP.sub(" ", body)
    if headline:
        body = body.replace(headline, " ")
    body = re.sub(r"\s+", " ", body).strip(" -–—/|:,")
    if len(body) < 40:  # nur Formalbausteine übrig
        return None
    if len(body) <= limit:
        return body
    cut = body[:limit]
    boundary = cut.rfind(". ")
    return (cut[:boundary + 1] if boundary > limit // 2 else cut).strip()


def _published_iso(record: Dict[str, Any]) -> Optional[str]:
    """Publikationszeitpunkt bevorzugt aus dem UTC-Feld der Schnittstelle."""
    for key in ("dateUtc", "date", "dtcreated"):
        value = record.get(key)
        if not value:
            continue
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat()
    return None


def resolve_isin(company_name: str) -> Optional[Dict[str, Any]]:
    """
    ISIN eines Unternehmens über die EQS-Meldungssuche auflösen.

    Der Unternehmens-Endpunkt der Schnittstelle liefert unabhängig von der
    Paginierung nur einen alphabetisch ersten Treffer und ist damit für die
    Auflösung unbrauchbar. Stattdessen wird die Volltextsuche über die
    Meldungen ausgewertet: Jeder Treffer trägt Emittentennamen und ISIN, die
    Trefferhäufigkeit je Emittent dient als Relevanzmaß.

    Ein Kandidat wird nur akzeptiert, wenn sein Name — nach Entfernen der
    Rechtsform — mit dem gesuchten Namen übereinstimmt oder ihn als Präfix
    enthält. Andernfalls liefert die Funktion None: Für nicht börsennotierte
    Unternehmen gibt es bei EQS keine Meldungen, und ein unscharfer Treffer
    würde einer Anomalie fremde Ereignisse zuordnen.
    """
    from collections import Counter

    from services.ticker_mapping import _LEGAL_SUFFIXES, _normalize_name

    # Die Volltextsuche der Schnittstelle wertet den Suchbegriff als
    # zusammenhängende Zeichenkette: 'Deutsche Lufthansa AG' liefert keinen
    # Treffer, 'Deutsche Lufthansa' dagegen den Emittenten. Die Rechtsform wird
    # deshalb zuerst entfernt und erst im Fallback mitgesucht.
    tokens = [t for t in (company_name or "").split()
              if "".join(c for c in t.lower() if c.isalnum()) not in _LEGAL_SUFFIXES]
    variants = [" ".join(tokens)] if tokens else []
    if company_name and company_name not in variants:
        variants.append(company_name)

    hits: "Counter[Tuple[str, str]]" = Counter()
    for variant in variants:
        if not variant.strip():
            continue
        try:
            payload = _api_get("news", {"search": variant, "per_page": _PER_PAGE})
        except Exception:
            continue
        for record in _records(payload):
            isin = str(record.get("isin") or "")
            name = str(record.get("companyName") or "")
            if not name or not isin or isin.lower().startswith("noisin"):
                continue
            hits[(name, isin)] += 1
        if hits:
            break

    query = _normalize_name(company_name)
    if not query:
        return None

    candidates = []
    for (name, isin), count in hits.items():
        normalized = _normalize_name(name)
        if not normalized:
            continue
        if normalized == query:
            rank = 0
        elif normalized.startswith(query + " ") or query.startswith(normalized + " "):
            rank = 1
        else:
            continue  # kein belastbarer Namensbezug
        candidates.append((rank, -count, name, isin))

    if not candidates:
        return None
    _, _, name, isin = sorted(candidates)[0]
    return {"isin": isin, "name": name, "source": "eqs"}


def _fetch_detail(record_id: str) -> Optional[Dict[str, Any]]:
    """
    Deutschsprachige Detailansicht einer Meldung.

    Die Liste liefert `<uuid>_<sprache>` in wechselnder Sprache; für die
    Auswertung wird durchgängig die deutsche Fassung angefragt und nur bei
    deren Fehlen auf die Originalfassung zurückgefallen.
    """
    uuid = str(record_id).rsplit("_", 1)[0]
    for candidate in (f"{uuid}_de", str(record_id)):
        try:
            detail = _records(_api_get("newsdetail", {"news_id": candidate}))
        except Exception:
            continue
        if detail:
            return detail[0]
    return None


def _fetch_news_page(isin: str, start: Optional[str], end: Optional[str],
                     page: int) -> List[Dict[str, Any]]:
    """
    Eine Ergebnisseite abrufen.

    Für die erste Seite wird `page` bewusst weggelassen: Die Schnittstelle
    liefert bei explizitem `page=1` in Verbindung mit `per_page=100` für einen
    Teil der Emittenten eine leere Ergebnismenge, während dieselbe Abfrage ohne
    `page` die erwarteten Datensätze zurückgibt (reproduzierbar u. a. für
    Siemens, ISIN DE0007236101). Ohne diese Behandlung fehlen die 100
    aktuellsten Meldungen — bei einem dreijährigen Erhebungszeitraum genau die
    für aktuelle Anomalien relevanten.
    """
    params: Dict[str, Any] = {
        "isin": isin,
        "start_date": start,
        "end_date": end,
        "per_page": _PER_PAGE,
    }
    if page > 1:
        params["page"] = page
    return _records(_api_get("news", params))


def fetch_adhoc(company_name: str, isin: Optional[str] = None,
                start: Optional[str] = None, end: Optional[str] = None,
                with_detail: bool = True) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Ad-hoc-Mitteilungen und Corporate News eines Unternehmens im Zeitraum.

    `start`/`end` als 'YYYY-MM-DD'; ohne Angabe liefert die Schnittstelle die
    jeweils aktuellsten Meldungen. Fehlt die ISIN, wird sie über die
    EQS-Unternehmenssuche aufgelöst.

    Rückgabe: (normalisierte context_items, Fehlermeldungen).
    """
    errors: List[str] = []

    if not isin:
        resolved = resolve_isin(company_name)
        if resolved is None:
            return [], [
                f"eqs: keine ISIN für '{company_name}' gefunden — ISIN manuell "
                "hinterlegen (PUT /api/context/company/{id}/ticker)"
            ]
        isin = resolved["isin"]

    raw_records: List[Dict[str, Any]] = []
    for page in range(1, _MAX_PAGES + 1):
        try:
            batch = _fetch_news_page(isin, start, end, page)
        except Exception as e:
            errors.append(f"eqs news (ISIN {isin}, Seite {page}): {e}")
            break
        if not batch:
            break
        raw_records.extend(batch)
        if len(batch) < _PER_PAGE:
            break

    # je Meldung nur eine Sprachfassung übernehmen
    relevant: Dict[str, Dict[str, Any]] = {}
    for record in raw_records:
        if record.get("categoryCode") not in RELEVANT_CATEGORIES:
            continue
        uuid = str(record.get("id") or "").rsplit("_", 1)[0]
        if uuid and uuid not in relevant:
            relevant[uuid] = record

    items: List[Dict[str, Any]] = []
    detail_calls = 0
    for record in relevant.values():
        category = str(record.get("categoryCode"))
        titel = str(record.get("headline") or "").strip()
        zusammenfassung: Optional[str] = None
        url: Optional[str] = None

        if with_detail and detail_calls < _MAX_DETAIL_CALLS:
            detail_calls += 1
            detail = _fetch_detail(str(record.get("id") or ""))
            if detail is not None:
                titel = str(detail.get("headline") or titel).strip()
                url = detail.get("share_url") or None
                zusammenfassung = _summary(detail.get("content"), titel)

        if not titel:
            continue
        items.append({
            "source_type": RELEVANT_CATEGORIES[category],
            "provider": "eqs",
            "titel": titel,
            "zusammenfassung": zusammenfassung,
            "url": url,
            "published_at": _published_iso(record),
            "raw": {"category": record.get("category"), "category_code": category,
                    "isin": record.get("isin"), "eqs_id": record.get("id")},
        })

    items.sort(key=lambda i: str(i.get("published_at") or ""))
    return items, errors
