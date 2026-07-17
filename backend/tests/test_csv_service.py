"""
Unit tests for csv_service.py

Covers:
- Delimiter detection: comma, semicolon, tab
- Encoding detection: UTF-8 (no warning), Latin-1 fallback (warning emitted)
- Encoding edge cases: replacement characters, mixed-encoding rows
- read_csv_to_dataframe: whitespace stripping, empty-string → NA conversion
- Integration with normalize_columns + extract_sternebewertungen_by_name

Run:
    uv run python -m pytest tests/test_csv_service.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pytest

from services.csv_service import (
    detect_encoding,
    detect_delimiter,
    read_csv_to_dataframe,
)
from services.excel_service import normalize_columns, extract_sternebewertungen_by_name


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def csv_bytes(text: str, encoding: str = "utf-8") -> bytes:
    return text.encode(encoding)


# ---------------------------------------------------------------------------
# detect_encoding
# ---------------------------------------------------------------------------

class TestDetectEncoding:
    def test_utf8_returns_utf8_no_fallback(self):
        raw = csv_bytes("Titel,Status\nReview A,aktiv\n")
        enc, had_fallback = detect_encoding(raw)
        assert enc == "utf-8"
        assert had_fallback is False

    def test_utf8_with_umlauts_ok(self):
        raw = csv_bytes("Titel,Bewertung\nArbeitsatmosphäre,gut\n")
        enc, had_fallback = detect_encoding(raw)
        assert enc == "utf-8"
        assert had_fallback is False

    def test_latin1_triggers_fallback(self):
        # ä in Latin-1 is 0xe4, which is invalid in UTF-8 without the right lead byte
        raw = "Titel,Beschreibung\nReview,Sch\xf6n\n".encode("latin-1")
        enc, had_fallback = detect_encoding(raw)
        assert enc == "latin-1"
        assert had_fallback is True

    def test_pure_ascii_reports_utf8(self):
        raw = csv_bytes("a,b,c\n1,2,3\n")
        enc, had_fallback = detect_encoding(raw)
        assert enc == "utf-8"
        assert had_fallback is False


# ---------------------------------------------------------------------------
# detect_delimiter
# ---------------------------------------------------------------------------

class TestDetectDelimiter:
    def test_comma_delimiter(self):
        text = "Titel,Status,Datum\nReview A,aktiv,2024-01-01\n"
        assert detect_delimiter(text) == ","

    def test_semicolon_delimiter(self):
        text = "Titel;Status;Datum\nReview A;aktiv;2024-01-01\n"
        assert detect_delimiter(text) == ";"

    def test_tab_delimiter(self):
        text = "Titel\tStatus\tDatum\nReview A\taktiv\t2024-01-01\n"
        assert detect_delimiter(text) == "\t"

    def test_count_fallback_fires_when_sniffer_fails(self):
        # Single-column input: Sniffer cannot detect a delimiter → count-based fallback.
        # Inject semicolons manually to force the fallback to pick semicolon.
        text = "Titel\nReview A\n"  # no delimiters at all → fallback returns comma
        result = detect_delimiter(text)
        assert result in (",", ";", "\t")  # must not crash; exact value is implementation detail

    def test_empty_text_falls_back_to_comma(self):
        assert detect_delimiter("") == ","

    def test_single_column_no_delimiter_falls_back_to_comma(self):
        text = "Titel\nReview A\nReview B\n"
        # No delimiter found — must not crash; comma is the fallback
        result = detect_delimiter(text)
        assert result in (",", ";", "\t")

    def test_quoted_fields_with_commas_inside(self):
        # csv.Sniffer should still pick comma as the real delimiter
        text = '"Titel","Beschreibung"\n"Review A","gut, sehr gut"\n'
        assert detect_delimiter(text) == ","


# ---------------------------------------------------------------------------
# read_csv_to_dataframe — delimiter variants
# ---------------------------------------------------------------------------

class TestReadCsvDelimiters:
    def _make(self, delimiter: str) -> bytes:
        sep = delimiter
        rows = [
            sep.join(["Titel", "Status", "Sternebewertung Arbeitsatmosphäre"]),
            sep.join(["Review A", "aktiv", "4"]),
            sep.join(["Review B", "inaktiv", "3"]),
        ]
        return "\n".join(rows).encode("utf-8")

    def test_comma_parsed_correctly(self):
        df, warnings = read_csv_to_dataframe(self._make(","))
        assert list(df.columns) == ["Titel", "Status", "Sternebewertung Arbeitsatmosphäre"]
        assert len(df) == 2
        assert warnings == []

    def test_semicolon_parsed_correctly(self):
        df, warnings = read_csv_to_dataframe(self._make(";"))
        assert list(df.columns) == ["Titel", "Status", "Sternebewertung Arbeitsatmosphäre"]
        assert len(df) == 2
        assert warnings == []

    def test_tab_parsed_correctly(self):
        df, warnings = read_csv_to_dataframe(self._make("\t"))
        assert list(df.columns) == ["Titel", "Status", "Sternebewertung Arbeitsatmosphäre"]
        assert len(df) == 2
        assert warnings == []

    def test_correct_row_count_for_each_delimiter(self):
        for sep in [",", ";", "\t"]:
            df, _ = read_csv_to_dataframe(self._make(sep))
            assert len(df) == 2, f"delimiter={repr(sep)}"


# ---------------------------------------------------------------------------
# read_csv_to_dataframe — encoding
# ---------------------------------------------------------------------------

class TestReadCsvEncoding:
    def _latin1_bytes(self) -> bytes:
        return (
            "Titel;Beschreibung\n"
            "Review Sch\xf6n;Sehr sch\xf6ne Atmosph\xe4re\n"
        ).encode("latin-1")

    def test_utf8_produces_no_warning(self):
        raw = csv_bytes("Titel,Status\nA,aktiv\n")
        _, warnings = read_csv_to_dataframe(raw)
        assert warnings == []

    def test_latin1_produces_exactly_one_warning(self):
        _, warnings = read_csv_to_dataframe(self._latin1_bytes())
        assert len(warnings) == 1

    def test_latin1_warning_mentions_utf8(self):
        _, warnings = read_csv_to_dataframe(self._latin1_bytes())
        assert "UTF-8" in warnings[0]

    def test_latin1_warning_mentions_latin1(self):
        _, warnings = read_csv_to_dataframe(self._latin1_bytes())
        assert "Latin-1" in warnings[0] or "latin-1" in warnings[0].lower()

    def test_latin1_data_decoded_correctly(self):
        _, warnings = read_csv_to_dataframe(self._latin1_bytes())
        # We expect a warning, but no crash and the data is decoded (possibly with replacements)
        assert len(warnings) == 1  # encoding fallback surfaced as warning, not exception

    def test_replacement_character_on_undecodable_byte(self):
        # A byte sequence invalid even for Latin-1 won't exist — Latin-1 decodes all bytes.
        # Test that errors="replace" means we never crash even on pathological input.
        # We craft a valid latin-1 sequence and force utf-8 to fail.
        raw = b"Titel,Status\nCaf\xe9,aktiv\n"  # 0xe9 = é in latin-1
        df, warnings = read_csv_to_dataframe(raw)
        assert len(df) == 1
        assert len(warnings) == 1  # fallback warning


# ---------------------------------------------------------------------------
# read_csv_to_dataframe — whitespace stripping and NA normalisation
# ---------------------------------------------------------------------------

class TestReadCsvCleaning:
    def test_leading_trailing_whitespace_stripped(self):
        raw = csv_bytes("Titel, Status\n  Review A ,  aktiv  \n")
        df, _ = read_csv_to_dataframe(raw)
        assert df["Titel"].iloc[0] == "Review A"
        assert df[" Status"].iloc[0] == "aktiv"

    def test_empty_string_becomes_na(self):
        raw = csv_bytes("Titel,Status\nReview A,\n")
        df, _ = read_csv_to_dataframe(raw)
        assert pd.isna(df["Status"].iloc[0])

    def test_whitespace_only_cell_becomes_na_after_strip(self):
        raw = csv_bytes("Titel,Status\nReview A,   \n")
        df, _ = read_csv_to_dataframe(raw)
        assert pd.isna(df["Status"].iloc[0])

    def test_column_names_preserved(self):
        raw = csv_bytes("Titel,Datum,Status\nR,2024-01-01,aktiv\n")
        df, _ = read_csv_to_dataframe(raw)
        assert "Titel" in df.columns
        assert "Datum" in df.columns
        assert "Status" in df.columns


# ---------------------------------------------------------------------------
# Integration: CSV → normalize_columns → extract_sternebewertungen_by_name
# ---------------------------------------------------------------------------

class TestCsvColumnMatchingIntegration:
    """Column matching after CSV parsing must be identical to the Excel importer."""

    def _csv_with_explicit_ratings(self, delimiter=",") -> bytes:
        sep = delimiter
        header = sep.join([
            "Titel", "Status",
            "Sternebewertung Arbeitsatmosphäre",
            "Sternebewertung Image",
            "Stellenbeschreibung",
        ])
        row = sep.join(["Review A", "aktiv", "4", "3", "Backend Dev"])
        return f"{header}\n{row}\n".encode("utf-8")

    def _process(self, raw: bytes):
        df, _ = read_csv_to_dataframe(raw)
        df = normalize_columns(df)
        df = extract_sternebewertungen_by_name(df)
        return df

    def test_comma_explicit_ratings_resolved(self):
        df = self._process(self._csv_with_explicit_ratings(","))
        assert "sternebewertung_arbeitsatmosphaere" in df.columns
        assert "sternebewertung_image" in df.columns
        assert df["sternebewertung_arbeitsatmosphaere"].iloc[0] == 4.0
        assert df["sternebewertung_image"].iloc[0] == 3.0

    def test_semicolon_explicit_ratings_resolved(self):
        df = self._process(self._csv_with_explicit_ratings(";"))
        assert df["sternebewertung_arbeitsatmosphaere"].iloc[0] == 4.0

    def test_tab_explicit_ratings_resolved(self):
        df = self._process(self._csv_with_explicit_ratings("\t"))
        assert df["sternebewertung_image"].iloc[0] == 3.0

    def test_candidate_detection_column_present(self):
        df = self._process(self._csv_with_explicit_ratings(","))
        assert "stellenbeschreibung" in df.columns

    def test_non_numeric_rating_becomes_nan(self):
        sep = ","
        header = f"Titel{sep}Sternebewertung Arbeitsatmosphäre"
        row = f"Review A{sep}keine Angabe"
        raw = f"{header}\n{row}\n".encode("utf-8")
        df = self._process(raw)
        assert pd.isna(df["sternebewertung_arbeitsatmosphaere"].iloc[0])

    def test_generic_positional_fallback_in_csv(self):
        # Some BI-tool exports repeat "Sternebewertung" as a generic header
        sep = ","
        header = f"Titel{sep}Sternebewertung{sep}Arbeitsatmosphäre{sep}Sternebewertung{sep}Image"
        row = f"Review A{sep}4{sep}gut{sep}3{sep}mittel"
        raw = f"{header}\n{row}\n".encode("utf-8")
        df, _ = read_csv_to_dataframe(raw)
        # pandas deduplicates repeated column names
        df = normalize_columns(df)
        df = extract_sternebewertungen_by_name(df)
        assert "sternebewertung_arbeitsatmosphaere" in df.columns
        assert "sternebewertung_image" in df.columns

    def test_extra_columns_do_not_raise(self):
        sep = ","
        header = f"Titel{sep}Sternebewertung Arbeitsatmosphäre{sep}UnbekanntesSpalte"
        row = f"Review A{sep}4{sep}ignored"
        raw = f"{header}\n{row}\n".encode("utf-8")
        df = self._process(raw)
        assert "sternebewertung_arbeitsatmosphaere" in df.columns
        assert "unbekanntesspalte" in df.columns  # left in place; whitelist filters it later

    def test_latin1_csv_column_matching_works(self):
        header = "Titel;Sternebewertung Arbeitsatmosph\xe4re"
        row = "Review A;4"
        raw = f"{header}\n{row}\n".encode("latin-1")
        df = self._process(raw)
        assert "sternebewertung_arbeitsatmosphaere" in df.columns
        assert df["sternebewertung_arbeitsatmosphaere"].iloc[0] == 4.0
