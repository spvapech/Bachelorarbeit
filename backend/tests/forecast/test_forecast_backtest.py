"""
Backtest-Validierung der Prognose-Engine
Vergleicht Holt's Exponential Smoothing mit dem Durchschnitt-Fallback
auf synthetischen, realistischen Bewertungszeitreihen für 3 Beispielunternehmen.

Ausführung:
    uv run python -m pytest tests/forecast/test_forecast_backtest.py -v -s
    uv run python tests/forecast/test_forecast_backtest.py
"""

import math
import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from routes.analytics import calculate_forecast, _fallback_forecast_average


# ─── Hilfsfunktionen ─────────────────────────────────────────────────────────

def _make_historical(scores: list[float], start_year: int = 2023, start_month: int = 1) -> list[dict]:
    """Erstellt historische Monatsdaten aus einer Score-Liste."""
    data = []
    for i, score in enumerate(scores):
        month_offset = start_month + i
        year = start_year + (month_offset - 1) // 12
        month = ((month_offset - 1) % 12) + 1
        date_obj = datetime(year, month, 1)
        data.append({
            "date": date_obj.strftime("%Y-%m"),
            "date_display": date_obj.strftime("%b %Y"),
            "score": round(score, 2),
            "count": 10,
            "is_forecast": False
        })
    return data


def calc_mae(actual: list[float], predicted: list[float]) -> float:
    """Mean Absolute Error."""
    return sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual)


def calc_rmse(actual: list[float], predicted: list[float]) -> float:
    """Root Mean Squared Error."""
    mse = sum((a - p) ** 2 for a, p in zip(actual, predicted)) / len(actual)
    return math.sqrt(mse)


def calc_mape(actual: list[float], predicted: list[float]) -> float:
    """Mean Absolute Percentage Error (in %)."""
    return sum(abs((a - p) / a) * 100 for a, p in zip(actual, predicted) if a != 0) / len(actual)


def run_backtest(all_scores: list[float], train_months: int, test_months: int,
                 start_year: int = 2023, start_month: int = 1) -> dict:
    """
    Führt einen Backtest durch: Trainiert auf den ersten `train_months` Monaten,
    prognostiziert `test_months` Monate und vergleicht mit den echten Werten.
    """
    train_data = _make_historical(all_scores[:train_months], start_year, start_month)
    actual_scores = all_scores[train_months:train_months + test_months]

    # Holt's Method
    holt_result = calculate_forecast(train_data, test_months)
    holt_scores = [e["score"] for e in holt_result]

    # Fallback (Durchschnitt)
    y_values = [p["score"] for p in train_data]
    fallback_result = _fallback_forecast_average(train_data, test_months, y_values)
    fallback_scores = [e["score"] for e in fallback_result]

    return {
        "actual": actual_scores,
        "holt_predicted": holt_scores,
        "fallback_predicted": fallback_scores,
        "holt_mae": round(calc_mae(actual_scores, holt_scores), 4),
        "holt_rmse": round(calc_rmse(actual_scores, holt_scores), 4),
        "holt_mape": round(calc_mape(actual_scores, holt_scores), 2),
        "fallback_mae": round(calc_mae(actual_scores, fallback_scores), 4),
        "fallback_rmse": round(calc_rmse(actual_scores, fallback_scores), 4),
        "fallback_mape": round(calc_mape(actual_scores, fallback_scores), 2),
    }


# ─── Unternehmensdaten (realistische synthetische Zeitreihen) ─────────────────

# Unternehmen A: TechVision GmbH — leichter Aufwärtstrend (verbesserndes Unternehmen)
# 18 Monate: 12 Training + 6 Test
COMPANY_A_SCORES = [
    3.10, 3.15, 3.20, 3.25, 3.18, 3.30, 3.35, 3.28, 3.40, 3.45, 3.50, 3.55,  # Training
    3.58, 3.60, 3.55, 3.65, 3.70, 3.68                                         # Test
]

# Unternehmen B: LogistikPro AG — stabil mit leichten Schwankungen
COMPANY_B_SCORES = [
    3.80, 3.75, 3.82, 3.78, 3.85, 3.80, 3.77, 3.83, 3.79, 3.84, 3.81, 3.82,  # Training
    3.80, 3.83, 3.79, 3.85, 3.81, 3.82                                         # Test
]

# Unternehmen C: ServiceFirst KG — Abwärtstrend (Problem-Unternehmen)
COMPANY_C_SCORES = [
    4.20, 4.10, 4.05, 3.95, 3.90, 3.85, 3.75, 3.70, 3.60, 3.55, 3.50, 3.45,  # Training
    3.40, 3.35, 3.30, 3.28, 3.25, 3.20                                         # Test
]

TRAIN_MONTHS = 12
TEST_MONTHS = 6


# ═══════════════════════════════════════════════════════════════════════════════
# Backtest-Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBacktestCompanyA:
    """Backtest: TechVision GmbH — Aufwärtstrend."""

    def test_holt_mae_acceptable(self):
        """Test: MAE von Holt liegt unter 0.5 Sterne für TechVision GmbH."""
        result = run_backtest(COMPANY_A_SCORES, TRAIN_MONTHS, TEST_MONTHS)
        assert result["holt_mae"] < 0.5, f"Holt MAE {result['holt_mae']} zu hoch"
        print(f"\n✓ TechVision GmbH (Aufwärtstrend)")
        print(f"  Holt  — MAE: {result['holt_mae']}, RMSE: {result['holt_rmse']}, MAPE: {result['holt_mape']}%")
        print(f"  Actual:    {result['actual']}")
        print(f"  Holt:      {result['holt_predicted']}")

    def test_holt_rmse_acceptable(self):
        """Test: RMSE von Holt liegt unter 0.5 Sterne."""
        result = run_backtest(COMPANY_A_SCORES, TRAIN_MONTHS, TEST_MONTHS)
        assert result["holt_rmse"] < 0.5, f"Holt RMSE {result['holt_rmse']} zu hoch"
        print(f"\n✓ TechVision GmbH — RMSE: {result['holt_rmse']}")

    def test_holt_beats_fallback(self):
        """Test: Holt schlägt Fallback bei Aufwärtstrend."""
        result = run_backtest(COMPANY_A_SCORES, TRAIN_MONTHS, TEST_MONTHS)
        assert result["holt_mae"] <= result["fallback_mae"], \
            f"Holt MAE ({result['holt_mae']}) > Fallback MAE ({result['fallback_mae']})"
        print(f"\n✓ Holt ({result['holt_mae']}) ≤ Fallback ({result['fallback_mae']})")


class TestBacktestCompanyB:
    """Backtest: LogistikPro AG — stabile Bewertungen."""

    def test_holt_mae_acceptable(self):
        """Test: MAE von Holt liegt unter 0.5 Sterne für LogistikPro AG."""
        result = run_backtest(COMPANY_B_SCORES, TRAIN_MONTHS, TEST_MONTHS)
        assert result["holt_mae"] < 0.5, f"Holt MAE {result['holt_mae']} zu hoch"
        print(f"\n✓ LogistikPro AG (stabil)")
        print(f"  Holt  — MAE: {result['holt_mae']}, RMSE: {result['holt_rmse']}, MAPE: {result['holt_mape']}%")
        print(f"  Actual:    {result['actual']}")
        print(f"  Holt:      {result['holt_predicted']}")

    def test_holt_rmse_acceptable(self):
        """Test: RMSE von Holt liegt unter 0.5 Sterne."""
        result = run_backtest(COMPANY_B_SCORES, TRAIN_MONTHS, TEST_MONTHS)
        assert result["holt_rmse"] < 0.5, f"Holt RMSE {result['holt_rmse']} zu hoch"
        print(f"\n✓ LogistikPro AG — RMSE: {result['holt_rmse']}")

    def test_fallback_competitive_on_stable(self):
        """Test: Bei stabilen Daten ist Fallback fast so gut wie Holt."""
        result = run_backtest(COMPANY_B_SCORES, TRAIN_MONTHS, TEST_MONTHS)
        # Differenz sollte klein sein bei stabilen Daten
        diff = abs(result["holt_mae"] - result["fallback_mae"])
        assert diff < 0.2, f"Differenz {diff} unerwartet groß bei stabilen Daten"
        print(f"\n✓ Stabile Daten → Holt/Fallback-Differenz gering: {diff:.4f}")


class TestBacktestCompanyC:
    """Backtest: ServiceFirst KG — Abwärtstrend."""

    def test_holt_mae_acceptable(self):
        """Test: MAE von Holt liegt unter 0.5 Sterne für ServiceFirst KG."""
        result = run_backtest(COMPANY_C_SCORES, TRAIN_MONTHS, TEST_MONTHS)
        assert result["holt_mae"] < 0.5, f"Holt MAE {result['holt_mae']} zu hoch"
        print(f"\n✓ ServiceFirst KG (Abwärtstrend)")
        print(f"  Holt  — MAE: {result['holt_mae']}, RMSE: {result['holt_rmse']}, MAPE: {result['holt_mape']}%")
        print(f"  Actual:    {result['actual']}")
        print(f"  Holt:      {result['holt_predicted']}")

    def test_holt_rmse_acceptable(self):
        """Test: RMSE von Holt liegt unter 0.5 Sterne."""
        result = run_backtest(COMPANY_C_SCORES, TRAIN_MONTHS, TEST_MONTHS)
        assert result["holt_rmse"] < 0.5, f"Holt RMSE {result['holt_rmse']} zu hoch"
        print(f"\n✓ ServiceFirst KG — RMSE: {result['holt_rmse']}")

    def test_holt_beats_fallback(self):
        """Test: Holt schlägt Fallback bei Abwärtstrend."""
        result = run_backtest(COMPANY_C_SCORES, TRAIN_MONTHS, TEST_MONTHS)
        assert result["holt_mae"] <= result["fallback_mae"], \
            f"Holt MAE ({result['holt_mae']}) > Fallback MAE ({result['fallback_mae']})"
        print(f"\n✓ Holt ({result['holt_mae']}) ≤ Fallback ({result['fallback_mae']})")


# ═══════════════════════════════════════════════════════════════════════════════
# Gesamtvergleich Holt vs. Fallback
# ═══════════════════════════════════════════════════════════════════════════════

class TestHoltVsFallbackComparison:
    """Gesamtvergleich: Holt's Method vs. Durchschnitt-Fallback über alle Unternehmen."""

    def test_holt_lower_average_mae(self):
        """Test: Holt hat über alle 3 Unternehmen einen niedrigeren Durchschnitts-MAE."""
        companies = [
            ("TechVision GmbH", COMPANY_A_SCORES),
            ("LogistikPro AG", COMPANY_B_SCORES),
            ("ServiceFirst KG", COMPANY_C_SCORES),
        ]

        holt_maes = []
        fallback_maes = []

        for name, scores in companies:
            result = run_backtest(scores, TRAIN_MONTHS, TEST_MONTHS)
            holt_maes.append(result["holt_mae"])
            fallback_maes.append(result["fallback_mae"])

        avg_holt = sum(holt_maes) / len(holt_maes)
        avg_fallback = sum(fallback_maes) / len(fallback_maes)

        assert avg_holt <= avg_fallback, \
            f"Durchschnitt Holt MAE ({avg_holt:.4f}) > Fallback MAE ({avg_fallback:.4f})"

        print(f"\n✓ Gesamtvergleich über 3 Unternehmen:")
        print(f"  ∅ Holt MAE:     {avg_holt:.4f}")
        print(f"  ∅ Fallback MAE: {avg_fallback:.4f}")
        print(f"  Verbesserung:   {((avg_fallback - avg_holt) / avg_fallback * 100):.1f}%")

    def test_holt_lower_average_mape(self):
        """Test: Holt hat über alle 3 Unternehmen einen niedrigeren Durchschnitts-MAPE."""
        companies = [
            ("TechVision GmbH", COMPANY_A_SCORES),
            ("LogistikPro AG", COMPANY_B_SCORES),
            ("ServiceFirst KG", COMPANY_C_SCORES),
        ]

        holt_mapes = []
        fallback_mapes = []

        for name, scores in companies:
            result = run_backtest(scores, TRAIN_MONTHS, TEST_MONTHS)
            holt_mapes.append(result["holt_mape"])
            fallback_mapes.append(result["fallback_mape"])

        avg_holt = sum(holt_mapes) / len(holt_mapes)
        avg_fallback = sum(fallback_mapes) / len(fallback_mapes)

        assert avg_holt <= avg_fallback, \
            f"Durchschnitt Holt MAPE ({avg_holt:.2f}%) > Fallback MAPE ({avg_fallback:.2f}%)"

        print(f"\n✓ MAPE-Vergleich über 3 Unternehmen:")
        print(f"  ∅ Holt MAPE:     {avg_holt:.2f}%")
        print(f"  ∅ Fallback MAPE: {avg_fallback:.2f}%")


# ═══════════════════════════════════════════════════════════════════════════════
# Runner für direkten Aufruf mit formatierter Ausgabe
# ═══════════════════════════════════════════════════════════════════════════════

def run_all_tests():
    """Führt den vollständigen Backtest aus und gibt eine formatierte Zusammenfassung aus."""
    print("=" * 75)
    print("PROGNOSE-ENGINE — BACKTEST-VALIDIERUNG")
    print("Holt's Exponential Smoothing vs. Durchschnitt-Fallback")
    print("=" * 75)

    companies = [
        ("TechVision GmbH", "Aufwärtstrend", COMPANY_A_SCORES),
        ("LogistikPro AG", "Stabil", COMPANY_B_SCORES),
        ("ServiceFirst KG", "Abwärtstrend", COMPANY_C_SCORES),
    ]

    all_results = []

    for name, trend, scores in companies:
        result = run_backtest(scores, TRAIN_MONTHS, TEST_MONTHS)
        all_results.append((name, trend, result))

        print(f"\n{'─' * 75}")
        print(f"  {name} ({trend})")
        print(f"{'─' * 75}")
        print(f"  Training: {TRAIN_MONTHS} Monate | Test: {TEST_MONTHS} Monate")
        print()
        print(f"  Monat       | Actual | Holt   | Fallback | Holt-Δ  | Fallback-Δ")
        print(f"  {'─' * 67}")

        for i in range(TEST_MONTHS):
            a = result["actual"][i]
            h = result["holt_predicted"][i]
            f = result["fallback_predicted"][i]
            print(f"  Monat {i+1:2d}    | {a:.2f}  | {h:.2f}  | {f:.2f}    | {abs(a-h):+.3f}  | {abs(a-f):+.3f}")

        print()
        print(f"  {'':14s} HOLT          FALLBACK")
        print(f"  MAE:         {result['holt_mae']:.4f}        {result['fallback_mae']:.4f}")
        print(f"  RMSE:        {result['holt_rmse']:.4f}        {result['fallback_rmse']:.4f}")
        print(f"  MAPE:        {result['holt_mape']:.2f}%        {result['fallback_mape']:.2f}%")

    # Gesamtvergleich
    print(f"\n{'=' * 75}")
    print("GESAMTVERGLEICH")
    print(f"{'=' * 75}")
    print()
    print(f"  {'Unternehmen':<25s} | {'Trend':<15s} | {'Holt MAE':>10s} | {'Fallback MAE':>13s} | {'Gewinner':>10s}")
    print(f"  {'─' * 80}")

    holt_wins = 0
    for name, trend, result in all_results:
        winner = "Holt ✓" if result["holt_mae"] <= result["fallback_mae"] else "Fallback ✓"
        if result["holt_mae"] <= result["fallback_mae"]:
            holt_wins += 1
        print(f"  {name:<25s} | {trend:<15s} | {result['holt_mae']:>10.4f} | {result['fallback_mae']:>13.4f} | {winner:>10s}")

    avg_holt = sum(r["holt_mae"] for _, _, r in all_results) / len(all_results)
    avg_fallback = sum(r["fallback_mae"] for _, _, r in all_results) / len(all_results)
    improvement = (avg_fallback - avg_holt) / avg_fallback * 100

    print(f"\n  ∅ Holt MAE:     {avg_holt:.4f}")
    print(f"  ∅ Fallback MAE: {avg_fallback:.4f}")
    print(f"  Verbesserung:   {improvement:.1f}% weniger Fehler durch Holt")
    print(f"  Holt gewinnt:   {holt_wins}/{len(all_results)} Unternehmen")

    print(f"\n{'=' * 75}")
    if holt_wins >= 2:
        print("✓ Holt's Method ist dem Durchschnitt-Fallback überlegen.")
    else:
        print("⚠ Holt's Method zeigt keinen klaren Vorteil gegenüber dem Fallback.")
    print(f"{'=' * 75}")


if __name__ == "__main__":
    run_all_tests()
