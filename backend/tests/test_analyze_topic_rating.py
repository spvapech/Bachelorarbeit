"""
Unit tests for analyze_topic() — verifies that topic avg-ratings are not
distorted by double-counting the overall durchschnittsbewertung.

Bug that was fixed: both `durchschnittsbewertung` (overall avg) AND the
topic-specific rating field were appended to the same `ratings` list,
biasing the topic score toward the overall company mean.

Expected behaviour after fix:
- When a topic-specific rating field is present, use ONLY that field.
- When no topic-specific rating is present, fall back to durchschnittsbewertung.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from routes.analytics import analyze_topic


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_employee_review(
    *,
    durchschnittsbewertung: float,
    topic_rating: float | None = None,
    topic_field: str = "sternebewertung_work_life_balance",
    text: str = "work-life-balance ist gut",
) -> dict:
    r = {
        "id": 1,
        "datum": "2024-01-15",
        "durchschnittsbewertung": durchschnittsbewertung,
        "titel": "Testbewertung",
        "gut_am_arbeitgeber_finde_ich": text,
        "schlecht_am_arbeitgeber_finde_ich": "",
        "verbesserungsvorschlaege": "",
        "jobbeschreibung": "",
    }
    if topic_rating is not None:
        r[topic_field] = topic_rating
    return r


# ---------------------------------------------------------------------------
# Tests: no double-counting
# ---------------------------------------------------------------------------

class TestAnalyzeTopicNoDoubleCounting:
    """avgRating must reflect the topic-specific field, not a blend."""

    KEYWORDS = [r"\bwork[\s-]*life[\s-]*balance\b", r"\barbeitszeit\b"]
    RATING_FIELDS = ["sternebewertung_work_life_balance"]

    def _run(self, reviews: list[dict]) -> float:
        result = analyze_topic(
            topic_name="Work-Life Balance",
            keywords=self.KEYWORDS,
            rating_fields=self.RATING_FIELDS,
            all_reviews=reviews,
        )
        return result["avgRating"]

    def test_topic_specific_rating_used_when_available(self):
        """If a topic-specific rating exists, it must be the sole source."""
        # durchschnittsbewertung=5.0, topic=1.0 → correct avg must be 1.0
        review = _make_employee_review(durchschnittsbewertung=5.0, topic_rating=1.0)
        avg = self._run([review])
        assert avg == pytest.approx(1.0, abs=0.05), (
            f"Expected topic avg ≈ 1.0 (topic-specific only), got {avg}. "
            "Likely double-counting with durchschnittsbewertung=5.0."
        )

    def test_no_blending_with_overall_average(self):
        """avgRating must NOT be a blend of overall + topic-specific."""
        # If blending occurred: (5.0 + 1.0) / 2 = 3.0
        review = _make_employee_review(durchschnittsbewertung=5.0, topic_rating=1.0)
        avg = self._run([review])
        assert avg != pytest.approx(3.0, abs=0.1), (
            "avgRating equals the blended value (5.0+1.0)/2=3.0 — "
            "double-counting bug is NOT fixed."
        )

    def test_fallback_to_overall_when_no_topic_field(self):
        """When no topic-specific rating exists, durchschnittsbewertung is the fallback."""
        review = _make_employee_review(durchschnittsbewertung=3.5, topic_rating=None)
        avg = self._run([review])
        assert avg == pytest.approx(3.5, abs=0.05), (
            f"Expected fallback to durchschnittsbewertung=3.5, got {avg}."
        )

    def test_multiple_reviews_topic_specific_only(self):
        """Average across multiple reviews uses only topic-specific fields."""
        reviews = [
            _make_employee_review(durchschnittsbewertung=5.0, topic_rating=2.0,
                                  text="work-life-balance schlecht"),
            _make_employee_review(durchschnittsbewertung=5.0, topic_rating=4.0,
                                  text="work-life-balance okay"),
        ]
        avg = self._run(reviews)
        expected = (2.0 + 4.0) / 2  # = 3.0
        assert avg == pytest.approx(expected, abs=0.1), (
            f"Expected topic avg ≈ {expected}, got {avg}."
        )

    def test_sentiment_positive_when_topic_rating_high(self):
        """Sentiment must be 'Positiv' when topic-specific rating is high (≥ 3.5)."""
        review = _make_employee_review(durchschnittsbewertung=1.0, topic_rating=4.5)
        result = analyze_topic(
            topic_name="Work-Life Balance",
            keywords=self.KEYWORDS,
            rating_fields=self.RATING_FIELDS,
            all_reviews=[review],
        )
        assert result["sentiment"] == "Positiv", (
            f"Expected 'Positiv' for topic rating 4.5, got '{result['sentiment']}'. "
            "Sentiment likely distorted by double-counting with low overall rating."
        )

    def test_sentiment_negativ_when_topic_rating_low(self):
        """Sentiment must be 'Negativ' when topic-specific rating is low (< 2.5)."""
        review = _make_employee_review(durchschnittsbewertung=5.0, topic_rating=1.0)
        result = analyze_topic(
            topic_name="Work-Life Balance",
            keywords=self.KEYWORDS,
            rating_fields=self.RATING_FIELDS,
            all_reviews=[review],
        )
        assert result["sentiment"] == "Negativ", (
            f"Expected 'Negativ' for topic rating 1.0, got '{result['sentiment']}'. "
            "Sentiment likely distorted by double-counting with high overall rating."
        )

    def test_zero_frequency_when_no_keyword_match(self):
        """Topics not mentioned in any review must have frequency=0."""
        review = _make_employee_review(
            durchschnittsbewertung=3.0,
            topic_rating=3.0,
            text="Gehalt ist gut",  # no WLB keyword
        )
        result = analyze_topic(
            topic_name="Work-Life Balance",
            keywords=self.KEYWORDS,
            rating_fields=self.RATING_FIELDS,
            all_reviews=[review],
        )
        assert result["frequency"] == 0

    def test_frequency_counts_only_keyword_matches(self):
        """frequency reflects the number of reviews that mention the topic."""
        reviews = [
            _make_employee_review(durchschnittsbewertung=3.0, text="work-life-balance okay"),
            _make_employee_review(durchschnittsbewertung=3.0, text="Gehalt ist gut"),
            _make_employee_review(durchschnittsbewertung=3.0, text="arbeitszeit ist lang"),
        ]
        result = analyze_topic(
            topic_name="Work-Life Balance",
            keywords=self.KEYWORDS,
            rating_fields=self.RATING_FIELDS,
            all_reviews=reviews,
        )
        assert result["frequency"] == 2  # only reviews 0 and 2 match
