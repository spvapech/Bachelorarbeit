"""
Yahoo-Finance-Adapter (yfinance) für Nachrichten, Kurse und Kennzahlen.

yfinance ist eine inoffizielle API: einzelne Felder können fehlen, `.info`
liefert zeitweise Fehler (Rate-Limits), und das News-Schema hat sich über
Versionen geändert (flach vs. verschachteltes `content`). Der Adapter
normalisiert beide Schemata und behandelt jede Extraktion defensiv.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import yfinance as yf


def _iso_from_any(value: Any) -> Optional[str]:
    """Publikationsdatum aus Unix-Timestamp oder ISO-String normalisieren."""
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
        text = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(text).isoformat()
    except (ValueError, OSError, OverflowError):
        return None


def _normalize_news_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Ein yfinance-News-Item (flaches oder verschachteltes Schema) normalisieren."""
    content = item.get("content") if isinstance(item.get("content"), dict) else None

    if content is not None:  # aktuelles Schema (verschachtelt)
        titel = content.get("title")
        summary = content.get("summary") or content.get("description")
        url = None
        for key in ("canonicalUrl", "clickThroughUrl"):
            candidate = content.get(key)
            if isinstance(candidate, dict) and candidate.get("url"):
                url = candidate["url"]
                break
        published = _iso_from_any(content.get("pubDate") or content.get("displayTime"))
    else:  # Legacy-Schema (flach)
        titel = item.get("title")
        summary = item.get("summary")
        url = item.get("link")
        published = _iso_from_any(item.get("providerPublishTime"))

    if not titel:
        return None
    return {
        "source_type": "news",
        "provider": "yfinance",
        "titel": str(titel),
        "zusammenfassung": str(summary) if summary else None,
        "url": str(url) if url else None,
        "published_at": published,
        "raw": None,  # Rohdaten bewusst nicht persistiert (Volumen)
    }


def fetch_news(ticker: str, count: int = 50) -> List[Dict[str, Any]]:
    """Unternehmensnachrichten zu einem Ticker, normalisiert auf context_item-Form."""
    raw_items = yf.Ticker(ticker).get_news(count=count) or []
    normalized = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        norm = _normalize_news_item(item)
        if norm is not None:
            normalized.append(norm)
    return normalized


def fetch_prices(ticker: str, years: int = 3) -> Dict[str, Any]:
    """Tägliche Schlusskurse der letzten `years` Jahre."""
    t = yf.Ticker(ticker)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365 * years)
    hist = t.history(start=start.date().isoformat(), end=end.date().isoformat(),
                     interval="1d", auto_adjust=True)

    currency = None
    try:
        currency = t.fast_info["currency"]
    except Exception:
        pass

    prices: List[Dict[str, Any]] = []
    for idx, row in hist.iterrows():
        close = row.get("Close")
        if close is None or close != close:  # NaN-Guard
            continue
        prices.append({
            "date": idx.date().isoformat(),
            "close": round(float(close), 4),
            "volume": int(row["Volume"]) if row.get("Volume") == row.get("Volume") else None,
            "currency": currency,
        })
    return {"currency": currency, "prices": prices}


def fetch_recommendations(ticker: str) -> List[Dict[str, Any]]:
    """
    Analystenempfehlungen (Strong Buy … Strong Sell) je Monat.

    yfinance liefert relative Perioden ('0m', '-1m', …); sie werden hier in
    Kalendermonate ('YYYY-MM') aufgelöst, sodass wiederholte Abrufe über die
    Zeit eine Historie in der Datenbank aufbauen.
    """
    try:
        df = yf.Ticker(ticker).recommendations
    except Exception:
        return []
    if df is None or getattr(df, "empty", True):
        return []

    now = datetime.now(timezone.utc)
    rows: List[Dict[str, Any]] = []
    for record in df.to_dict("records"):
        period = str(record.get("period") or "")
        try:
            offset = int(period.replace("m", "")) if period else 0
        except ValueError:
            continue
        idx = now.year * 12 + (now.month - 1) + offset  # offset ist 0 oder negativ
        month = f"{idx // 12:04d}-{idx % 12 + 1:02d}"

        def _count(key: str) -> int:
            value = record.get(key)
            try:
                return int(value) if value == value and value is not None else 0
            except (TypeError, ValueError):
                return 0

        rows.append({
            "month": month,
            "strong_buy": _count("strongBuy"),
            "buy": _count("buy"),
            "hold": _count("hold"),
            "sell": _count("sell"),
            "strong_sell": _count("strongSell"),
        })
    return rows


_KPI_FIELDS = {
    "market_cap": "marketCap",
    "trailing_pe": "trailingPE",
    "revenue": "totalRevenue",
    "employees": "fullTimeEmployees",
    "dividend_yield": "dividendYield",
    "profit_margin": "profitMargins",
    "currency": "currency",
}


def fetch_kpis(ticker: str) -> Dict[str, Any]:
    """Zentrale Kennzahlen aus `Ticker.info`; fehlende Felder werden None."""
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:
        info = {}

    kpis: Dict[str, Any] = {"ticker": ticker}
    for target, source in _KPI_FIELDS.items():
        try:
            kpis[target] = info.get(source)
        except Exception:
            kpis[target] = None
    return kpis
