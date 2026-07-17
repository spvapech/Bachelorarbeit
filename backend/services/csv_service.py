"""
csv_service.py

CSV ingestion with automatic delimiter and encoding detection.

Supported delimiters: comma (,), semicolon (;), tab (\\t)
Encoding strategy  : try UTF-8 first; fall back to Latin-1 (ISO-8859-1) with a
                     user-facing warning rather than crashing.
"""

from __future__ import annotations

import csv
import io
import pandas as pd

SUPPORTED_DELIMITERS = [",", ";", "\t"]
SNIFF_SAMPLE_SIZE = 8192


def detect_encoding(raw: bytes) -> tuple[str, bool]:
    """
    Attempt UTF-8 decoding first; fall back to Latin-1.

    Returns:
        (encoding_name, had_fallback)
    """
    try:
        raw.decode("utf-8")
        return "utf-8", False
    except UnicodeDecodeError:
        return "latin-1", True


def detect_delimiter(text: str) -> str:
    """
    Sniff the most likely field delimiter from the first 8 KB of *text*.

    Strategy:
    1. Let csv.Sniffer try (handles quoted fields correctly).
    2. If Sniffer fails or returns an unsupported delimiter, count raw occurrences
       across the first 5 lines and pick the most frequent supported delimiter.
    3. Fallback: comma.
    """
    sample = text[:SNIFF_SAMPLE_SIZE]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        if dialect.delimiter in SUPPORTED_DELIMITERS:
            return dialect.delimiter
    except csv.Error:
        pass

    lines = sample.splitlines()[:5]
    counts = {d: sum(line.count(d) for line in lines) for d in SUPPORTED_DELIMITERS}
    best = max(counts, key=lambda d: counts[d])
    return best if counts[best] > 0 else ","


def read_csv_to_dataframe(raw: bytes) -> tuple[pd.DataFrame, list[str]]:
    """
    Parse *raw* CSV bytes into a DataFrame, returning any encoding warnings.

    Steps:
    1. Detect encoding (UTF-8 → Latin-1 fallback).
    2. Detect delimiter.
    3. Parse with pandas; all columns read as str to preserve leading zeros etc.
    4. Strip surrounding whitespace from every string cell.

    Returns:
        (df, warnings)   — warnings is empty on clean UTF-8 files.

    Raises:
        ValueError  if the content cannot be parsed as a valid CSV at all.
    """
    warnings: list[str] = []

    encoding, had_fallback = detect_encoding(raw)
    if had_fallback:
        warnings.append(
            "Encoding-Warnung: Die Datei ist nicht UTF-8-kodiert. "
            "Latin-1 (ISO-8859-1) wird als Fallback verwendet. "
            "Bitte exportieren Sie die CSV-Datei als UTF-8 für beste Ergebnisse."
        )

    text = raw.decode(encoding, errors="replace")
    delimiter = detect_delimiter(text)

    try:
        df = pd.read_csv(
            io.StringIO(text),
            sep=delimiter,
            dtype=str,
            keep_default_na=False,  # avoid converting "NA" strings to NaN prematurely
        )
    except Exception as exc:
        raise ValueError(f"CSV konnte nicht gelesen werden: {exc}") from exc

    # Strip surrounding whitespace from every string cell (common in CSV exports)
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    # Treat empty strings as proper NaN so downstream logic behaves like Excel
    df.replace("", pd.NA, inplace=True)

    return df, warnings
