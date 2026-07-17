"""
API-Routen der Erklärungsgenerierung (2. Design-Zyklus): Erklärungsansätze
je Anomalie mit Quellenbeleg sowie die Erklärungsabdeckung (DZ2).
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.explanation_service import (
    compute_coverage,
    generate_explanations_for_company,
    get_explanations_grouped,
)

router = APIRouter(prefix="/api/explanations", tags=["Erklärungen"])


class GenerateRequest(BaseModel):
    source: Optional[str] = None
    method: Optional[str] = None
    min_score: float = Field(default=0.2, ge=0, le=1)
    top_n: int = Field(default=5, ge=1, le=20)
    with_sentiment: bool = True


@router.post("/company/{company_id}/generate")
async def generate(company_id: int, request: GenerateRequest | None = None):
    """Erklärungen für alle Anomalien des Unternehmens (neu) generieren."""
    try:
        request = request or GenerateRequest()
        return generate_explanations_for_company(
            company_id,
            source=request.source,
            method=request.method,
            min_score=request.min_score,
            top_n=request.top_n,
            with_sentiment=request.with_sentiment,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Erklärungsgenerierung: {str(e)}")


@router.get("/company/{company_id}")
async def list_explanations(
    company_id: int,
    source: Optional[str] = Query(default=None, description="'employee' oder 'candidates'"),
    method: Optional[str] = Query(default=None, description="'pelt' oder 'zscore'"),
):
    """Anomalien mit ihren Erklärungsansätzen (auch ohne Erklärung, leere Liste)."""
    try:
        items = get_explanations_grouped(company_id, source=source, method=method)
        return {
            "items": items,
            "coverage": compute_coverage(company_id, source=source, method=method),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Erklärungs-Abfrage: {str(e)}")


@router.get("/company/{company_id}/coverage")
async def coverage(
    company_id: int,
    source: Optional[str] = Query(default=None),
    method: Optional[str] = Query(default=None),
):
    """Erklärungsabdeckung (DZ2): Anteil der Anomalien mit ≥1 Erklärungsansatz."""
    try:
        return compute_coverage(company_id, source=source, method=method)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Coverage-Berechnung: {str(e)}")
