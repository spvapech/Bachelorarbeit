"""
Tests des DZ1-Validierungs-Matchings (scripts/validate_anomaly_detection.py).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from scripts.validate_anomaly_detection import (
    compute_metrics,
    load_annotations,
    match_anomalies,
)


def _d(period, direction="fall"):
    return {"period": period, "direction": direction}


def test_exact_match():
    pairs, fps, fns = match_anomalies([_d("2023-01")], [_d("2023-01")])
    assert len(pairs) == 1 and fps == [] and fns == []


def test_tolerance_match():
    pairs, fps, fns = match_anomalies([_d("2023-02")], [_d("2023-01")],
                                      tolerance_months=1)
    assert len(pairs) == 1
    pairs, fps, fns = match_anomalies([_d("2023-03")], [_d("2023-01")],
                                      tolerance_months=1)
    assert pairs == [] and len(fps) == 1 and len(fns) == 1


def test_direction_mismatch_blocks_match():
    pairs, fps, fns = match_anomalies([_d("2023-01", "rise")], [_d("2023-01", "fall")])
    assert pairs == [] and len(fps) == 1 and len(fns) == 1
    # ohne Richtungsprüfung matcht es
    pairs, _, _ = match_anomalies([_d("2023-01", "rise")], [_d("2023-01", "fall")],
                                  require_direction=False)
    assert len(pairs) == 1


def test_greedy_one_to_one_nearest_first():
    detected = [_d("2023-01"), _d("2023-02")]
    annotated = [_d("2023-02")]
    pairs, fps, fns = match_anomalies(detected, annotated, tolerance_months=1)
    # exakter Treffer gewinnt, der andere wird FP
    assert len(pairs) == 1
    assert pairs[0][0]["period"] == "2023-02"
    assert len(fps) == 1 and fps[0]["period"] == "2023-01"
    assert fns == []


def test_year_boundary_distance():
    pairs, _, _ = match_anomalies([_d("2024-01")], [_d("2023-12")], tolerance_months=1)
    assert len(pairs) == 1


def test_empty_inputs():
    pairs, fps, fns = match_anomalies([], [_d("2023-01")])
    assert pairs == [] and fps == [] and len(fns) == 1
    pairs, fps, fns = match_anomalies([_d("2023-01")], [])
    assert pairs == [] and len(fps) == 1 and fns == []
    pairs, fps, fns = match_anomalies([], [])
    assert pairs == [] and fps == [] and fns == []


def test_compute_metrics():
    m = compute_metrics(2, 0, 0)
    assert m == {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    m = compute_metrics(1, 1, 1)
    assert m["precision"] == 0.5 and m["recall"] == 0.5 and m["f1"] == 0.5
    m = compute_metrics(0, 0, 0)
    assert m == {"precision": 0.0, "recall": 0.0, "f1": 0.0}


def test_load_annotations_demo3():
    path = os.path.join(os.path.dirname(__file__), '..', '..',
                        'annotations', 'demo3_annotations.json')
    data = load_annotations(path)
    assert data["company_id"] == 3
    assert len(data["annotated_anomalies"]) == 2
    assert data["annotated_anomalies"][0]["direction"] == "fall"
