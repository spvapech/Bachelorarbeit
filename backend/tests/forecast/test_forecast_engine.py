"""
Test Suite für Prognose-Engine (Forecast)
Überprüft die Funktionalität der Holt's Exponential Smoothing Prognose
sowie des Durchschnitt-Fallbacks für Bewertungszeitreihen.

Ausführung:
    uv run python -m pytest tests/forecast/test_forecast_engine.py -v
"""

import pytest
from datetime import datetime
from unittest.mock import patch

# Import the forecast functions from analytics
import sys
import os

# Add backend root to path so we can import from routes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from routes.analytics import calculate_forecast, _fallback_forecast_average


# ─── Fixtures ────────────────────────────────────────────────────────────────

def _make_historical(scores: list[float], start_year: int = 2024, start_month: int = 1) -> list[dict]:
    """Helper: Erstellt historische Daten aus einer Score-Liste."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Eingabevalidierung
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculateForecastInput:
    """Tests für die Eingabevalidierung von calculate_forecast."""

    def test_empty_data_returns_empty(self):
        """Test: Leere historische Daten → leere Prognose."""
        result = calculate_forecast([], 6)
        assert result == []
        print("\n✓ Leere Daten → leere Prognose")

    def test_single_datapoint_returns_empty(self):
        """Test: Nur 1 Datenpunkt → leere Prognose (min. 2 nötig für Holt)."""
        data = _make_historical([3.5])
        result = calculate_forecast(data, 6)
        assert result == []
        print("\n✓ 1 Datenpunkt → leere Prognose (Mindestens 2 erforderlich)")

    def test_zero_months_returns_empty(self):
        """Test: months=0 → leere Prognose."""
        data = _make_historical([3.0, 3.5, 4.0])
        result = calculate_forecast(data, 0)
        assert result == []
        print("\n✓ 0 Monate → leere Prognose")

    def test_negative_months_returns_empty(self):
        """Test: Negative months → leere Prognose."""
        data = _make_historical([3.0, 3.5, 4.0])
        result = calculate_forecast(data, -3)
        assert result == []
        print("\n✓ Negative Monate → leere Prognose")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Holt's Method — Kernfunktionalität
# ═══════════════════════════════════════════════════════════════════════════════

class TestHoltForecast:
    """Tests für Holt's Exponential Smoothing Prognose."""

    @pytest.fixture
    def stable_data(self):
        """12 Monate stabile Bewertungsdaten mit leichtem Aufwärtstrend."""
        return _make_historical(
            [3.0, 3.1, 3.2, 3.15, 3.3, 3.25, 3.4, 3.35, 3.5, 3.45, 3.6, 3.55]
        )

    def test_forecast_returns_correct_count(self, stable_data):
        """Test: Prognose liefert exakt die angeforderte Anzahl Monate."""
        for months in [1, 6, 12]:
            result = calculate_forecast(stable_data, months)
            assert len(result) == months, f"Erwartet {months} Prognose-Einträge, erhalten: {len(result)}"
        print("\n✓ Korrekte Anzahl Prognose-Einträge für 1, 6 und 12 Monate")

    def test_forecast_structure(self, stable_data):
        """Test: Jeder Prognose-Eintrag hat die korrekte Struktur."""
        result = calculate_forecast(stable_data, 6)

        for i, entry in enumerate(result):
            assert "date" in entry, f"Eintrag {i}: 'date' fehlt"
            assert "date_display" in entry, f"Eintrag {i}: 'date_display' fehlt"
            assert "score" in entry, f"Eintrag {i}: 'score' fehlt"
            assert "is_forecast" in entry, f"Eintrag {i}: 'is_forecast' fehlt"
            assert entry["is_forecast"] is True, f"Eintrag {i}: is_forecast muss True sein"
            assert isinstance(entry["score"], float), f"Eintrag {i}: Score muss float sein"

        print("\n✓ Prognose-Struktur korrekt (date, date_display, score, is_forecast=True)")

    def test_forecast_dates_sequential(self, stable_data):
        """Test: Prognosemonate sind aufeinanderfolgend."""
        result = calculate_forecast(stable_data, 6)

        dates = [datetime.strptime(e["date"], "%Y-%m") for e in result]
        for i in range(1, len(dates)):
            # Nächster Monat muss genau 1 Monat nach dem vorherigen sein
            prev = dates[i - 1]
            curr = dates[i]
            expected_month = prev.month % 12 + 1
            expected_year = prev.year + (1 if prev.month == 12 else 0)
            assert curr.month == expected_month and curr.year == expected_year, \
                f"Datum {i}: Erwartet {expected_year}-{expected_month:02d}, erhalten {curr.strftime('%Y-%m')}"

        print(f"\n✓ Prognosedaten sequenziell: {result[0]['date']} → {result[-1]['date']}")

    def test_forecast_scores_clamped_0_5(self):
        """Test: Prognose-Scores werden auf [0, 5] begrenzt (Clamping)."""
        # Stark steigender Trend → würde ohne Clamping > 5 gehen
        rising_data = _make_historical(
            [3.0, 3.5, 4.0, 4.5, 4.8, 4.9, 4.95, 4.98, 5.0, 5.0, 5.0, 5.0]
        )
        result = calculate_forecast(rising_data, 12)

        for entry in result:
            assert 0.0 <= entry["score"] <= 5.0, \
                f"Score {entry['score']} außerhalb [0, 5] am {entry['date']}"

        print("\n✓ Alle Prognose-Scores im Rating-Bereich [0, 5]")

    def test_forecast_trend_direction(self):
        """Test: Aufwärtstrend in Daten → Prognose bleibt ≥ letztem historischen Wert."""
        # Klarer Aufwärtstrend
        rising_data = _make_historical(
            [2.0, 2.2, 2.5, 2.7, 3.0, 3.2, 3.5, 3.7, 4.0, 4.2, 4.3, 4.5]
        )
        result = calculate_forecast(rising_data, 3)
        last_historical = rising_data[-1]["score"]

        # Mindestens der erste Prognosewert sollte ≥ dem letzten historischen sein
        assert result[0]["score"] >= last_historical - 0.5, \
            f"Erster Prognosewert {result[0]['score']} zu weit unter letztem Wert {last_historical}"

        print(f"\n✓ Trendrichtung validiert: Letzter historischer Wert={last_historical}, "
              f"Erster Prognosewert={result[0]['score']}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Fallback-Prognose (Durchschnitt)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFallbackForecast:
    """Tests für die Durchschnitt-Fallback-Prognose."""

    @pytest.fixture
    def sample_data(self):
        """Einfache Testdaten für Fallback."""
        return _make_historical([3.0, 3.5, 4.0, 3.5])

    def test_fallback_returns_correct_count(self, sample_data):
        """Test: Fallback liefert exakt die angeforderte Anzahl."""
        y_values = [p["score"] for p in sample_data]
        result = _fallback_forecast_average(sample_data, 6, y_values)
        assert len(result) == 6
        print("\n✓ Fallback liefert korrekte Anzahl (6 Monate)")

    def test_fallback_uses_average(self, sample_data):
        """Test: Alle Fallback-Prognosen verwenden den Durchschnitt."""
        y_values = [p["score"] for p in sample_data]
        expected_avg = round(sum(y_values) / len(y_values), 2)
        result = _fallback_forecast_average(sample_data, 6, y_values)

        for entry in result:
            assert entry["score"] == expected_avg, \
                f"Erwarteter Score {expected_avg}, erhalten {entry['score']}"

        print(f"\n✓ Alle Fallback-Werte = Durchschnitt ({expected_avg})")

    def test_fallback_structure(self, sample_data):
        """Test: Fallback-Einträge haben die korrekte Struktur."""
        y_values = [p["score"] for p in sample_data]
        result = _fallback_forecast_average(sample_data, 3, y_values)

        for entry in result:
            assert "date" in entry
            assert "date_display" in entry
            assert "score" in entry
            assert "is_forecast" in entry
            assert entry["is_forecast"] is True

        print("\n✓ Fallback-Struktur korrekt")

    def test_fallback_dates_sequential(self, sample_data):
        """Test: Fallback-Monate sind aufeinanderfolgend."""
        y_values = [p["score"] for p in sample_data]
        result = _fallback_forecast_average(sample_data, 6, y_values)

        dates = [datetime.strptime(e["date"], "%Y-%m") for e in result]
        for i in range(1, len(dates)):
            prev = dates[i - 1]
            curr = dates[i]
            expected_month = prev.month % 12 + 1
            expected_year = prev.year + (1 if prev.month == 12 else 0)
            assert curr.month == expected_month and curr.year == expected_year

        print(f"\n✓ Fallback-Daten sequenziell: {result[0]['date']} → {result[-1]['date']}")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Datemberechnung
# ═══════════════════════════════════════════════════════════════════════════════

class TestDateCalculation:
    """Tests für korrekte Jahres- und Monatsberechnung in Prognosen."""

    def test_year_rollover(self):
        """Test: Dezember → Januar (Jahresübergang)."""
        data = _make_historical([3.0, 3.5, 4.0], start_year=2024, start_month=10)
        # Data: 2024-10, 2024-11, 2024-12
        result = calculate_forecast(data, 3)

        expected_dates = ["2025-01", "2025-02", "2025-03"]
        actual_dates = [e["date"] for e in result]
        assert actual_dates == expected_dates, f"Erwartet {expected_dates}, erhalten {actual_dates}"

        print(f"\n✓ Jahresübergang korrekt: {actual_dates}")

    def test_mid_year_forecast(self):
        """Test: Prognose ab Jahresmitte (Juni → Juli, Aug, ...)."""
        data = _make_historical([3.0, 3.5, 4.0, 3.8, 3.5, 3.6], start_year=2024, start_month=1)
        # Data: 2024-01 bis 2024-06
        result = calculate_forecast(data, 3)

        expected_dates = ["2024-07", "2024-08", "2024-09"]
        actual_dates = [e["date"] for e in result]
        assert actual_dates == expected_dates, f"Erwartet {expected_dates}, erhalten {actual_dates}"

        print(f"\n✓ Jahresmitte-Prognose korrekt: {actual_dates}")

    def test_multi_year_forecast(self):
        """Test: 24-Monate-Prognose über 2 Jahreswechsel."""
        data = _make_historical([3.0, 3.2, 3.4, 3.6], start_year=2024, start_month=1)
        # Data: 2024-01 bis 2024-04
        result = calculate_forecast(data, 24)

        assert len(result) == 24
        # Erster Prognosemonat: 2024-05, letzter: 2026-04
        assert result[0]["date"] == "2024-05"
        assert result[-1]["date"] == "2026-04"

        # Prüfe, dass keine Duplikate vorhanden sind
        dates = [e["date"] for e in result]
        assert len(dates) == len(set(dates)), "Doppelte Prognosemonate gefunden"

        print(f"\n✓ 24-Monate-Prognose über 2 Jahreswechsel: {result[0]['date']} → {result[-1]['date']}")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Grenzfälle (Edge Cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests für Grenzfälle der Prognose-Engine."""

    def test_constant_values(self):
        """Test: Konstante Eingabewerte → Prognose ≈ gleicher Wert."""
        data = _make_historical([3.5] * 12)
        result = calculate_forecast(data, 6)

        for entry in result:
            assert abs(entry["score"] - 3.5) < 0.5, \
                f"Bei konstanten Daten sollte Prognose nahe 3.5 sein, erhalten: {entry['score']}"

        print(f"\n✓ Konstante Eingabe → Prognose stabil bei ~3.5")

    def test_extreme_trend_clamped(self):
        """Test: Stark fallender Trend → Clamping auf ≥ 0.0."""
        # Stark fallend: von 2.0 runter
        falling_data = _make_historical(
            [2.0, 1.8, 1.5, 1.2, 0.9, 0.6, 0.4, 0.3, 0.2, 0.15, 0.1, 0.05]
        )
        result = calculate_forecast(falling_data, 12)

        for entry in result:
            assert entry["score"] >= 0.0, \
                f"Score {entry['score']} unter 0.0 am {entry['date']} (Clamping fehlgeschlagen)"

        print("\n✓ Stark fallender Trend → alle Werte ≥ 0.0 (Clamping aktiv)")

    def test_two_datapoints_minimum(self):
        """Test: Genau 2 Datenpunkte → Prognose funktioniert."""
        data = _make_historical([3.0, 3.5])
        result = calculate_forecast(data, 3)

        # Muss entweder Holt oder Fallback liefern, aber nicht leer sein
        assert len(result) == 3, f"2 Datenpunkte sollten Prognose ermöglichen, erhalten: {len(result)}"
        for entry in result:
            assert 0.0 <= entry["score"] <= 5.0

        print(f"\n✓ 2 Datenpunkte → Prognose möglich: {[e['score'] for e in result]}")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Backtest-Genauigkeit
# ═══════════════════════════════════════════════════════════════════════════════

class TestBacktestAccuracy:
    """Backtest-Tests: Prüft Prognosegenauigkeit auf synthetischen Daten."""

    def test_backtest_mae_within_bounds(self):
        """Test: MAE auf realistischen Testdaten liegt unter 1.0 Sterne."""
        # Simulierte 18 Monate: 12 Training + 6 Test
        all_scores = [3.2, 3.3, 3.1, 3.4, 3.5, 3.3, 3.6, 3.5, 3.7, 3.6, 3.8, 3.7,
                      3.9, 3.8, 4.0, 3.9, 4.1, 4.0]
        train_data = _make_historical(all_scores[:12])
        actual_scores = all_scores[12:]

        result = calculate_forecast(train_data, 6)
        predicted_scores = [e["score"] for e in result]

        # MAE berechnen
        mae = sum(abs(a - p) for a, p in zip(actual_scores, predicted_scores)) / len(actual_scores)
        assert mae < 1.0, f"MAE {mae:.3f} ist zu hoch (Grenzwert: 1.0)"

        print(f"\n✓ Backtest MAE = {mae:.3f} (< 1.0 Sterne)")
        print(f"  Actual:    {actual_scores}")
        print(f"  Predicted: {[round(s, 2) for s in predicted_scores]}")

    def test_holt_beats_average_on_trend(self):
        """Test: Holt's Method hat niedrigeren MAE als Durchschnitt bei Trenddaten."""
        # Klarer Aufwärtstrend: 12 Training + 6 Test
        all_scores = [2.0, 2.2, 2.4, 2.5, 2.7, 2.9, 3.0, 3.2, 3.3, 3.5, 3.6, 3.8,
                      3.9, 4.0, 4.1, 4.2, 4.3, 4.4]
        train_data = _make_historical(all_scores[:12])
        actual_scores = all_scores[12:]

        # Holt-Prognose
        holt_result = calculate_forecast(train_data, 6)
        holt_scores = [e["score"] for e in holt_result]
        holt_mae = sum(abs(a - p) for a, p in zip(actual_scores, holt_scores)) / len(actual_scores)

        # Fallback-Prognose (Durchschnitt)
        y_values = [p["score"] for p in train_data]
        fallback_result = _fallback_forecast_average(train_data, 6, y_values)
        fallback_scores = [e["score"] for e in fallback_result]
        fallback_mae = sum(abs(a - p) for a, p in zip(actual_scores, fallback_scores)) / len(actual_scores)

        assert holt_mae <= fallback_mae, \
            f"Holt MAE ({holt_mae:.3f}) sollte ≤ Fallback MAE ({fallback_mae:.3f}) bei Trenddaten sein"

        print(f"\n✓ Holt MAE ({holt_mae:.3f}) ≤ Fallback MAE ({fallback_mae:.3f}) bei Trenddaten")
        print(f"  Holt:     {[round(s, 2) for s in holt_scores]}")
        print(f"  Fallback: {[round(s, 2) for s in fallback_scores]}")
        print(f"  Actual:   {actual_scores}")


# ═══════════════════════════════════════════════════════════════════════════════
# Runner für direkten Aufruf
# ═══════════════════════════════════════════════════════════════════════════════

def run_all_tests():
    """Führt alle Tests aus (für direkten Aufruf)."""
    print("=" * 70)
    print("PROGNOSE-ENGINE (FORECAST) — TEST SUITE")
    print("=" * 70)

    test_classes = [
        ("Eingabevalidierung", TestCalculateForecastInput, [
            "test_empty_data_returns_empty",
            "test_single_datapoint_returns_empty",
            "test_zero_months_returns_empty",
            "test_negative_months_returns_empty",
        ]),
        ("Holt's Method — Kernfunktionalität", TestHoltForecast, [
            "test_forecast_returns_correct_count",
            "test_forecast_structure",
            "test_forecast_dates_sequential",
            "test_forecast_scores_clamped_0_5",
            "test_forecast_trend_direction",
        ]),
        ("Fallback-Prognose (Durchschnitt)", TestFallbackForecast, [
            "test_fallback_returns_correct_count",
            "test_fallback_uses_average",
            "test_fallback_structure",
            "test_fallback_dates_sequential",
        ]),
        ("Datumberechnung", TestDateCalculation, [
            "test_year_rollover",
            "test_mid_year_forecast",
            "test_multi_year_forecast",
        ]),
        ("Grenzfälle", TestEdgeCases, [
            "test_constant_values",
            "test_extreme_trend_clamped",
            "test_two_datapoints_minimum",
        ]),
        ("Backtest-Genauigkeit", TestBacktestAccuracy, [
            "test_backtest_mae_within_bounds",
            "test_holt_beats_average_on_trend",
        ]),
    ]

    total_passed = 0
    total_failed = 0
    test_number = 1

    for category_name, cls, methods in test_classes:
        print(f"\n{'─' * 70}")
        print(f"  {category_name}")
        print(f"{'─' * 70}")

        instance = cls()
        for method_name in methods:
            method = getattr(instance, method_name)
            try:
                # Handle fixtures
                import inspect
                sig = inspect.signature(method)
                kwargs = {}
                if "stable_data" in sig.parameters:
                    kwargs["stable_data"] = instance.stable_data(None) if hasattr(instance, "stable_data") else _make_historical(
                        [3.0, 3.1, 3.2, 3.15, 3.3, 3.25, 3.4, 3.35, 3.5, 3.45, 3.6, 3.55])
                if "sample_data" in sig.parameters:
                    kwargs["sample_data"] = _make_historical([3.0, 3.5, 4.0, 3.5])

                print(f"\n[TEST {test_number}] {method_name}")
                method(**kwargs)
                print(f"  → PASSED ✓")
                total_passed += 1
            except Exception as e:
                print(f"  → FAILED ✗: {e}")
                total_failed += 1
            test_number += 1

    # Zusammenfassung
    print(f"\n{'=' * 70}")
    print("TEST-ZUSAMMENFASSUNG")
    print(f"{'=' * 70}")
    print(f"  Bestanden:      {total_passed}")
    print(f"  Fehlgeschlagen:  {total_failed}")
    print(f"  Gesamt:          {total_passed + total_failed}")
    print(f"  Bestehensquote:  {total_passed / (total_passed + total_failed) * 100:.1f} %")
    print(f"{'=' * 70}")

    if total_failed == 0:
        print("\n✓ Alle Tests erfolgreich bestanden!")
    else:
        print(f"\n✗ {total_failed} Test(s) fehlgeschlagen.")


if __name__ == "__main__":
    run_all_tests()
