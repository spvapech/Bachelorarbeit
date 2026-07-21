"""
API-Routen der Kontextsammlung (2. Design-Zyklus): Ticker-Zuordnung,
Refresh externer Quellen, Zugriff auf News/Ad-hoc, Kurse und Kennzahlen.
"""

from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from services import context_service
from services.ticker_mapping import suggest_tickers

router = APIRouter(prefix="/api/context", tags=["Kontext"])


class TickerUpdate(BaseModel):
    ticker: str
    isin: Optional[str] = None


@router.get("/ticker-suggestions")
async def ticker_suggestions(q: str = Query(default="")):
    """Ticker-Vorschläge für deutsche börsennotierte Unternehmen."""
    return {"suggestions": suggest_tickers(q)}


@router.get("/company/{company_id}")
async def context_overview(company_id: int):
    """Statusübersicht: Ticker, Kennzahlen, Anzahl News/Ad-hoc/Kurspunkte."""
    try:
        return context_service.get_context_overview(company_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Kontext-Übersicht: {str(e)}")


@router.post("/company/{company_id}/resolve-ticker")
async def resolve_ticker(company_id: int):
    """Ticker automatisch anhand des Firmennamens auflösen und speichern."""
    try:
        return context_service.resolve_and_set_ticker(company_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Ticker-Auflösung: {str(e)}")


@router.post("/company/{company_id}/resolve-isin")
async def resolve_isin(company_id: int):
    """ISIN automatisch auflösen und speichern (Voraussetzung für Ad-hoc-Abruf)."""
    try:
        return context_service.resolve_and_set_isin(company_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der ISIN-Auflösung: {str(e)}")


@router.put("/company/{company_id}/ticker")
async def update_ticker(company_id: int, body: TickerUpdate):
    """Ticker (und optional ISIN) eines Unternehmens setzen."""
    try:
        company = context_service.set_company_ticker(company_id, body.ticker, body.isin)
        return {"company": company}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Setzen des Tickers: {str(e)}")


@router.post("/company/{company_id}/refresh")
async def refresh(
    company_id: int,
    sources: Optional[str] = Query(default=None, description="Kommagetrennt: news,adhoc,prices,kpis"),
    years: int = Query(default=3, ge=1, le=10),
):
    """Externe Quellen abrufen und persistieren (explizit, kein Auto-Fetch)."""
    try:
        requested = (
            {s.strip() for s in sources.split(",") if s.strip()} if sources else None
        )
        return context_service.refresh_context(company_id, requested, years=years)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Kontext-Refresh: {str(e)}")


@router.get("/company/{company_id}/news")
async def news(
    company_id: int,
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    source_type: Optional[str] = Query(default=None, description="'news' | 'adhoc' | 'stock_move'"),
):
    """Persistierte Kontext-Ereignisse (News/Ad-hoc) im Zeitraum."""
    try:
        items = context_service.get_context_items(company_id, start, end, source_type)
        return {"items": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der News-Abfrage: {str(e)}")


@router.get("/company/{company_id}/stock")
async def stock(
    company_id: int,
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
):
    """Aktienkursverlauf (Tageswerte + Monatsaggregat)."""
    try:
        return context_service.get_stock_series(company_id, start, end)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Kursabfrage: {str(e)}")


@router.get("/company/{company_id}/recommendations")
async def recommendations(company_id: int):
    """Analystenempfehlungen (Strong Buy … Strong Sell) je Monat, persistiert."""
    try:
        items = context_service.get_analyst_recommendations(company_id)
        return {"recommendations": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Empfehlungs-Abfrage: {str(e)}")


@router.get("/company/{company_id}/kpis")
async def kpis(company_id: int):
    """Zentrale Unternehmenskennzahlen (persistiert)."""
    try:
        data = context_service.get_financial_kpis(company_id)
        if data is None:
            raise HTTPException(status_code=404, detail="Keine Kennzahlen vorhanden")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Kennzahlen-Abfrage: {str(e)}")


@router.post("/company/{company_id}/import")
async def import_manual(company_id: int, file: UploadFile = File(...)):
    """Manueller Import externer Ereignisse (CSV/JSON, provider 'manual')."""
    try:
        raw = await file.read()
        return context_service.import_manual_items(company_id, raw, file.filename or "upload.csv")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Import: {str(e)}")
