"""
Anomalieerkennung in Bewertungszeitreihen (2. Design-Zyklus).

Bereitet Kununu-Bewertungen als monatliche Zeitreihen auf (Gesamtbewertung
und Einzeldimensionen) und erkennt extreme Steigungen und Senkungen über
zwei Verfahren hinter einer gemeinsamen Schnittstelle:

- PELT (Changepoint-Detection, Truong et al. 2020) via `ruptures`
- schwellenwertbasiert (rollierender z-Score)

Beide Verfahren arbeiten auf derselben Serienaufbereitung, sodass die
Parameterkalibrierung (DZ1, scripts/validate_anomaly_detection.py) die
Methoden direkt vergleichen kann.
"""

from calendar import monthrange
from dataclasses import dataclass, asdict
from datetime import datetime
from statistics import mean, stdev
from typing import Any, Dict, List, Literal, Optional, Union

import ruptures as rpt

from database.supabase_client import get_supabase_client
from services.topic_average_rating_service import TOPIC_COLUMNS_BY_SOURCE

supabase = get_supabase_client()

OVERALL_DIMENSION = "durchschnittsbewertung"

# Minimale Standardabweichung fuer den z-Score: verhindert Divisionsartefakte
# bei nahezu konstanten Baselines (Bewertungen sind auf 0.01 gerundet).
_MIN_STD = 0.05

DIMENSION_LABELS: Dict[str, str] = {
    OVERALL_DIMENSION: "Gesamtbewertung",
    # employee
    "arbeitsatmosphaere": "Arbeitsatmosphäre",
    "image": "Image",
    "work_life_balance": "Work-Life-Balance",
    "karriere_weiterbildung": "Karriere & Weiterbildung",
    "gehalt_sozialleistungen": "Gehalt & Sozialleistungen",
    "kollegenzusammenhalt": "Kollegenzusammenhalt",
    "umwelt_sozialbewusstsein": "Umwelt- & Sozialbewusstsein",
    "vorgesetztenverhalten": "Vorgesetztenverhalten",
    "kommunikation": "Kommunikation",
    "interessante_aufgaben": "Interessante Aufgaben",
    "umgang_mit_aelteren_kollegen": "Umgang mit älteren Kollegen",
    "arbeitsbedingungen": "Arbeitsbedingungen",
    "gleichberechtigung": "Gleichberechtigung",
    # candidates
    "erklaerung_der_weiteren_schritte": "Erklärung der weiteren Schritte",
    "zufriedenstellende_reaktion": "Zufriedenstellende Reaktion",
    "vollstaendigkeit_der_infos": "Vollständigkeit der Infos",
    "zufriedenstellende_antworten": "Zufriedenstellende Antworten",
    "angenehme_atmosphaere": "Angenehme Atmosphäre",
    "professionalitaet_des_gespraechs": "Professionalität des Gesprächs",
    "wertschaetzende_behandlung": "Wertschätzende Behandlung",
    "erwartbarkeit_des_prozesses": "Erwartbarkeit des Prozesses",
    "zeitgerechte_zu_oder_absage": "Zeitgerechte Zu- oder Absage",
    "schnelle_antwort": "Schnelle Antwort",
}


def dimension_label(dimension: str) -> str:
    return DIMENSION_LABELS.get(dimension, dimension)


def available_dimensions(source: str) -> List[str]:
    """Alle analysierbaren Dimensionen einer Quelle (Gesamt + Einzeldimensionen)."""
    return [OVERALL_DIMENSION] + list(TOPIC_COLUMNS_BY_SOURCE[source].keys())


@dataclass
class AnomalyParams:
    method: Literal["pelt", "zscore"] = "pelt"
    # PELT: Penalty auf Bewertungsskala (1-5) kalibriert — hoehere Werte
    # unterdruecken Segmentwechsel; 0.5 trifft die annotierten Demo-Zeitraeume.
    penalty: float = 0.5
    min_size: int = 2
    model: str = "l2"
    # z-Score
    z_threshold: float = 2.0
    z_window: int = 6          # rollierendes Fenster in Monaten (0 = alle Vormonate)
    # gemeinsame Filter
    min_reviews_per_month: int = 3
    min_magnitude: float = 0.3

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _value_column(source: str, dimension: str) -> str:
    if dimension == OVERALL_DIMENSION:
        return OVERALL_DIMENSION
    topic_cols = TOPIC_COLUMNS_BY_SOURCE[source]
    if dimension not in topic_cols:
        raise ValueError(f"Unbekannte Dimension '{dimension}' für Quelle '{source}'")
    return topic_cols[dimension]


def _fetch_rows_paginated(source: str, company_id: int, select_cols: str,
                          page_size: int = 1000) -> List[Dict[str, Any]]:
    """Paginierter Fetch mit frischer Query je Seite (kompatibel mit In-Memory-Store)."""
    all_rows: List[Dict[str, Any]] = []
    start = 0
    while True:
        res = (
            supabase.table(source)
            .select(select_cols)
            .eq("company_id", company_id)
            .order("datum")
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = res.data or []
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size
    return all_rows


def build_monthly_series(company_id: int, source: str, dimension: str,
                         min_reviews: int = 3) -> List[Dict[str, Any]]:
    """
    Monatliche Durchschnittswerte einer Bewertungsdimension.

    Rückgabe: [{"period": "2023-03", "value": 2.71, "count": 14}, ...],
    aufsteigend sortiert; Monate mit weniger als `min_reviews` Bewertungen
    werden verworfen (dünn besetzte Monate sind zu verrauscht).
    """
    col = _value_column(source, dimension)
    rows = _fetch_rows_paginated(source, company_id, f"datum, {col}")

    buckets: Dict[str, List[float]] = {}
    for row in rows:
        datum = row.get("datum")
        value = row.get(col)
        if datum is None or value is None:
            continue
        period = str(datum)[:7]
        if len(period) != 7 or period[4] != "-":
            continue
        buckets.setdefault(period, []).append(float(value))

    series = [
        {"period": period, "value": round(mean(vals), 3), "count": len(vals)}
        for period, vals in sorted(buckets.items())
        if len(vals) >= min_reviews
    ]
    return series


def _shift_period(period: str, months: int) -> str:
    y, m = int(period[:4]), int(period[5:7])
    idx = y * 12 + (m - 1) + months
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def event_window(period: str, window_months: int) -> tuple[str, str]:
    """Ereignisfenster um einen Anomaliemonat: erster/letzter Kalendertag."""
    start_period = _shift_period(period, -window_months)
    end_period = _shift_period(period, window_months)
    end_y, end_m = int(end_period[:4]), int(end_period[5:7])
    last_day = monthrange(end_y, end_m)[1]
    return f"{start_period}-01", f"{end_period}-{last_day:02d}"


def _make_anomaly(periods: List[str], idx: int, direction: str, magnitude: float,
                  score: float, baseline: float, params: AnomalyParams,
                  dimension: str, source: str, values: List[float],
                  window_months: int) -> Dict[str, Any]:
    period = periods[idx]
    window_start, window_end = event_window(period, window_months)
    return {
        "period": period,
        "dimension": dimension,
        "source": source,
        "direction": direction,
        "magnitude": round(magnitude, 2),
        "score": round(score, 3),
        "method": params.method,
        "params": params.to_dict(),
        "window_start": window_start,
        "window_end": window_end,
        "series_value": round(values[idx], 3),
        "baseline_value": round(baseline, 3),
    }


def _detect_pelt(values: List[float], periods: List[str], params: AnomalyParams,
                 dimension: str, source: str, window_months: int) -> List[Dict[str, Any]]:
    """Changepoints via PELT; je Changepoint Segmentmittel davor/danach vergleichen."""
    n = len(values)
    if n < 2 * params.min_size:
        return []

    import numpy as np
    signal = np.asarray(values, dtype=float).reshape(-1, 1)
    algo = rpt.Pelt(model=params.model, min_size=params.min_size, jump=1).fit(signal)
    breakpoints = algo.predict(pen=params.penalty)  # Segment-Endindizes, letzter = n

    anomalies: List[Dict[str, Any]] = []
    boundaries = [0] + breakpoints  # Segmentgrenzen: [0, b1, b2, ..., n]
    for i in range(1, len(boundaries) - 1):
        prev_seg = values[boundaries[i - 1]:boundaries[i]]
        next_seg = values[boundaries[i]:boundaries[i + 1]]
        if not prev_seg or not next_seg:
            continue
        delta = mean(next_seg) - mean(prev_seg)
        if abs(delta) < params.min_magnitude:
            continue
        anomalies.append(_make_anomaly(
            periods, boundaries[i],
            direction="rise" if delta > 0 else "fall",
            magnitude=delta, score=abs(delta), baseline=mean(prev_seg),
            params=params, dimension=dimension, source=source,
            values=values, window_months=window_months,
        ))
    return anomalies


def _detect_zscore(values: List[float], periods: List[str], params: AnomalyParams,
                   dimension: str, source: str, window_months: int) -> List[Dict[str, Any]]:
    """z-Score jedes Monats gegenüber der Baseline der Vormonate."""
    anomalies: List[Dict[str, Any]] = []
    for t in range(1, len(values)):
        lo = 0 if params.z_window <= 0 else max(0, t - params.z_window)
        baseline = values[lo:t]
        if len(baseline) < 3:
            continue
        mu = mean(baseline)
        sigma = max(stdev(baseline), _MIN_STD)
        delta = values[t] - mu
        z = delta / sigma
        if abs(z) < params.z_threshold or abs(delta) < params.min_magnitude:
            continue
        anomalies.append(_make_anomaly(
            periods, t,
            direction="rise" if delta > 0 else "fall",
            magnitude=delta, score=abs(z), baseline=mu,
            params=params, dimension=dimension, source=source,
            values=values, window_months=window_months,
        ))
    return anomalies


def detect_anomalies(series: List[Dict[str, Any]], params: AnomalyParams,
                     dimension: str, source: str,
                     window_months: int = 2) -> List[Dict[str, Any]]:
    """Erkennt Anomalien in einer Monatsserie; dispatcht auf die gewählte Methode."""
    values = [s["value"] for s in series]
    periods = [s["period"] for s in series]
    if params.method == "pelt":
        return _detect_pelt(values, periods, params, dimension, source, window_months)
    if params.method == "zscore":
        return _detect_zscore(values, periods, params, dimension, source, window_months)
    raise ValueError(f"Unbekannte Methode '{params.method}'")


def detect_and_persist(company_id: int, source: str,
                       dimensions: Union[Literal["all"], List[str]],
                       params: AnomalyParams, window_months: int = 2,
                       replace: bool = True) -> List[Dict[str, Any]]:
    """
    Führt die Erkennung für die gewünschten Dimensionen aus und persistiert
    die Ergebnisse (Tabelle `anomalies`) inklusive der verwendeten Parameter.
    """
    if dimensions == "all":
        dims = available_dimensions(source)
    else:
        dims = list(dimensions)

    persisted: List[Dict[str, Any]] = []
    for dim in dims:
        series = build_monthly_series(company_id, source, dim,
                                      min_reviews=params.min_reviews_per_month)
        found = detect_anomalies(series, params, dim, source, window_months)

        if replace:
            supabase.table("anomalies").delete() \
                .eq("company_id", company_id).eq("source", source) \
                .eq("dimension", dim).eq("method", params.method).execute()

        for anomaly in found:
            row = {
                "company_id": company_id,
                "source": source,
                "dimension": dim,
                "period": anomaly["period"],
                "window_start": anomaly["window_start"],
                "window_end": anomaly["window_end"],
                "direction": anomaly["direction"],
                "magnitude": anomaly["magnitude"],
                "score": anomaly["score"],
                "method": anomaly["method"],
                "params": anomaly["params"],
                "detected_at": datetime.now().isoformat(),
            }
            res = supabase.table("anomalies").insert(row).execute()
            stored = (res.data or [row])[0]
            persisted.append(stored)

    return persisted


def get_anomalies(company_id: int, source: Optional[str] = None,
                  dimension: Optional[str] = None,
                  method: Optional[str] = None) -> List[Dict[str, Any]]:
    """Persistierte Anomalien eines Unternehmens, aufsteigend nach Monat."""
    q = supabase.table("anomalies").select("*").eq("company_id", company_id)
    if source:
        q = q.eq("source", source)
    if dimension:
        q = q.eq("dimension", dimension)
    if method:
        q = q.eq("method", method)
    rows = q.order("period").execute().data or []
    for row in rows:
        row["dimension_label"] = dimension_label(row.get("dimension", ""))
    return rows
