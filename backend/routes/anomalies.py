"""
API-Routen der Anomalieerkennung (2. Design-Zyklus).

Erkennt extreme Veränderungen in Bewertungszeitreihen (PELT / z-Score)
und liefert persistierte Anomalien für das Dashboard.
"""

from typing import List, Literal, Optional, Union

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.anomaly_detection_service import (
    AnomalyParams,
    available_dimensions,
    build_monthly_series,
    detect_and_persist,
    dimension_label,
    get_anomalies,
)

router = APIRouter(prefix="/api/anomalies", tags=["Anomalien"])


class DetectRequest(BaseModel):
    method: Literal["pelt", "zscore"] = "pelt"
    penalty: float = Field(default=0.5, gt=0)
    min_size: int = Field(default=2, ge=1)
    model: str = "l2"
    z_threshold: float = Field(default=2.0, gt=0)
    z_window: int = Field(default=6, ge=0)
    min_reviews_per_month: int = Field(default=3, ge=1)
    min_magnitude: float = Field(default=0.3, ge=0)
    window_months: int = Field(default=2, ge=0)
    source: Literal["employee", "candidates"] = "employee"
    dimensions: Union[Literal["all"], List[str]] = ["durchschnittsbewertung"]
    replace: bool = True

    def to_params(self) -> AnomalyParams:
        return AnomalyParams(
            method=self.method,
            penalty=self.penalty,
            min_size=self.min_size,
            model=self.model,
            z_threshold=self.z_threshold,
            z_window=self.z_window,
            min_reviews_per_month=self.min_reviews_per_month,
            min_magnitude=self.min_magnitude,
        )


@router.get("/company/{company_id}")
async def list_anomalies(
    company_id: int,
    source: str = Query(default="employee", description="'employee' oder 'candidates'"),
    dimension: Optional[str] = Query(default=None),
    method: Optional[str] = Query(default=None, description="'pelt' oder 'zscore'"),
    autodetect: bool = Query(default=True, description="Bei leerer DB Default-Erkennung ausführen"),
):
    """Persistierte Anomalien; führt bei Bedarf eine Default-PELT-Erkennung aus."""
    try:
        anomalies = get_anomalies(company_id, source=source, dimension=dimension, method=method)

        if not anomalies and autodetect and method in (None, "pelt"):
            detect_and_persist(
                company_id, source, dimensions="all",
                params=AnomalyParams(method="pelt"), window_months=2, replace=True,
            )
            anomalies = get_anomalies(company_id, source=source, dimension=dimension, method=method)

        return {"anomalies": anomalies, "count": len(anomalies)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Anomalie-Abfrage: {str(e)}")


@router.post("/company/{company_id}/detect")
async def detect(company_id: int, request: DetectRequest):
    """Anomalieerkennung mit expliziten Parametern ausführen und persistieren."""
    try:
        params = request.to_params()
        persisted = detect_and_persist(
            company_id, request.source, request.dimensions,
            params=params, window_months=request.window_months,
            replace=request.replace,
        )
        for anomaly in persisted:
            anomaly["dimension_label"] = dimension_label(anomaly.get("dimension", ""))
        return {
            "detected": len(persisted),
            "anomalies": persisted,
            "params_used": params.to_dict() | {"window_months": request.window_months},
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Anomalieerkennung: {str(e)}")


@router.get("/company/{company_id}/series")
async def get_series(
    company_id: int,
    source: str = Query(default="employee"),
    dimension: str = Query(default="durchschnittsbewertung"),
    min_reviews: int = Query(default=3, ge=1),
):
    """Monatliche Zeitreihe einer Dimension (für Kalibrierung/Debugging)."""
    try:
        if dimension not in available_dimensions(source):
            raise ValueError(f"Unbekannte Dimension '{dimension}' für Quelle '{source}'")
        series = build_monthly_series(company_id, source, dimension, min_reviews=min_reviews)
        return {
            "dimension": dimension,
            "dimension_label": dimension_label(dimension),
            "source": source,
            "series": series,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Serienaufbau: {str(e)}")
