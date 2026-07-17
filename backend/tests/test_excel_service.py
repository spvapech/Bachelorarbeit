"""
Unit tests for excel_service column resolution.

Covers:
- Name-based (explicit) sternebewertung column resolution
- Positional (generic) fallback for legacy column naming
- Shuffled column ordering
- Missing required columns
- Extra / unknown columns are silently ignored

Run:
    uv run python -m pytest tests/test_excel_service.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pytest

from services.excel_service import (
    extract_sternebewertungen_by_name,
    normalize_columns,
    validate_required_columns,
    CANDIDATES_REQUIRED,
    EMPLOYEE_REQUIRED,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_df(data: dict) -> pd.DataFrame:
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# extract_sternebewertungen_by_name – explicit naming
# ---------------------------------------------------------------------------

class TestExplicitNaming:
    """Columns already carry the topic name after normalization."""

    def test_explicit_column_converted_to_numeric(self):
        df = make_df({
            "titel": ["Review A"],
            "sternebewertung_arbeitsatmosphaere": ["4"],
        })
        result = extract_sternebewertungen_by_name(df)
        assert "sternebewertung_arbeitsatmosphaere" in result.columns
        import numpy as np
        assert pd.api.types.is_numeric_dtype(result["sternebewertung_arbeitsatmosphaere"])
        assert result["sternebewertung_arbeitsatmosphaere"].iloc[0] == 4

    def test_multiple_explicit_columns_all_converted(self):
        df = make_df({
            "titel": ["R"],
            "sternebewertung_image": ["3"],
            "sternebewertung_kommunikation": ["5"],
        })
        result = extract_sternebewertungen_by_name(df)
        assert result["sternebewertung_image"].iloc[0] == 3.0
        assert result["sternebewertung_kommunikation"].iloc[0] == 5.0

    def test_non_numeric_value_becomes_nan(self):
        df = make_df({
            "titel": ["R"],
            "sternebewertung_image": ["n/a"],
        })
        result = extract_sternebewertungen_by_name(df)
        assert pd.isna(result["sternebewertung_image"].iloc[0])


# ---------------------------------------------------------------------------
# extract_sternebewertungen_by_name – generic (positional) fallback
# ---------------------------------------------------------------------------

class TestGenericPositionalFallback:
    """Legacy Excel files with repeated generic 'sternebewertung' headers."""

    def _make_generic_df(self):
        # Simulates what pandas produces after reading a file with duplicate headers:
        # "Sternebewertung | Arbeitsatmosphäre | Sternebewertung.1 | Image"
        return make_df({
            "titel": ["R"],
            "sternebewertung": [4],
            "arbeitsatmosphaere": ["gut"],
            "sternebewertung_1": [3],
            "image": ["mittel"],
        })

    def test_generic_creates_named_columns(self):
        df = self._make_generic_df()
        result = extract_sternebewertungen_by_name(df)
        assert "sternebewertung_arbeitsatmosphaere" in result.columns
        assert "sternebewertung_image" in result.columns

    def test_generic_columns_are_dropped(self):
        df = self._make_generic_df()
        result = extract_sternebewertungen_by_name(df)
        assert "sternebewertung" not in result.columns
        assert "sternebewertung_1" not in result.columns

    def test_generic_values_numeric(self):
        df = self._make_generic_df()
        result = extract_sternebewertungen_by_name(df)
        assert result["sternebewertung_arbeitsatmosphaere"].iloc[0] == 4.0
        assert result["sternebewertung_image"].iloc[0] == 3.0


# ---------------------------------------------------------------------------
# Shuffled column ordering
# ---------------------------------------------------------------------------

class TestShuffledColumns:
    """Explicit naming must survive any column reordering."""

    def _canonical_df(self):
        return make_df({
            "titel": ["R"],
            "datum": ["2024-01-01"],
            "sternebewertung_arbeitsatmosphaere": [5],
            "sternebewertung_image": [4],
            "sternebewertung_kommunikation": [3],
            "stellenbeschreibung": ["Backend Dev"],
        })

    def test_permutation_1_original_order(self):
        df = self._canonical_df()
        result = extract_sternebewertungen_by_name(df)
        assert result["sternebewertung_arbeitsatmosphaere"].iloc[0] == 5.0
        assert result["sternebewertung_image"].iloc[0] == 4.0
        assert result["sternebewertung_kommunikation"].iloc[0] == 3.0

    def test_permutation_2_ratings_first(self):
        df = self._canonical_df()[
            [
                "sternebewertung_image",
                "sternebewertung_arbeitsatmosphaere",
                "sternebewertung_kommunikation",
                "titel",
                "datum",
                "stellenbeschreibung",
            ]
        ]
        result = extract_sternebewertungen_by_name(df)
        assert result["sternebewertung_arbeitsatmosphaere"].iloc[0] == 5.0
        assert result["sternebewertung_image"].iloc[0] == 4.0
        assert result["sternebewertung_kommunikation"].iloc[0] == 3.0

    def test_permutation_3_interleaved(self):
        df = self._canonical_df()[
            [
                "datum",
                "sternebewertung_kommunikation",
                "titel",
                "sternebewertung_image",
                "stellenbeschreibung",
                "sternebewertung_arbeitsatmosphaere",
            ]
        ]
        result = extract_sternebewertungen_by_name(df)
        assert result["sternebewertung_arbeitsatmosphaere"].iloc[0] == 5.0
        assert result["sternebewertung_image"].iloc[0] == 4.0
        assert result["sternebewertung_kommunikation"].iloc[0] == 3.0


# ---------------------------------------------------------------------------
# Extra / unknown columns
# ---------------------------------------------------------------------------

class TestExtraColumns:
    def test_extra_columns_do_not_raise(self):
        df = make_df({
            "titel": ["R"],
            "stellenbeschreibung": ["Desc"],
            "unknown_column_xyz": ["ignored"],
            "another_extra": [42],
            "sternebewertung_image": [3],
        })
        result = extract_sternebewertungen_by_name(df)
        # Processing must succeed; unknown columns are left in place (whitelist filters later)
        assert "sternebewertung_image" in result.columns
        assert "unknown_column_xyz" in result.columns

    def test_extra_columns_do_not_corrupt_ratings(self):
        df = make_df({
            "titel": ["R"],
            "sternebewertung_image": [5],
            "completely_unknown": ["foo"],
        })
        result = extract_sternebewertungen_by_name(df)
        assert result["sternebewertung_image"].iloc[0] == 5.0


# ---------------------------------------------------------------------------
# validate_required_columns
# ---------------------------------------------------------------------------

class TestValidateRequiredColumns:
    def test_all_present_returns_empty(self):
        df = make_df({"titel": ["R"], "stellenbeschreibung": ["S"]})
        assert validate_required_columns(df, CANDIDATES_REQUIRED) == []

    def test_missing_single_column(self):
        df = make_df({"titel": ["R"]})
        missing = validate_required_columns(df, CANDIDATES_REQUIRED)
        assert missing == ["stellenbeschreibung"]

    def test_missing_multiple_columns(self):
        df = make_df({"status": ["active"]})
        missing = validate_required_columns(df, CANDIDATES_REQUIRED)
        assert set(missing) == {"titel", "stellenbeschreibung"}

    def test_employee_required_only_titel(self):
        df = make_df({"titel": ["R"]})
        assert validate_required_columns(df, EMPLOYEE_REQUIRED) == []

    def test_employee_missing_titel(self):
        df = make_df({"status": ["active"]})
        assert validate_required_columns(df, EMPLOYEE_REQUIRED) == ["titel"]

    def test_extra_columns_do_not_affect_validation(self):
        df = make_df({"titel": ["R"], "stellenbeschreibung": ["S"], "extra": [1]})
        assert validate_required_columns(df, CANDIDATES_REQUIRED) == []


# ---------------------------------------------------------------------------
# normalize_columns + extract pipeline combined
# ---------------------------------------------------------------------------

class TestNormalizePlusPipeline:
    """End-to-end column name normalization feeding into the extractor."""

    def test_umlaut_in_column_name_normalized(self):
        df = make_df({
            "Titel": ["R"],
            "Sternebewertung Arbeitsatmosphäre": [4],
        })
        df = normalize_columns(df)
        result = extract_sternebewertungen_by_name(df)
        assert "sternebewertung_arbeitsatmosphaere" in result.columns
        assert result["sternebewertung_arbeitsatmosphaere"].iloc[0] == 4.0

    def test_shuffled_after_normalize(self):
        df = make_df({
            "Sternebewertung Kommunikation": [2],
            "Titel": ["R"],
            "Sternebewertung Image": [5],
        })
        df = normalize_columns(df)
        result = extract_sternebewertungen_by_name(df)
        assert result["sternebewertung_kommunikation"].iloc[0] == 2.0
        assert result["sternebewertung_image"].iloc[0] == 5.0
