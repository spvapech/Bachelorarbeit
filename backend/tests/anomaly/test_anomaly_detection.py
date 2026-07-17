"""
Tests der Anomalieerkennung (PELT + z-Score) auf synthetischen Zeitreihen.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.anomaly_detection_service import (
    AnomalyParams,
    available_dimensions,
    build_monthly_series,
    detect_anomalies,
    event_window,
)


def _series(values, start_year=2022, count=10):
    """Baut eine Monatsserie aus einer Werteliste (fortlaufende Monate)."""
    out = []
    for i, v in enumerate(values):
        y = start_year + i // 12
        m = i % 12 + 1
        out.append({"period": f"{y:04d}-{m:02d}", "value": v, "count": count})
    return out


LEVEL_SHIFT = _series([4.0, 4.1, 3.9, 4.0, 4.1, 4.0, 2.8, 2.7, 2.9, 2.8, 2.7, 2.8])
SPIKE = _series([3.5, 3.6, 3.5, 3.4, 3.5, 3.6, 4.8, 3.5, 3.4, 3.5, 3.6, 3.5])
FLAT = _series([3.5] * 12)
NOISY = _series([3.5, 3.6, 3.4, 3.55, 3.45, 3.6, 3.5, 3.4, 3.6, 3.5, 3.45, 3.55])


def test_pelt_finds_level_shift():
    res = detect_anomalies(LEVEL_SHIFT, AnomalyParams(method="pelt"),
                           "durchschnittsbewertung", "employee")
    assert len(res) == 1
    anomaly = res[0]
    # Shift beginnt bei Index 6 → Periode 2022-07 (±1 Monat toleriert)
    assert anomaly["period"] in ("2022-06", "2022-07", "2022-08")
    assert anomaly["direction"] == "fall"
    assert anomaly["magnitude"] < -1.0
    assert anomaly["method"] == "pelt"


def test_zscore_finds_spike_pelt_does_not():
    z_res = detect_anomalies(SPIKE, AnomalyParams(method="zscore"),
                             "durchschnittsbewertung", "employee")
    assert any(a["period"] == "2022-07" and a["direction"] == "rise" for a in z_res)

    # PELT mit min_size=2 ignoriert den Ein-Monats-Ausreisser
    p_res = detect_anomalies(SPIKE, AnomalyParams(method="pelt", min_size=2),
                             "durchschnittsbewertung", "employee")
    assert not any(a["period"] == "2022-07" for a in p_res)


def test_flat_and_noisy_series_yield_nothing():
    for series in (FLAT, NOISY):
        for method in ("pelt", "zscore"):
            res = detect_anomalies(series, AnomalyParams(method=method),
                                   "durchschnittsbewertung", "employee")
            assert res == [], f"{method} sollte auf ruhiger Serie nichts finden"


def test_higher_penalty_detects_no_more():
    counts = []
    for pen in (0.2, 0.5, 1.0, 3.0, 10.0):
        res = detect_anomalies(LEVEL_SHIFT, AnomalyParams(method="pelt", penalty=pen),
                               "durchschnittsbewertung", "employee")
        counts.append(len(res))
    assert counts == sorted(counts, reverse=True), \
        f"Hoehere Penalty darf nicht mehr Anomalien liefern: {counts}"


def test_min_magnitude_filters_small_shifts():
    small_shift = _series([4.0] * 6 + [3.85] * 6)  # Delta 0.15 < 0.3
    res = detect_anomalies(small_shift, AnomalyParams(method="pelt", penalty=0.01),
                           "durchschnittsbewertung", "employee")
    assert res == []


def test_zscore_direction_and_magnitude():
    res = detect_anomalies(LEVEL_SHIFT, AnomalyParams(method="zscore"),
                           "durchschnittsbewertung", "employee")
    assert res, "z-Score sollte den Level-Shift erkennen"
    first = res[0]
    assert first["direction"] == "fall"
    assert first["magnitude"] < -0.3
    assert first["score"] >= 2.0  # |z| ueber der Schwelle


def test_too_short_series_yields_nothing():
    short = _series([4.0, 2.5])
    for method in ("pelt", "zscore"):
        res = detect_anomalies(short, AnomalyParams(method=method),
                               "durchschnittsbewertung", "employee")
        assert res == []


def test_event_window_bounds():
    start, end = event_window("2023-01", 2)
    assert start == "2022-11-01"
    assert end == "2023-03-31"
    start, end = event_window("2023-12", 2)
    assert end == "2024-02-29"  # Schaltjahr
    start, end = event_window("2023-06", 0)
    assert (start, end) == ("2023-06-01", "2023-06-30")


def test_build_monthly_series_min_reviews_filter():
    # In-Memory-Demo: Demo 3 hat durchgehend >= 10 Reviews/Monat;
    # eine absurd hohe Schwelle muss alle Monate verwerfen.
    many = build_monthly_series(3, "employee", "durchschnittsbewertung", min_reviews=3)
    none = build_monthly_series(3, "employee", "durchschnittsbewertung", min_reviews=10_000)
    assert len(many) > 0
    assert none == []
    assert all(m["count"] >= 3 for m in many)
    periods = [m["period"] for m in many]
    assert periods == sorted(periods)


def test_available_dimensions():
    dims = available_dimensions("employee")
    assert dims[0] == "durchschnittsbewertung"
    assert "kommunikation" in dims and len(dims) == 14
    cand = available_dimensions("candidates")
    assert "schnelle_antwort" in cand and len(cand) == 11
