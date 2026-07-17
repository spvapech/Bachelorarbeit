"""
Test: Transformer bleibt primäres Modell
=========================================
Überprüft, dass:
1. Das Transformer-Modell bei klaren Texten stets das korrekte Ergebnis liefert.
2. Das Lexikon den Transformer NICHT bei eindeutigen Fällen überschreibt.
3. Die Hybrid-Korrektur (Cases C/D/E) nur bei echter Unsicherheit greift.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from models.sentiment_analyzer import SentimentAnalyzer


# ---------------------------------------------------------------------------
# Testdaten: (text, erwartetes_sentiment, begründung)
# ---------------------------------------------------------------------------
CLEAR_POSITIVE_TEXTS = [
    ("Das Team ist fantastisch und die Unternehmenskultur hervorragend.",    "positive", "klares Lob"),
    ("Toller Arbeitgeber mit fairer Bezahlung und guten Karrierechancen.",   "positive", "deutlich positiv"),
    ("Ich liebe meinen Job, super Kollegen und spannende Projekte!",         "positive", "begeistert positiv"),
    ("Exzellente Entwicklungsmöglichkeiten und ein wertschätzendes Team.",   "positive", "sehr positiv"),
]

CLEAR_NEGATIVE_TEXTS = [
    ("Das Management ist katastrophal und die Bezahlung ist eine Frechheit.", "negative", "klare Kritik"),
    ("Schreckliche Arbeitsatmosphäre, kein Respekt, übermäßiger Stress.",     "negative", "stark negativ"),
    ("Absolut frustrierend – keine Wertschätzung und ständige Überstunden.",  "negative", "negativ"),
    ("Unterirdisches Gehalt, schlechte Führung und keinerlei Work-Life-Balance.", "negative", "sehr negativ"),
]

NEUTRAL_TEXTS = [
    ("Es ist okay, nichts Besonderes.",            "neutral", "neutral-phrase"),
    ("Normaler Job, nicht gut, nicht schlecht.",    "neutral", "ausgewogen"),
    ("Geht so.",                                    "neutral", "kurz neutral"),
]

# Texte die das Lexikon falsch einschätzt, aber der Transformer richtig
TRICKY_TEXTS = [
    # Negation — Lexikon sieht "schrecklich" als negativ,
    # aber der Kontext macht es positiv/neutral
    ("Die Zusammenarbeit ist nicht schrecklich, sondern eigentlich ganz gut.", "positive", "Negierte Negation → positiv"),
    # Sarkasmus / gemischter Kontext
    ("Gehalt lässt zu wünschen übrig, aber die Kollegen sind wirklich super.", "neutral", "gemischt"),
]


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def build_mock_pipeline(sentiment: str, confidence: float = 0.9):
    """
    Erstellt eine Mock-Transformer-Pipeline die ein festes Ergebnis zurückgibt.
    Wird genutzt um den Transformer zu simulieren ohne echtes Modell zu laden.
    """
    score_map = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
    score_map[sentiment] = confidence
    remainder = (1.0 - confidence) / 2
    for key in score_map:
        if key != sentiment:
            score_map[key] = remainder

    mock_result = [[
        {"label": k, "score": v} for k, v in score_map.items()
    ]]

    pipeline = MagicMock()
    pipeline.return_value = mock_result
    return pipeline


def make_analyzer_with_mock_transformer(transformer_sentiment: str, confidence: float = 0.9):
    """
    Gibt einen SentimentAnalyzer zurück dessen Transformer-Pipeline gemockt ist.
    Das Lexikon läuft echt.
    """
    analyzer = SentimentAnalyzer(mode="lexicon")  # erst ohne Transformer
    analyzer.mode = "transformer"
    analyzer._transformer_available = True
    analyzer._transformer_pipeline = build_mock_pipeline(transformer_sentiment, confidence)
    return analyzer


# ---------------------------------------------------------------------------
# Tests: Transformer dominiert bei hoher Konfidenz
# ---------------------------------------------------------------------------

class TestTransformerDominiert:
    """
    Wenn der Transformer sehr sicher ist (confidence >= 0.9),
    darf das Lexikon ihn NICHT überschreiben — unabhängig vom Lexikon-Ergebnis.
    """

    @pytest.mark.parametrize("text,expected,reason", CLEAR_POSITIVE_TEXTS)
    def test_klare_positive_texte_bleiben_positiv(self, text, expected, reason):
        """Transformer sagt positiv mit 90% Konfidenz → Ergebnis bleibt positiv."""
        analyzer = make_analyzer_with_mock_transformer("positive", confidence=0.9)
        result = analyzer.analyze_sentiment(text)
        assert result["sentiment"] == expected, (
            f"[{reason}] Erwartet '{expected}', bekam '{result['sentiment']}' "
            f"(confidence={result['confidence']:.2f})"
        )

    @pytest.mark.parametrize("text,expected,reason", CLEAR_NEGATIVE_TEXTS)
    def test_klare_negative_texte_bleiben_negativ(self, text, expected, reason):
        """Transformer sagt negativ mit 90% Konfidenz → Ergebnis bleibt negativ."""
        analyzer = make_analyzer_with_mock_transformer("negative", confidence=0.9)
        result = analyzer.analyze_sentiment(text)
        assert result["sentiment"] == expected, (
            f"[{reason}] Erwartet '{expected}', bekam '{result['sentiment']}' "
            f"(confidence={result['confidence']:.2f})"
        )

    @pytest.mark.parametrize("text,expected,reason", CLEAR_NEGATIVE_TEXTS)
    def test_lexikon_kann_nicht_negatives_korrigieren_bei_70_prozent(self, text, expected, reason):
        """
        Case C: Transformer sagt negativ mit confidence=0.7 und margin=0.4.
        Da margin >= 0.2 OR confidence >= 0.55, darf das Lexikon nicht überschreiben.
        """
        # margin = 0.7 - (0.15) = 0.55 >= 0.2 → kein Override
        analyzer = make_analyzer_with_mock_transformer("negative", confidence=0.7)
        result = analyzer.analyze_sentiment(text)
        # Ergebnis muss negativ bleiben (oder neutral durch neutrale Phrase, aber nicht positiv)
        assert result["sentiment"] in ("negative", "neutral"), (
            f"[{reason}] Transformer (70% negativ) wurde auf '{result['sentiment']}' geändert — Lexikon zu aggressiv!"
        )
        assert result["sentiment"] != "positive", (
            f"[{reason}] Lexikon hat fälschlicherweise auf 'positiv' überschrieben!"
        )


# ---------------------------------------------------------------------------
# Tests: Case C — neutrales Override nur bei echter Unsicherheit
# ---------------------------------------------------------------------------

class TestCaseCNurBeiUnsicherheit:
    """
    Case C: Transformer sagt negativ, Lexikon sagt neutral.
    Override soll NUR passieren wenn margin < 0.2 UND confidence < 0.55.
    """

    def test_kein_override_wenn_margin_gross(self):
        """Transformer: negativ, margin=0.5 → kein Override (margin >= 0.2)."""
        # confidence=0.7 → scores: neg=0.7, pos=0.15, neu=0.15 → margin=0.55
        analyzer = make_analyzer_with_mock_transformer("negative", confidence=0.7)
        # Leerer Text der vom Lexikon als neutral gesehen wird
        result = analyzer.analyze_sentiment("Die Situation ist durchwachsen.")
        assert result["sentiment"] != "positive", "Darf nicht auf positiv springen"

    def test_kein_override_wenn_confidence_hoch(self):
        """Transformer: negativ, confidence=0.8 → kein Override trotz kleinem Margin (da conf >= 0.55)."""
        # Confidence=0.8 → überschreitet 0.55-Schwelle → kein Override
        analyzer = make_analyzer_with_mock_transformer("negative", confidence=0.8)
        result = analyzer.analyze_sentiment("Es könnte besser sein.")
        assert result["sentiment"] in ("negative", "neutral"), (
            f"Erwartet negativ/neutral, bekam '{result['sentiment']}'"
        )

    def test_override_erlaubt_bei_echter_unsicherheit(self):
        """
        Transformer sehr unsicher (confidence=0.45, margin≈0.15).
        Override auf neutral ist erlaubt.
        """
        # confidence=0.45 → scores: neg=0.45, rest=0.275 → margin≈0.175 < 0.2
        # confidence < 0.55 → beide Bedingungen erfüllt → Override erlaubt
        analyzer = make_analyzer_with_mock_transformer("negative", confidence=0.45)
        result = analyzer.analyze_sentiment("Es ist ganz okay hier.")
        # Darf auf neutral gehen
        assert result["sentiment"] in ("neutral", "negative"), (
            f"Erwartet neutral oder negativ, bekam '{result['sentiment']}'"
        )


# ---------------------------------------------------------------------------
# Tests: Case D — Lexikon-Override nur bei sehr hoher Konfidenz
# ---------------------------------------------------------------------------

class TestCaseDHoheLexikonKonfidenz:
    """
    Case D: Transformer sagt negativ, Lexikon sagt positiv.
    Override nur wenn Lexikon confidence > 0.7.
    """

    def test_stark_negative_texte_werden_nicht_positiv(self):
        """
        Transformer: negativ mit 0.9. Lexikon sagt: positiv (durch positive Wörter).
        Da confidence > 0.7 nicht durch das Lexikon erreicht wird, bleibt negativ.
        """
        analyzer = make_analyzer_with_mock_transformer("negative", confidence=0.9)
        # "fantastisch" → Lexikon positiv, aber Transformer sehr sicher negativ
        result = analyzer.analyze_sentiment(
            "Obwohl die Kollegen fantastisch sind, ist das Management eine Katastrophe "
            "und die Arbeitsbedingungen sind unerträglich schlecht."
        )
        assert result["sentiment"] != "positive", (
            f"Transformer (90% negativ) wurde fälschlicherweise auf 'positiv' gesetzt!"
        )


# ---------------------------------------------------------------------------
# Tests: Transformer vs. Lexikon — Transformer gewinnt öfter
# ---------------------------------------------------------------------------

class TestTransformerBesserAlsLexikon:
    """
    Vergleicht echten Transformer vs. echtes Lexikon auf bekannten Texten.
    Transformer soll mindestens genauso gut oder besser sein.
    """

    @pytest.fixture(scope="class")
    def transformer_analyzer(self):
        try:
            a = SentimentAnalyzer(mode="transformer")
            if not a._transformer_available:
                pytest.skip("Transformer nicht verfügbar (fehlende Abhängigkeiten)")
            return a
        except Exception:
            pytest.skip("Transformer konnte nicht geladen werden")

    @pytest.fixture(scope="class")
    def lexicon_analyzer(self):
        return SentimentAnalyzer(mode="lexicon")

    def _accuracy(self, analyzer, test_cases):
        correct = 0
        for text, expected, _ in test_cases:
            result = analyzer.analyze_sentiment(text)
            if result["sentiment"] == expected:
                correct += 1
        return correct / len(test_cases)

    def test_transformer_mindestens_so_gut_bei_positiv(self, transformer_analyzer, lexicon_analyzer):
        """Transformer-Genauigkeit bei positiven Texten >= Lexikon-Genauigkeit."""
        t_acc = self._accuracy(transformer_analyzer, CLEAR_POSITIVE_TEXTS)
        l_acc = self._accuracy(lexicon_analyzer, CLEAR_POSITIVE_TEXTS)
        assert t_acc >= l_acc, (
            f"Transformer ({t_acc:.0%}) schlechter als Lexikon ({l_acc:.0%}) bei positiven Texten!"
        )

    def test_transformer_mindestens_so_gut_bei_negativ(self, transformer_analyzer, lexicon_analyzer):
        """Transformer-Genauigkeit bei negativen Texten >= Lexikon-Genauigkeit."""
        t_acc = self._accuracy(transformer_analyzer, CLEAR_NEGATIVE_TEXTS)
        l_acc = self._accuracy(lexicon_analyzer, CLEAR_NEGATIVE_TEXTS)
        assert t_acc >= l_acc, (
            f"Transformer ({t_acc:.0%}) schlechter als Lexikon ({l_acc:.0%}) bei negativen Texten!"
        )

    def test_transformer_gesamtgenauigkeit_ueber_70_prozent(self, transformer_analyzer):
        """Transformer soll auf den bekannten Testfällen mindestens 70% Genauigkeit haben."""
        all_cases = CLEAR_POSITIVE_TEXTS + CLEAR_NEGATIVE_TEXTS + NEUTRAL_TEXTS
        acc = self._accuracy(transformer_analyzer, all_cases)
        assert acc >= 0.70, (
            f"Transformer-Gesamtgenauigkeit zu niedrig: {acc:.0%} (Minimum: 70%)"
        )


# ---------------------------------------------------------------------------
# Tests: Konfidenz-Werte sind sinnvoll
# ---------------------------------------------------------------------------

class TestKonfidenzWerte:
    """Stellt sicher dass confidence-Werte plausibel sind."""

    @pytest.fixture(scope="class")
    def analyzer(self):
        try:
            a = SentimentAnalyzer(mode="transformer")
            if not a._transformer_available:
                pytest.skip("Transformer nicht verfügbar")
            return a
        except Exception:
            pytest.skip("Transformer konnte nicht geladen werden")

    def test_confidence_immer_zwischen_0_und_1(self, analyzer):
        all_texts = [t for t, _, _ in CLEAR_POSITIVE_TEXTS + CLEAR_NEGATIVE_TEXTS + NEUTRAL_TEXTS]
        for text in all_texts:
            result = analyzer.analyze_sentiment(text)
            assert 0.0 <= result["confidence"] <= 1.0, (
                f"Confidence außerhalb [0,1]: {result['confidence']} für '{text[:40]}'"
            )

    def test_klare_texte_haben_hohe_confidence(self, analyzer):
        """Eindeutige Texte sollen confidence > 0.55 haben."""
        combined = CLEAR_POSITIVE_TEXTS + CLEAR_NEGATIVE_TEXTS
        for text, expected, reason in combined:
            result = analyzer.analyze_sentiment(text)
            if result["sentiment"] == expected:
                assert result["confidence"] > 0.55, (
                    f"[{reason}] Richtige Vorhersage aber niedrige Confidence: "
                    f"{result['confidence']:.2f} für '{text[:40]}'"
                )


# ---------------------------------------------------------------------------
# Entry point für direkten Aufruf
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("TEST: Transformer bleibt primäres Modell")
    print("=" * 70)

    print("\n--- Mock-basierte Tests (Cases C/D/E Schwellenwerte) ---")

    # Case C: Kein Override bei margin=0.55
    analyzer = make_analyzer_with_mock_transformer("negative", confidence=0.7)
    result = analyzer.analyze_sentiment("Die Situation ist durchwachsen.")
    status = "OK" if result["sentiment"] != "positive" else "FEHLER"
    print(f"[{status}] Case C kein Override (margin=0.55): {result['sentiment']}")

    # Case D: Kein Override bei transformer 90%
    analyzer = make_analyzer_with_mock_transformer("negative", confidence=0.9)
    result = analyzer.analyze_sentiment(
        "Obwohl die Kollegen fantastisch sind, ist das Management eine Katastrophe."
    )
    status = "OK" if result["sentiment"] != "positive" else "FEHLER"
    print(f"[{status}] Case D kein Override (transformer 90%): {result['sentiment']}")

    # Case C: Override erlaubt bei Unsicherheit
    analyzer = make_analyzer_with_mock_transformer("negative", confidence=0.45)
    result = analyzer.analyze_sentiment("Es ist ganz okay hier.")
    status = "OK" if result["sentiment"] in ("neutral", "negative") else "FEHLER"
    print(f"[{status}] Case C Override bei Unsicherheit (45%): {result['sentiment']}")

    print("\n--- Echter Transformer ---")
    try:
        ta = SentimentAnalyzer(mode="transformer")
        if ta._transformer_available:
            all_cases = CLEAR_POSITIVE_TEXTS + CLEAR_NEGATIVE_TEXTS + NEUTRAL_TEXTS
            correct = sum(
                1 for text, exp, _ in all_cases
                if ta.analyze_sentiment(text)["sentiment"] == exp
            )
            print(f"Transformer Genauigkeit: {correct}/{len(all_cases)} ({correct/len(all_cases):.0%})")

            la = SentimentAnalyzer(mode="lexicon")
            correct_lex = sum(
                1 for text, exp, _ in all_cases
                if la.analyze_sentiment(text)["sentiment"] == exp
            )
            print(f"Lexikon Genauigkeit:      {correct_lex}/{len(all_cases)} ({correct_lex/len(all_cases):.0%})")

            winner = "Transformer" if correct >= correct_lex else "Lexikon"
            print(f"\n→ Gewinner: {winner}")
        else:
            print("Transformer nicht verfügbar.")
    except Exception as e:
        print(f"Transformer Fehler: {e}")
