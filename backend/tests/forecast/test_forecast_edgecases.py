"""
Edge-Case-Analyse der Prognose-Engine
1. Verhalten bei weniger als 2 Datenpunkten
2. Extreme monotone Trends (steigend/fallend/sprunghaft)
3. Clamping-Analyse: Wie oft greift die [0, 5]-Begrenzung?

Ausführung:
    uv run python -m pytest tests/forecast/test_forecast_edgecases.py -v -s
    uv run python tests/forecast/test_forecast_edgecases.py
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


def count_clamped(forecast: list[dict]) -> dict:
    """Zählt wie viele Prognosewerte geclampt wurden."""
    clamped_low = sum(1 for e in forecast if e["score"] == 0.0)
    clamped_high = sum(1 for e in forecast if e["score"] == 5.0)
    return {
        "total": len(forecast),
        "clamped_low": clamped_low,
        "clamped_high": clamped_high,
        "clamped_total": clamped_low + clamped_high,
        "clamped_pct": round((clamped_low + clamped_high) / len(forecast) * 100, 1) if forecast else 0
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Verhalten bei unzureichenden Datenpunkten
# ═══════════════════════════════════════════════════════════════════════════════

class TestInsufficientData:
    """Systematische Prüfung des Verhaltens bei 0 und 1 Datenpunkten."""

    def test_empty_list(self):
        """Test: Leere Liste → leere Prognose."""
        result = calculate_forecast([], 6)
        assert result == []
        print(f"\n✓ Leere Liste → [] (korrekt)")

    def test_single_point(self):
        """Test: 1 Datenpunkt → leere Prognose."""
        data = _make_historical([3.5])
        result = calculate_forecast(data, 6)
        assert result == []
        print(f"\n✓ 1 Datenpunkt → [] (korrekt, Holt benötigt min. 2)")

    def test_zero_months_requested(self):
        """Test: 0 Monate angefordert → leere Prognose."""
        data = _make_historical([3.0, 3.5, 4.0])
        result = calculate_forecast(data, 0)
        assert result == []
        print(f"\n✓ 0 Monate angefordert → [] (korrekt)")

    def test_negative_months_requested(self):
        """Test: Negative Monate → leere Prognose."""
        data = _make_historical([3.0, 3.5])
        result = calculate_forecast(data, -5)
        assert result == []
        print(f"\n✓ Negative Monate → [] (korrekt)")

    def test_exactly_two_points(self):
        """Test: Genau 2 Punkte → Prognose funktioniert (Minimum)."""
        data = _make_historical([3.0, 3.5])
        result = calculate_forecast(data, 6)
        assert len(result) == 6, f"2 Punkte sollten Prognose liefern, erhalten: {len(result)}"
        for e in result:
            assert 0.0 <= e["score"] <= 5.0
        print(f"\n✓ 2 Datenpunkte → Prognose möglich: {[e['score'] for e in result]}")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Extreme monotone Trends
# ═══════════════════════════════════════════════════════════════════════════════

class TestExtremeTrends:
    """Verhalten bei extrem steigenden und fallenden Bewertungen."""

    def test_strongly_rising_to_max(self):
        """Test: Stark steigend (nahe 5.0) → Prognose bleibt ≤ 5.0."""
        data = _make_historical([3.0, 3.5, 4.0, 4.3, 4.5, 4.7, 4.8, 4.85, 4.9, 4.95, 4.98, 5.0])
        result = calculate_forecast(data, 12)
        assert all(e["score"] <= 5.0 for e in result), "Prognosewerte über 5.0 gefunden"
        clamped = count_clamped(result)
        print(f"\n✓ Stark steigend → alle Werte ≤ 5.0")
        print(f"  Scores:  {[e['score'] for e in result]}")
        print(f"  Clamped: {clamped['clamped_high']}/{clamped['total']} auf 5.0")

    def test_strongly_falling_to_min(self):
        """Test: Stark fallend (nahe 0.0) → Prognose bleibt ≥ 0.0."""
        data = _make_historical([2.0, 1.8, 1.5, 1.2, 0.9, 0.7, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05])
        result = calculate_forecast(data, 12)
        assert all(e["score"] >= 0.0 for e in result), "Prognosewerte unter 0.0 gefunden"
        clamped = count_clamped(result)
        print(f"\n✓ Stark fallend → alle Werte ≥ 0.0")
        print(f"  Scores:  {[e['score'] for e in result]}")
        print(f"  Clamped: {clamped['clamped_low']}/{clamped['total']} auf 0.0")

    def test_monotonic_linear_increase(self):
        """Test: Perfekt linearer Anstieg → Prognose folgt dem Trend."""
        data = _make_historical([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5])
        result = calculate_forecast(data, 6)
        # Holt sollte den linearen Trend extrapolieren
        assert result[0]["score"] >= 4.5, \
            f"Erster Prognosewert {result[0]['score']} sollte ≥ 4.5 sein bei linearem Anstieg"
        clamped = count_clamped(result)
        print(f"\n✓ Linearer Anstieg (+0.5/Monat): Prognose folgt Trend")
        print(f"  Scores:  {[e['score'] for e in result]}")
        print(f"  Clamped: {clamped['clamped_high']}/{clamped['total']} auf 5.0")

    def test_monotonic_linear_decrease(self):
        """Test: Perfekt linearer Abstieg → Prognose folgt dem Trend."""
        data = _make_historical([4.5, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0])
        result = calculate_forecast(data, 6)
        assert result[0]["score"] <= 1.0, \
            f"Erster Prognosewert {result[0]['score']} sollte ≤ 1.0 sein bei linearem Abstieg"
        clamped = count_clamped(result)
        print(f"\n✓ Linearer Abstieg (−0.5/Monat): Prognose folgt Trend")
        print(f"  Scores:  {[e['score'] for e in result]}")
        print(f"  Clamped: {clamped['clamped_low']}/{clamped['total']} auf 0.0")

    def test_sudden_spike(self):
        """Test: Plötzlicher Sprung → Prognose reagiert, bleibt im Bereich."""
        data = _make_historical([3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 5.0])
        result = calculate_forecast(data, 6)
        assert all(0.0 <= e["score"] <= 5.0 for e in result)
        print(f"\n✓ Plötzlicher Sprung (3.0 → 5.0): Prognose reagiert")
        print(f"  Scores:  {[e['score'] for e in result]}")

    def test_sudden_drop(self):
        """Test: Plötzlicher Absturz → Prognose reagiert, bleibt im Bereich."""
        data = _make_historical([3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 1.0])
        result = calculate_forecast(data, 6)
        assert all(0.0 <= e["score"] <= 5.0 for e in result)
        print(f"\n✓ Plötzlicher Absturz (3.5 → 1.0): Prognose reagiert")
        print(f"  Scores:  {[e['score'] for e in result]}")

    def test_constant_maximum(self):
        """Test: Konstant bei 5.0 → Prognose ≈ 5.0."""
        data = _make_historical([5.0] * 12)
        result = calculate_forecast(data, 6)
        for e in result:
            assert abs(e["score"] - 5.0) < 0.5, f"Score {e['score']} weicht zu stark von 5.0 ab"
        print(f"\n✓ Konstant 5.0: Prognose stabil — {[e['score'] for e in result]}")

    def test_constant_minimum(self):
        """Test: Konstant bei 1.0 → Prognose ≈ 1.0."""
        data = _make_historical([1.0] * 12)
        result = calculate_forecast(data, 6)
        for e in result:
            assert abs(e["score"] - 1.0) < 0.5, f"Score {e['score']} weicht zu stark von 1.0 ab"
        print(f"\n✓ Konstant 1.0: Prognose stabil — {[e['score'] for e in result]}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Clamping-Analyse: Wie oft greift [0, 5]?
# ═══════════════════════════════════════════════════════════════════════════════

class TestClampingAnalysis:
    """Systematische Analyse: In welchen Szenarien greift das Clamping?"""

    def test_clamping_frequency_overview(self):
        """Test: Übersicht über Clamping-Häufigkeit in verschiedenen Szenarien."""
        scenarios = [
            ("Stabil (3.5)", [3.5] * 12),
            ("Leicht steigend", [3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0, 4.1]),
            ("Leicht fallend", [4.0, 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1, 3.0, 2.9]),
            ("Stark steigend", [3.0, 3.5, 4.0, 4.3, 4.5, 4.7, 4.8, 4.85, 4.9, 4.95, 4.98, 5.0]),
            ("Stark fallend", [2.0, 1.8, 1.5, 1.2, 0.9, 0.7, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05]),
            ("Nahe Obergrenze", [4.5, 4.6, 4.7, 4.8, 4.9, 4.95, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]),
            ("Nahe Untergrenze", [0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1, 0.1, 0.1, 0.05, 0.05, 0.05]),
            ("V-förmig (Erholung)", [4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]),
            ("Sprung hoch", [3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 5.0]),
            ("Sprung runter", [3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 3.5, 1.0]),
        ]

        total_forecasts = 0
        total_clamped = 0

        print(f"\n{'Szenario':<25s} | {'Prognosen':>10s} | {'Clamped ↓':>10s} | {'Clamped ↑':>10s} | {'Gesamt':>8s} | {'Anteil':>8s}")
        print(f"{'─' * 85}")

        for name, scores in scenarios:
            data = _make_historical(scores)
            result = calculate_forecast(data, 12)
            cl = count_clamped(result)

            total_forecasts += cl["total"]
            total_clamped += cl["clamped_total"]

            print(f"{name:<25s} | {cl['total']:>10d} | {cl['clamped_low']:>10d} | {cl['clamped_high']:>10d} | {cl['clamped_total']:>8d} | {cl['clamped_pct']:>7.1f}%")

        overall_pct = round(total_clamped / total_forecasts * 100, 1) if total_forecasts else 0
        print(f"{'─' * 85}")
        print(f"{'GESAMT':<25s} | {total_forecasts:>10d} | {'':>10s} | {'':>10s} | {total_clamped:>8d} | {overall_pct:>7.1f}%")

        # Das Clamping sollte nur bei extremen Szenarien greifen
        assert total_clamped < total_forecasts, "Nicht alle Prognosen dürfen geclampt sein"
        print(f"\n✓ Clamping greift in {total_clamped}/{total_forecasts} Fällen ({overall_pct}%)")

    def test_normal_scenarios_no_clamping(self):
        """Test: Bei normalen Bewertungsverläufen greift kein Clamping."""
        normal_scenarios = [
            [3.0, 3.1, 3.2, 3.15, 3.3, 3.25, 3.4, 3.35, 3.5, 3.45, 3.6, 3.55],
            [3.80, 3.75, 3.82, 3.78, 3.85, 3.80, 3.77, 3.83, 3.79, 3.84, 3.81, 3.82],
            [4.20, 4.10, 4.05, 3.95, 3.90, 3.85, 3.75, 3.70, 3.60, 3.55, 3.50, 3.45],
        ]

        for i, scores in enumerate(normal_scenarios):
            data = _make_historical(scores)
            result = calculate_forecast(data, 6)
            cl = count_clamped(result)
            assert cl["clamped_total"] == 0, \
                f"Szenario {i+1}: Clamping bei normalen Daten unerwartet ({cl['clamped_total']} Werte)"

        print(f"\n✓ Kein Clamping bei 3 normalen Bewertungsverläufen (wie erwartet)")

    def test_clamping_preserves_structure(self):
        """Test: Geclampt Werte behalten die korrekte Datenstruktur."""
        # Extrem steigend — wird geclampt
        data = _make_historical([3.0, 3.5, 4.0, 4.3, 4.5, 4.7, 4.8, 4.85, 4.9, 4.95, 4.98, 5.0])
        result = calculate_forecast(data, 12)
        clamped_entries = [e for e in result if e["score"] == 5.0]

        for entry in clamped_entries:
            assert "date" in entry
            assert "date_display" in entry
            assert "is_forecast" in entry
            assert entry["is_forecast"] is True
            assert entry["score"] == 5.0

        print(f"\n✓ Geclampt Einträge behalten vollständige Struktur ({len(clamped_entries)} Einträge)")


# ═══════════════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════════════

def run_all_tests():
    """Führt die Edge-Case-Analyse aus."""
    print("=" * 85)
    print("PROGNOSE-ENGINE — EDGE-CASE-ANALYSE")
    print("=" * 85)

    sections = [
        ("Unzureichende Datenpunkte", TestInsufficientData, [
            "test_empty_list", "test_single_point", "test_zero_months_requested",
            "test_negative_months_requested", "test_exactly_two_points"
        ]),
        ("Extreme Trends", TestExtremeTrends, [
            "test_strongly_rising_to_max", "test_strongly_falling_to_min",
            "test_monotonic_linear_increase", "test_monotonic_linear_decrease",
            "test_sudden_spike", "test_sudden_drop",
            "test_constant_maximum", "test_constant_minimum"
        ]),
        ("Clamping-Analyse [0, 5]", TestClampingAnalysis, [
            "test_clamping_frequency_overview", "test_normal_scenarios_no_clamping",
            "test_clamping_preserves_structure"
        ]),
    ]

    total_passed = 0
    total_failed = 0

    for section_name, cls, methods in sections:
        print(f"\n{'─' * 85}")
        print(f"  {section_name}")
        print(f"{'─' * 85}")

        instance = cls()
        for method in methods:
            try:
                getattr(instance, method)()
                print(f"  → PASSED ✓")
                total_passed += 1
            except Exception as e:
                print(f"  → FAILED ✗: {e}")
                total_failed += 1

    print(f"\n{'=' * 85}")
    print(f"ERGEBNIS: {total_passed} bestanden, {total_failed} fehlgeschlagen")
    print(f"{'=' * 85}")


if __name__ == "__main__":
    run_all_tests()
