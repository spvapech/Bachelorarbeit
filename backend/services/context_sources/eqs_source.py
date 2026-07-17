"""
EQS/DGAP-Adapter für Ad-hoc-Mitteilungen (Best Effort).

EQS (vormals DGAP) bietet keine offizielle, frei nutzbare API. Dieser
Adapter liest den öffentlichen EQS-News-RSS-Feed und filtert Einträge
auf den Unternehmensnamen bzw. die ISIN. Einschränkungen (bewusster
Trade-off, siehe Exposé Abschnitt 2.6):

- RSS enthält nur aktuelle Meldungen, keine Historie — für zurückliegende
  Anomaliezeiträume ist der manuelle Import (manual_import.py) der
  garantierte Pfad.
- Feed-Struktur kann sich ändern; jeder Fehler führt zu einer leeren
  Ergebnisliste plus Fehlereintrag, nie zu einem Abbruch der Pipeline.
"""

import os
import urllib.request
from typing import Any, Dict, List, Tuple

import feedparser

# Öffentlicher EQS-News-Feed; per Env-Variable übersteuerbar.
EQS_RSS_URLS = [
    url.strip()
    for url in os.getenv("EQS_RSS_URLS", "https://www.eqs-news.com/feed/").split(",")
    if url.strip()
]

_TIMEOUT_SECONDS = 10


def _matches_company(text: str, company_name: str, isin: str | None) -> bool:
    haystack = text.lower()
    tokens = [t for t in company_name.lower().split() if len(t) >= 3]
    if tokens and all(t in haystack for t in tokens):
        return True
    if isin and isin.lower() in haystack:
        return True
    return False


def fetch_adhoc(company_name: str, isin: str | None = None) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Ad-hoc-/Corporate-News-Einträge zum Unternehmen aus den EQS-RSS-Feeds.

    Rückgabe: (normalisierte Items, Fehlermeldungen). Fehler einzelner Feeds
    brechen die Sammlung nicht ab.
    """
    items: List[Dict[str, Any]] = []
    errors: List[str] = []

    for feed_url in EQS_RSS_URLS:
        try:
            with urllib.request.urlopen(feed_url, timeout=_TIMEOUT_SECONDS) as resp:
                raw = resp.read()
            feed = feedparser.parse(raw)
            for entry in feed.entries or []:
                title = getattr(entry, "title", "") or ""
                summary = getattr(entry, "summary", "") or ""
                if not _matches_company(f"{title} {summary}", company_name, isin):
                    continue
                published = None
                parsed = getattr(entry, "published_parsed", None)
                if parsed is not None:
                    from datetime import datetime, timezone
                    from calendar import timegm
                    published = datetime.fromtimestamp(timegm(parsed), tz=timezone.utc).isoformat()
                items.append({
                    "source_type": "adhoc",
                    "provider": "eqs_rss",
                    "titel": title,
                    "zusammenfassung": summary or None,
                    "url": getattr(entry, "link", None),
                    "published_at": published,
                    "raw": None,
                })
        except Exception as e:
            errors.append(f"eqs_rss ({feed_url}): {e}")

    return items, errors
