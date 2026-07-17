"""
Funktionale Validierung der Anomalieerkennung (DZ1).

Vergleicht automatisch erkannte Anomalien mit manuell annotierten
auffälligen Zeiträumen (Precision/Recall/F1 mit Monats-Toleranz) und
unterstützt einen Parameter-Sweep für die Kalibrierung.

Verwendung (aus backend/):
    uv run python scripts/validate_anomaly_detection.py \
        --company-id 3 --annotations annotations/demo3_annotations.json \
        --method both --sweep

Annotationsformat: siehe annotations/demo3_annotations.json.
"""

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.anomaly_detection_service import (  # noqa: E402
    AnomalyParams,
    build_monthly_series,
    detect_anomalies,
)

PELT_PENALTY_GRID = [0.2, 0.3, 0.5, 0.8, 1.0, 1.5]
ZSCORE_THRESHOLD_GRID = [1.5, 2.0, 2.5, 3.0]


def load_annotations(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if "annotated_anomalies" not in data:
        raise ValueError("Annotationsdatei benötigt den Schlüssel 'annotated_anomalies'")
    return data


def _period_index(period: str) -> int:
    return int(period[:4]) * 12 + int(period[5:7]) - 1


def match_anomalies(detected: List[Dict[str, Any]], annotated: List[Dict[str, Any]],
                    tolerance_months: int = 1,
                    require_direction: bool = True) -> Tuple[List[Tuple[dict, dict]], List[dict], List[dict]]:
    """
    Greedy-1:1-Matching (nächster Monat zuerst) zwischen erkannten und
    annotierten Anomalien. Rückgabe: (TP-Paare, FP-Liste, FN-Liste).
    """
    candidates = []
    for di, d in enumerate(detected):
        for ai, a in enumerate(annotated):
            distance = abs(_period_index(d["period"]) - _period_index(a["period"]))
            if distance > tolerance_months:
                continue
            if require_direction and a.get("direction") and d.get("direction") != a["direction"]:
                continue
            candidates.append((distance, di, ai))

    candidates.sort()
    used_detected: set = set()
    used_annotated: set = set()
    pairs: List[Tuple[dict, dict]] = []
    for _, di, ai in candidates:
        if di in used_detected or ai in used_annotated:
            continue
        used_detected.add(di)
        used_annotated.add(ai)
        pairs.append((detected[di], annotated[ai]))

    false_positives = [d for i, d in enumerate(detected) if i not in used_detected]
    false_negatives = [a for i, a in enumerate(annotated) if i not in used_annotated]
    return pairs, false_positives, false_negatives


def compute_metrics(tp: int, fp: int, fn: int) -> Dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3)}


def _param_sets(args) -> List[AnomalyParams]:
    methods = ["pelt", "zscore"] if args.method == "both" else [args.method]
    sets: List[AnomalyParams] = []
    for method in methods:
        if args.sweep:
            grid = PELT_PENALTY_GRID if method == "pelt" else ZSCORE_THRESHOLD_GRID
            for value in grid:
                sets.append(AnomalyParams(
                    method=method,
                    penalty=value if method == "pelt" else args.penalty,
                    z_threshold=value if method == "zscore" else args.z_threshold,
                    min_size=args.min_size, z_window=args.z_window,
                    min_reviews_per_month=args.min_reviews,
                    min_magnitude=args.min_magnitude,
                ))
        else:
            sets.append(AnomalyParams(
                method=method, penalty=args.penalty, z_threshold=args.z_threshold,
                min_size=args.min_size, z_window=args.z_window,
                min_reviews_per_month=args.min_reviews,
                min_magnitude=args.min_magnitude,
            ))
    return sets


def _param_summary(p: AnomalyParams) -> str:
    if p.method == "pelt":
        return f"pen={p.penalty}, min_size={p.min_size}"
    return f"z={p.z_threshold}, window={p.z_window}"


def main() -> None:
    parser = argparse.ArgumentParser(description="DZ1: Validierung der Anomalieerkennung")
    parser.add_argument("--company-id", type=int, required=True)
    parser.add_argument("--annotations", required=True,
                        help="Pfad zur JSON-Annotationsdatei")
    parser.add_argument("--method", choices=["pelt", "zscore", "both"], default="both")
    parser.add_argument("--dimension", default=None,
                        help="Default: Dimension aus der Annotationsdatei")
    parser.add_argument("--source", default=None,
                        help="Default: Quelle aus der Annotationsdatei")
    parser.add_argument("--tolerance-months", type=int, default=1)
    parser.add_argument("--ignore-direction", action="store_true",
                        help="Richtung beim Matching nicht prüfen")
    parser.add_argument("--penalty", type=float, default=0.5)
    parser.add_argument("--min-size", type=int, default=2)
    parser.add_argument("--z-threshold", type=float, default=2.0)
    parser.add_argument("--z-window", type=int, default=6)
    parser.add_argument("--min-reviews", type=int, default=3)
    parser.add_argument("--min-magnitude", type=float, default=0.3)
    parser.add_argument("--sweep", action="store_true",
                        help="Parameter-Grid statt Einzelwerten")
    parser.add_argument("--out", default=None, help="Ergebnisse als CSV speichern")
    args = parser.parse_args()

    annotations = load_annotations(args.annotations)
    annotated = annotations["annotated_anomalies"]
    source = args.source or annotations.get("source", "employee")
    dimension = args.dimension or annotations.get("dimension", "durchschnittsbewertung")

    series = build_monthly_series(args.company_id, source, dimension,
                                  min_reviews=args.min_reviews)
    print(f"Unternehmen {args.company_id} · Quelle {source} · Dimension {dimension}")
    print(f"Serie: {len(series)} Monate ({series[0]['period']} – {series[-1]['period']})"
          if series else "Serie: leer")
    print(f"Annotationen: {len(annotated)} · Toleranz ±{args.tolerance_months} Monat(e)\n")

    header = f"{'Methode':<8} {'Parameter':<22} {'TP':>3} {'FP':>3} {'FN':>3} " \
             f"{'Precision':>10} {'Recall':>8} {'F1':>7}"
    print(header)
    print("-" * len(header))

    results: List[Dict[str, Any]] = []
    for params in _param_sets(args):
        detected = detect_anomalies(series, params, dimension, source)
        pairs, fps, fns = match_anomalies(
            detected, annotated, tolerance_months=args.tolerance_months,
            require_direction=not args.ignore_direction,
        )
        metrics = compute_metrics(len(pairs), len(fps), len(fns))
        row = {
            "method": params.method,
            "params": _param_summary(params),
            "tp": len(pairs), "fp": len(fps), "fn": len(fns),
            **metrics,
        }
        results.append(row)
        print(f"{row['method']:<8} {row['params']:<22} {row['tp']:>3} {row['fp']:>3} "
              f"{row['fn']:>3} {row['precision']:>10.3f} {row['recall']:>8.3f} {row['f1']:>7.3f}")

    best = max(results, key=lambda r: (r["f1"], r["precision"]))
    print(f"\nBeste Konfiguration: {best['method']} ({best['params']}) — F1 {best['f1']:.3f}")

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
        print(f"Ergebnisse gespeichert: {args.out}")


if __name__ == "__main__":
    main()
