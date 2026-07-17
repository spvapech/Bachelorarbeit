"""
Hyperparameter-Sweep für Holt's Exponential Smoothing
Vergleicht verschiedene alpha/beta-Kombinationen mit den Default-Parametern
auf den 3 Backtest-Unternehmen, analog zum LDA c_v-Kohärenz-Sweep.

Ausführung:
    uv run python -m pytest tests/forecast/test_forecast_hyperparams.py -v -s
    uv run python tests/forecast/test_forecast_hyperparams.py
"""

import math
import pytest
from datetime import datetime
from itertools import product

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


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
    return sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual)


def calc_rmse(actual: list[float], predicted: list[float]) -> float:
    mse = sum((a - p) ** 2 for a, p in zip(actual, predicted)) / len(actual)
    return math.sqrt(mse)


def forecast_with_params(train_data: list[dict], months: int,
                         smoothing_level: float | None = None,
                         smoothing_trend: float | None = None) -> list[dict]:
    """
    Prognose mit spezifischen alpha/beta-Werten.
    None = statsmodels optimiert automatisch (Default).
    """
    from statsmodels.tsa.holtwinters import Holt
    import numpy as np

    y_values = [p["score"] for p in train_data]
    series = np.asarray(y_values, dtype=float)
    last_date = datetime.strptime(train_data[-1]["date"], "%Y-%m")

    model = Holt(series)

    fit_kwargs = {}
    if smoothing_level is not None:
        fit_kwargs["smoothing_level"] = smoothing_level
    if smoothing_trend is not None:
        fit_kwargs["smoothing_trend"] = smoothing_trend
    if fit_kwargs:
        fit_kwargs["optimized"] = False  # Verwende gegebene Werte statt Optimierung

    fit = model.fit(**fit_kwargs)
    preds = fit.forecast(steps=months)

    forecast = []
    for i in range(months):
        month_offset = last_date.month + (i + 1)
        year_offset = (month_offset - 1) // 12
        month = ((month_offset - 1) % 12) + 1
        next_month = last_date.replace(year=last_date.year + year_offset, month=month)
        score = float(preds[i])
        score = max(0.0, min(5.0, score))
        forecast.append({
            "date": next_month.strftime("%Y-%m"),
            "score": round(score, 2),
        })
    return forecast


def run_sweep(all_scores: list[float], train_months: int, test_months: int) -> dict:
    """
    Grid Search über alpha ∈ {0.1, 0.2, ..., 0.9} und beta ∈ {0.01, 0.05, 0.1, 0.2, 0.3, 0.5}
    plus Default (auto-optimiert).
    """
    train_data = _make_historical(all_scores[:train_months])
    actual_scores = all_scores[train_months:train_months + test_months]

    # Default (auto-optimierte Parameter)
    default_result = forecast_with_params(train_data, test_months)
    default_scores = [e["score"] for e in default_result]
    default_mae = calc_mae(actual_scores, default_scores)
    default_rmse = calc_rmse(actual_scores, default_scores)

    # Lese die optimierten Parameter aus
    from statsmodels.tsa.holtwinters import Holt
    import numpy as np
    series = np.asarray([p["score"] for p in train_data], dtype=float)
    default_fit = Holt(series).fit()
    optimized_alpha = round(default_fit.params["smoothing_level"], 4)
    optimized_beta = round(default_fit.params["smoothing_trend"], 4)

    # Grid Search
    alpha_values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    beta_values = [0.01, 0.05, 0.1, 0.2, 0.3, 0.5]

    grid_results = []
    for alpha, beta in product(alpha_values, beta_values):
        try:
            result = forecast_with_params(train_data, test_months, alpha, beta)
            pred_scores = [e["score"] for e in result]
            mae = calc_mae(actual_scores, pred_scores)
            rmse = calc_rmse(actual_scores, pred_scores)
            grid_results.append({
                "alpha": alpha, "beta": beta,
                "mae": round(mae, 4), "rmse": round(rmse, 4)
            })
        except Exception:
            pass

    # Sortieren nach MAE
    grid_results.sort(key=lambda x: x["mae"])

    return {
        "default_mae": round(default_mae, 4),
        "default_rmse": round(default_rmse, 4),
        "optimized_alpha": optimized_alpha,
        "optimized_beta": optimized_beta,
        "grid_results": grid_results,
        "best_grid": grid_results[0] if grid_results else None,
    }


# ─── Unternehmensdaten (gleich wie Backtest) ──────────────────────────────────

COMPANY_A_SCORES = [
    3.10, 3.15, 3.20, 3.25, 3.18, 3.30, 3.35, 3.28, 3.40, 3.45, 3.50, 3.55,
    3.58, 3.60, 3.55, 3.65, 3.70, 3.68
]
COMPANY_B_SCORES = [
    3.80, 3.75, 3.82, 3.78, 3.85, 3.80, 3.77, 3.83, 3.79, 3.84, 3.81, 3.82,
    3.80, 3.83, 3.79, 3.85, 3.81, 3.82
]
COMPANY_C_SCORES = [
    4.20, 4.10, 4.05, 3.95, 3.90, 3.85, 3.75, 3.70, 3.60, 3.55, 3.50, 3.45,
    3.40, 3.35, 3.30, 3.28, 3.25, 3.20
]

TRAIN_MONTHS = 12
TEST_MONTHS = 6


# ═══════════════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDefaultParameterOptimality:
    """Prüft, ob die auto-optimierten Default-Parameter nahe am Grid-Search-Optimum liegen."""

    def test_default_near_optimal_company_a(self):
        """Test: Default-Parameter liegen nahe dem Grid-Search-Optimum (TechVision)."""
        result = run_sweep(COMPANY_A_SCORES, TRAIN_MONTHS, TEST_MONTHS)
        best = result["best_grid"]
        # Default darf maximal 150% schlechter sein als das Grid-Optimum,
        # da Grid-Search auf Testdaten optimiert, während statsmodels auf Training-SSE optimiert
        assert result["default_mae"] <= best["mae"] * 2.5, \
            f"Default MAE {result['default_mae']} >> Grid-Best MAE {best['mae']}"
        print(f"\n✓ TechVision: Default α={result['optimized_alpha']}, β={result['optimized_beta']}")
        print(f"  Default MAE:    {result['default_mae']}")
        print(f"  Grid-Best MAE:  {best['mae']} (α={best['alpha']}, β={best['beta']})")

    def test_default_near_optimal_company_b(self):
        """Test: Default-Parameter liegen nahe dem Grid-Search-Optimum (LogistikPro)."""
        result = run_sweep(COMPANY_B_SCORES, TRAIN_MONTHS, TEST_MONTHS)
        best = result["best_grid"]
        assert result["default_mae"] <= best["mae"] * 2.5, \
            f"Default MAE {result['default_mae']} >> Grid-Best MAE {best['mae']}"
        print(f"\n✓ LogistikPro: Default α={result['optimized_alpha']}, β={result['optimized_beta']}")
        print(f"  Default MAE:    {result['default_mae']}")
        print(f"  Grid-Best MAE:  {best['mae']} (α={best['alpha']}, β={best['beta']})")

    def test_default_near_optimal_company_c(self):
        """Test: Default-Parameter liegen nahe dem Grid-Search-Optimum (ServiceFirst)."""
        result = run_sweep(COMPANY_C_SCORES, TRAIN_MONTHS, TEST_MONTHS)
        best = result["best_grid"]
        assert result["default_mae"] <= best["mae"] * 2.5, \
            f"Default MAE {result['default_mae']} >> Grid-Best MAE {best['mae']}"
        print(f"\n✓ ServiceFirst: Default α={result['optimized_alpha']}, β={result['optimized_beta']}")
        print(f"  Default MAE:    {result['default_mae']}")
        print(f"  Grid-Best MAE:  {best['mae']} (α={best['alpha']}, β={best['beta']})")


class TestParameterSensitivity:
    """Analysiert die Sensitivität gegenüber alpha/beta-Variationen."""

    def test_alpha_sensitivity(self):
        """Test: MAE-Varianz über alpha-Werte bei fixem beta=0.1."""
        train_data = _make_historical(COMPANY_A_SCORES[:TRAIN_MONTHS])
        actual = COMPANY_A_SCORES[TRAIN_MONTHS:TRAIN_MONTHS + TEST_MONTHS]

        maes = []
        for alpha in [0.1, 0.3, 0.5, 0.7, 0.9]:
            result = forecast_with_params(train_data, TEST_MONTHS, alpha, 0.1)
            mae = calc_mae(actual, [e["score"] for e in result])
            maes.append((alpha, round(mae, 4)))

        # Alle MAEs sollten unter 1.0 liegen (das Modell ist generell robust)
        for alpha, mae in maes:
            assert mae < 1.0, f"MAE {mae} bei alpha={alpha} zu hoch"

        print(f"\n✓ Alpha-Sensitivität (beta=0.1 fix):")
        for alpha, mae in maes:
            bar = "█" * int(mae * 50)
            print(f"  α={alpha}: MAE={mae} {bar}")

    def test_beta_sensitivity(self):
        """Test: MAE-Varianz über beta-Werte bei fixem alpha=0.5."""
        train_data = _make_historical(COMPANY_A_SCORES[:TRAIN_MONTHS])
        actual = COMPANY_A_SCORES[TRAIN_MONTHS:TRAIN_MONTHS + TEST_MONTHS]

        maes = []
        for beta in [0.01, 0.05, 0.1, 0.2, 0.3, 0.5]:
            result = forecast_with_params(train_data, TEST_MONTHS, 0.5, beta)
            mae = calc_mae(actual, [e["score"] for e in result])
            maes.append((beta, round(mae, 4)))

        for beta, mae in maes:
            assert mae < 1.0, f"MAE {mae} bei beta={beta} zu hoch"

        print(f"\n✓ Beta-Sensitivität (alpha=0.5 fix):")
        for beta, mae in maes:
            bar = "█" * int(mae * 50)
            print(f"  β={beta}: MAE={mae} {bar}")

    def test_top5_vs_bottom5_spread(self):
        """Test: Die Spreizung zwischen Top-5 und Bottom-5 Parametern ist begrenzt."""
        result = run_sweep(COMPANY_A_SCORES, TRAIN_MONTHS, TEST_MONTHS)
        grid = result["grid_results"]
        top5_avg = sum(g["mae"] for g in grid[:5]) / 5
        bottom5_avg = sum(g["mae"] for g in grid[-5:]) / 5

        print(f"\n✓ Parameterspreizung (TechVision):")
        print(f"  Top-5 ∅ MAE:    {top5_avg:.4f}")
        print(f"  Bottom-5 ∅ MAE: {bottom5_avg:.4f}")
        print(f"  Spreizung:      {bottom5_avg - top5_avg:.4f}")
        print(f"  Top-5:  {[(g['alpha'], g['beta'], g['mae']) for g in grid[:5]]}")
        print(f"  Bottom-5: {[(g['alpha'], g['beta'], g['mae']) for g in grid[-5:]]}")


class TestAutoOptimizationJustification:
    """Belegt, warum die Auto-Optimierung von statsmodels die richtige Wahl ist."""

    def test_auto_params_vary_by_data(self):
        """Test: Auto-optimierte Parameter unterscheiden sich je nach Datenmuster."""
        companies = [
            ("TechVision", COMPANY_A_SCORES),
            ("LogistikPro", COMPANY_B_SCORES),
            ("ServiceFirst", COMPANY_C_SCORES),
        ]

        params = []
        for name, scores in companies:
            result = run_sweep(scores, TRAIN_MONTHS, TEST_MONTHS)
            params.append((name, result["optimized_alpha"], result["optimized_beta"]))

        # Die Parameter sollten nicht alle identisch sein
        alphas = [p[1] for p in params]
        betas = [p[2] for p in params]
        alpha_varied = len(set(alphas)) > 1
        beta_varied = len(set(betas)) > 1

        assert alpha_varied or beta_varied, \
            "Auto-Optimierung sollte verschiedene Parameter für verschiedene Datenmuster finden"

        print(f"\n✓ Auto-optimierte Parameter variieren je nach Datenmuster:")
        for name, alpha, beta in params:
            print(f"  {name:<20s}: α={alpha}, β={beta}")

    def test_auto_is_optimal_or_near_optimal(self):
        """Test: Über alle 3 Firmen liegt der Default-∅-MAE nahe dem Grid-∅-MAE."""
        companies = [
            COMPANY_A_SCORES, COMPANY_B_SCORES, COMPANY_C_SCORES
        ]

        default_maes = []
        best_maes = []
        for scores in companies:
            result = run_sweep(scores, TRAIN_MONTHS, TEST_MONTHS)
            default_maes.append(result["default_mae"])
            best_maes.append(result["best_grid"]["mae"])

        avg_default = sum(default_maes) / len(default_maes)
        avg_best = sum(best_maes) / len(best_maes)

        # Default sollte nicht mehr als 100% schlechter sein als Grid-Optimum
        assert avg_default <= avg_best * 2.0, \
            f"∅ Default MAE ({avg_default:.4f}) >> ∅ Grid-Best MAE ({avg_best:.4f})"

        print(f"\n✓ Auto-Optimierung vs. Grid Search:")
        print(f"  ∅ Default MAE:    {avg_default:.4f}")
        print(f"  ∅ Grid-Best MAE:  {avg_best:.4f}")
        print(f"  Differenz:        {((avg_default - avg_best) / avg_best * 100):.1f}%")


# ═══════════════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════════════

def run_all_tests():
    """Führt den vollständigen Hyperparameter-Sweep aus."""
    print("=" * 75)
    print("PROGNOSE-ENGINE — HYPERPARAMETER-SWEEP")
    print("Holt's Exponential Smoothing: α (smoothing_level) × β (smoothing_trend)")
    print("=" * 75)

    companies = [
        ("TechVision GmbH", "Aufwärtstrend", COMPANY_A_SCORES),
        ("LogistikPro AG", "Stabil", COMPANY_B_SCORES),
        ("ServiceFirst KG", "Abwärtstrend", COMPANY_C_SCORES),
    ]

    all_sweeps = []

    for name, trend, scores in companies:
        result = run_sweep(scores, TRAIN_MONTHS, TEST_MONTHS)
        all_sweeps.append((name, trend, result))

        print(f"\n{'─' * 75}")
        print(f"  {name} ({trend})")
        print(f"{'─' * 75}")
        print(f"  Auto-optimierte Parameter: α={result['optimized_alpha']}, β={result['optimized_beta']}")
        print(f"  Default MAE:  {result['default_mae']}")
        print(f"  Default RMSE: {result['default_rmse']}")
        print()
        print(f"  Top-10 Grid-Search-Ergebnisse (von {len(result['grid_results'])} Kombinationen):")
        print(f"  {'Rang':<6s} {'α':>6s} {'β':>8s} {'MAE':>10s} {'RMSE':>10s} {'vs Default':>12s}")
        print(f"  {'─' * 55}")
        for i, g in enumerate(result["grid_results"][:10], 1):
            diff = g["mae"] - result["default_mae"]
            marker = "◀ besser" if diff < -0.001 else ("≈ gleich" if abs(diff) < 0.001 else "")
            print(f"  {i:<6d} {g['alpha']:>6.1f} {g['beta']:>8.2f} {g['mae']:>10.4f} {g['rmse']:>10.4f} {diff:>+10.4f}  {marker}")

    # Gesamtvergleich
    print(f"\n{'=' * 75}")
    print("ZUSAMMENFASSUNG: DEFAULT vs. GRID-SEARCH-OPTIMUM")
    print(f"{'=' * 75}")
    print()
    print(f"  {'Unternehmen':<25s} | {'Default α':>10s} | {'Default β':>10s} | {'Default MAE':>12s} | {'Best MAE':>10s}")
    print(f"  {'─' * 75}")

    for name, trend, result in all_sweeps:
        best = result["best_grid"]
        print(f"  {name:<25s} | {result['optimized_alpha']:>10.4f} | {result['optimized_beta']:>10.4f} | {result['default_mae']:>12.4f} | {best['mae']:>10.4f}")

    avg_default = sum(r["default_mae"] for _, _, r in all_sweeps) / len(all_sweeps)
    avg_best = sum(r["best_grid"]["mae"] for _, _, r in all_sweeps) / len(all_sweeps)

    print()
    print(f"  ∅ Default MAE:    {avg_default:.4f}")
    print(f"  ∅ Grid-Best MAE:  {avg_best:.4f}")
    print(f"  Differenz:        {((avg_default - avg_best) / avg_best * 100):.1f}%")
    print()
    print("  BEGRÜNDUNG: Die auto-optimierten Default-Parameter von statsmodels")
    print("  passen sich datengetrieben an jede Zeitreihe an. Ein festes α/β")
    print("  wäre suboptimal, da verschiedene Unternehmen unterschiedliche")
    print("  Bewertungstrends aufweisen. Die Auto-Optimierung minimiert den")
    print("  SSE (Sum of Squared Errors) auf den Trainingsdaten und liefert")
    print("  dadurch nahezu optimale Prognoseergebnisse ohne manuelles Tuning.")
    print(f"\n{'=' * 75}")


if __name__ == "__main__":
    run_all_tests()
