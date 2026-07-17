"""
excel_service.py

Excel file upload and processing service.
Handles uploading Excel files with candidate and employee data,
normalizes columns, maps repeated "Sternebewertung" columns to
DB columns (sternebewertung_<topic>), and imports into Supabase.

Features:
- Decodes HTML entities (&lt; &gt; &amp; &quot; etc.) from text fields
- Normalizes column names to DB-friendly format
- Maps rating columns to specific topics by name (position-independent)
- Handles both candidate and employee data

Assumptions (based on your schemas):
- Candidates Excel is identified ONLY by column "Stellenbeschreibung" (-> stellenbeschreibung).
- Employee Excel does NOT have that column.
- Rating columns are either explicitly named (sternebewertung_<topic>) or generic
  (sternebewertung / sternebewertung_<N>) paired with the next topic column (legacy fallback).
- Candidates DB does NOT store topic comments (only the ratings); Employee DB stores BOTH ratings + topic comments.
"""

from __future__ import annotations

from fastapi import UploadFile
import pandas as pd
from typing import Dict, Any, List, Optional
from database.supabase_client import get_supabase_client  # no-op in demo mode
from services.csv_service import read_csv_to_dataframe
import io
import re
import html


# ----------------------------
# Whitelists and required columns
# ----------------------------

CANDIDATES_ALLOWED = {
    "titel","status","datum","update_datum",
    "durchschnittsbewertung","gerundete_durchschnittsbewertung",
    "stellenbeschreibung","verbesserungsvorschlaege",
    "sternebewertung_erklaerung_der_weiteren_schritte",
    "sternebewertung_zufriedenstellende_reaktion",
    "sternebewertung_vollstaendigkeit_der_infos",
    "sternebewertung_zufriedenstellende_antworten",
    "sternebewertung_angenehme_atmosphaere",
    "sternebewertung_professionalitaet_des_gespraechs",
    "sternebewertung_wertschaetzende_behandlung",
    "sternebewertung_erwartbarkeit_des_prozesses",
    "sternebewertung_zeitgerechte_zu_oder_absage",
    "sternebewertung_schnelle_antwort",
    "company_id",
}

EMPLOYEE_ALLOWED = {
    "titel","status","datum","update_datum",
    "durchschnittsbewertung","gerundete_durchschnittsbewertung",
    "jobbeschreibung",
    "gut_am_arbeitgeber_finde_ich",
    "schlecht_am_arbeitgeber_finde_ich",
    "verbesserungsvorschlaege",

    # numeric ratings
    "sternebewertung_arbeitsatmosphaere",
    "sternebewertung_image",
    "sternebewertung_work_life_balance",
    "sternebewertung_karriere_weiterbildung",
    "sternebewertung_gehalt_sozialleistungen",
    "sternebewertung_kollegenzusammenhalt",
    "sternebewertung_umwelt_sozialbewusstsein",
    "sternebewertung_vorgesetztenverhalten",
    "sternebewertung_kommunikation",
    "sternebewertung_interessante_aufgaben",
    "sternebewertung_umgang_mit_aelteren_kollegen",
    "sternebewertung_arbeitsbedingungen",
    "sternebewertung_gleichberechtigung",

    # topic text columns (existieren bei employee!)
    "arbeitsatmosphaere",
    "image",
    "work_life_balance",
    "karriere_weiterbildung",
    "gehalt_sozialleistungen",
    "kollegenzusammenhalt",
    "umwelt_sozialbewusstsein",
    "vorgesetztenverhalten",
    "kommunikation",
    "interessante_aufgaben",
    "umgang_mit_aelteren_kollegen",
    "arbeitsbedingungen",
    "gleichberechtigung",
    "company_id",
}

# Minimum columns that must be present for each sheet type.
CANDIDATES_REQUIRED: set[str] = {"titel", "stellenbeschreibung"}
EMPLOYEE_REQUIRED: set[str] = {"titel"}


# ----------------------------
# Helpers
# ----------------------------

def slugify(s: str) -> str:
    s = str(s).strip().lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def clean_text(text: str) -> str:
    """
    Clean text by decoding HTML entities.
    Converts &lt;br/&gt; to <br/>, &amp; to &, etc.
    """
    if not text:
        return text
    # Decode HTML entities like &lt; &gt; &amp; &quot; etc.
    return html.unescape(text)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to DB-friendly snake_case-ish:
    - Lowercase
    - German umlauts replaced
    - Non-alphanum -> underscore
    """
    df = df.copy()
    df.columns = [slugify(c) for c in df.columns]
    return df


def is_sternebewertung_col(col: str) -> bool:
    """
    After normalize_columns(), repeated headers like:
    'Sternebewertung', 'Sternebewertung.1', ...
    can become:
    - 'sternebewertung', 'sternebewertung_1', 'sternebewertung_2', ...
    depending on how pandas read the file / header duplicates.
    We treat 'sternebewertung' and 'sternebewertung_<number>' as rating columns.
    """
    return col == "sternebewertung" or re.fullmatch(r"sternebewertung_\d+", col) is not None


def extract_sternebewertungen_by_name(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resolve Sternebewertung columns by header name, not column position.

    Two accepted naming styles:
    1. Explicit  – column already carries the topic in its name after normalization,
                   e.g. 'sternebewertung_arbeitsatmosphaere'.  These are converted to
                   numeric in-place; no positional lookup is needed.
    2. Generic   – column is named 'sternebewertung' or 'sternebewertung_<N>' (pandas
                   duplicate-suffix).  Legacy positional fallback: the immediately
                   following column is treated as the topic name.  Kept for backward
                   compatibility with Excel exports that use repeated generic headers.

    In both cases the intermediate generic sternebewertung columns are dropped at the end.
    """
    df = df.copy()
    cols = list(df.columns)

    # Step 1 – explicit naming: sternebewertung_<word> columns are already correct.
    for col in cols:
        if col.startswith("sternebewertung_") and not re.fullmatch(r"sternebewertung_\d+", col):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Step 2 – generic naming: positional fallback for 'sternebewertung' / 'sternebewertung_\d+'.
    for i, col in enumerate(cols):
        if is_sternebewertung_col(col):
            if i + 1 >= len(cols):
                continue
            topic_col = cols[i + 1]
            new_col = f"sternebewertung_{slugify(topic_col)}"
            if new_col not in df.columns:
                df[new_col] = pd.to_numeric(df[col], errors="coerce")

    drop_cols = [c for c in df.columns if is_sternebewertung_col(c)]
    df = df.drop(columns=drop_cols, errors="ignore")
    return df


def validate_required_columns(df: pd.DataFrame, required: set[str]) -> list[str]:
    """Return sorted list of required column names absent from *df*."""
    return sorted(col for col in required if col not in df.columns)


def to_iso_dt(val) -> Optional[str]:
    """
    Convert Excel date/time cell to ISO string for Supabase.
    Returns None if invalid/empty.
    """
    if val is None or (isinstance(val, float) and pd.isna(val)) or pd.isna(val):
        return None
    dt = pd.to_datetime(val, errors="coerce")
    if pd.isna(dt):
        return None
    # Keep timezone-naive ISO; Postgres can parse it. If you need timezone-aware, adjust here.
    return dt.isoformat()


def get_star_columns(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if c.startswith("sternebewertung_")]


# ----------------------------
# Main service
# ----------------------------

class ExcelProcessor:
    """Process Excel files and import data into database."""

    def __init__(self):
        self.supabase = get_supabase_client()

    async def process_excel_file(self, file: UploadFile, company_id: int) -> Dict[str, Any]:
        """Process an uploaded Excel (.xlsx / .xls) file."""
        filename = getattr(file, "filename", None)
        try:
            contents = await file.read()
            if not contents:
                return self._error_result(filename, "Leere Datei oder Upload-Inhalt leer.")
            df = pd.read_excel(io.BytesIO(contents))
            return await self._process_dataframe(df, filename, company_id, warnings=[])
        except Exception as exc:
            return self._error_result(filename, str(exc))

    async def process_csv_file(self, file: UploadFile, company_id: int) -> Dict[str, Any]:
        """
        Process an uploaded CSV file.

        Automatically detects delimiter (comma / semicolon / tab) and encoding
        (UTF-8 preferred; Latin-1 fallback surfaced as a user-facing warning).
        Column matching uses the same name-based logic as the Excel importer.
        """
        filename = getattr(file, "filename", None)
        try:
            contents = await file.read()
            if not contents:
                return self._error_result(filename, "Leere Datei oder Upload-Inhalt leer.")
            df, warnings = read_csv_to_dataframe(contents)
            return await self._process_dataframe(df, filename, company_id, warnings=warnings)
        except Exception as exc:
            return self._error_result(filename, str(exc))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _error_result(filename: Optional[str], message: str) -> Dict[str, Any]:
        return {
            "status": "error",
            "filename": filename,
            "total_rows": 0,
            "detected_type": None,
            "imported": {"candidates": 0, "employees": 0},
            "errors": [message],
            "warnings": [],
        }

    async def _process_dataframe(
        self,
        df: pd.DataFrame,
        filename: Optional[str],
        company_id: int,
        warnings: List[str],
    ) -> Dict[str, Any]:
        """
        Shared processing pipeline for both Excel and CSV uploads.

        Returns:
            {
              "status": "success" | "error",
              "filename": str,
              "total_rows": int,
              "detected_type": "candidates" | "employees" | None,
              "imported": {"candidates": int, "employees": int},
              "errors": [...],
              "warnings": [...],   # non-fatal issues (e.g. encoding fallback)
            }
        """
        result: Dict[str, Any] = {
            "status": "success",
            "filename": filename,
            "total_rows": int(len(df)),
            "detected_type": None,
            "imported": {"candidates": 0, "employees": 0},
            "errors": [],
            "warnings": list(warnings),
        }

        try:
            # Normalize & map ratings by header name (position-independent)
            df = normalize_columns(df)
            df = extract_sternebewertungen_by_name(df)

            # Detect type and validate required columns
            if self._is_candidates_data(df):
                result["detected_type"] = "candidates"
                missing = validate_required_columns(df, CANDIDATES_REQUIRED)
                if missing:
                    result["status"] = "error"
                    result["errors"].append(
                        f"Required columns missing for candidates sheet: {', '.join(missing)}"
                    )
                    return result
                imported, errors = await self._import_candidates(df, company_id)
                result["imported"]["candidates"] = imported
                result["errors"].extend(errors)
            else:
                result["detected_type"] = "employees"
                missing = validate_required_columns(df, EMPLOYEE_REQUIRED)
                if missing:
                    result["status"] = "error"
                    result["errors"].append(
                        f"Required columns missing for employees sheet: {', '.join(missing)}"
                    )
                    return result
                imported, errors = await self._import_employees(df, company_id)
                result["imported"]["employees"] = imported
                result["errors"].extend(errors)

            if (result["imported"]["candidates"] + result["imported"]["employees"]) == 0 and result["errors"]:
                result["status"] = "error"

        except Exception as exc:
            result["status"] = "error"
            result["errors"].append(str(exc))

        return result

    def _is_candidates_data(self, df: pd.DataFrame) -> bool:
        # Candidates Excel is ONLY recognized by "stellenbeschreibung"
        return "stellenbeschreibung" in df.columns

    # Employee is the "else" case; kept for completeness/debugging
    def _is_employee_data(self, df: pd.DataFrame) -> bool:
        return "stellenbeschreibung" not in df.columns

    async def _import_candidates(self, df: pd.DataFrame, company_id: int) -> tuple[int, List[str]]:
        """
        Candidates:
        - store base fields + star ratings that exist in candidates DB
        - DO NOT store topic comment columns (not present in candidates table)
        - whitelist by CANDIDATES_ALLOWED
        """
        errors: List[str] = []
        rows_to_insert: List[Dict[str, Any]] = []

        # only star columns that exist in DB schema
        star_columns = [c for c in get_star_columns(df) if c in CANDIDATES_ALLOWED]

        for idx, row in df.iterrows():
            try:
                data: Dict[str, Any] = {
                    "titel": clean_text(str(row.get("titel"))) if pd.notna(row.get("titel")) else None,
                    "status": clean_text(str(row.get("status"))) if pd.notna(row.get("status")) else None,
                    "datum": to_iso_dt(row.get("datum")),
                    "update_datum": to_iso_dt(row.get("update_datum")),
                    "stellenbeschreibung": clean_text(str(row.get("stellenbeschreibung"))) if pd.notna(row.get("stellenbeschreibung")) else None,
                    "verbesserungsvorschlaege": clean_text(str(row.get("verbesserungsvorschlaege"))) if pd.notna(row.get("verbesserungsvorschlaege")) else None,
                    "company_id": company_id,
                }

                # Ratings
                vals: List[float] = []
                for c in star_columns:
                    v = row.get(c)
                    if pd.notna(v):
                        fv = float(v)
                        data[c] = fv
                        vals.append(fv)

                # Average: prefer Excel values if present; else compute from stars
                avg_excel = row.get("durchschnittsbewertung")
                rnd_excel = row.get("gerundete_durchschnittsbewertung")

                avg = float(avg_excel) if pd.notna(avg_excel) else (sum(vals) / len(vals) if vals else None)
                rnd = float(rnd_excel) if pd.notna(rnd_excel) else (round(avg, 1) if avg is not None else None)

                data["durchschnittsbewertung"] = avg
                data["gerundete_durchschnittsbewertung"] = rnd

                # Whitelist (critical)
                data = {k: v for k, v in data.items() if k in CANDIDATES_ALLOWED}

                rows_to_insert.append(data)

            except Exception as e:
                errors.append(f"candidates row {idx}: {e}")

        if rows_to_insert:
            try:
                self.supabase.table("candidates").insert(rows_to_insert).execute()
            except Exception as e:
                # If bulk insert fails, surface the error (often schema mismatch)
                errors.append(f"candidates bulk insert failed: {e}")
                # Optional: fallback to per-row insert for debugging (commented)
                # for i, payload in enumerate(rows_to_insert):
                #     try:
                #         self.supabase.table("candidates").insert(payload).execute()
                #     except Exception as ee:
                #         errors.append(f"candidates row insert failed (batch index {i}): {ee}")
                return 0, errors

        return len(rows_to_insert), errors

    async def _import_employees(self, df: pd.DataFrame, company_id: int) -> tuple[int, List[str]]:
        """
        Employees:
        - store base fields
        - store star ratings columns that exist in employee DB
        - store topic comment columns (text) that exist in employee DB
        - whitelist by EMPLOYEE_ALLOWED
        """
        errors: List[str] = []
        rows_to_insert: List[Dict[str, Any]] = []

        star_columns = [c for c in get_star_columns(df) if c in EMPLOYEE_ALLOWED]

        # topic text columns = columns present in DF that are also allowed and not rating columns
        # (plus excluding base columns we already map explicitly)
        base_cols = {
            "titel", "status", "datum", "update_datum",
            "durchschnittsbewertung", "gerundete_durchschnittsbewertung",
            "jobbeschreibung", "gut_am_arbeitgeber_finde_ich",
            "schlecht_am_arbeitgeber_finde_ich", "verbesserungsvorschlaege",
            "stellenbeschreibung",  # not used for employee
        }

        topic_text_cols = [
            c for c in df.columns
            if (c in EMPLOYEE_ALLOWED and not c.startswith("sternebewertung_") and c not in base_cols)
        ]

        for idx, row in df.iterrows():
            try:
                data: Dict[str, Any] = {
                    "titel": clean_text(str(row.get("titel"))) if pd.notna(row.get("titel")) else None,
                    "status": clean_text(str(row.get("status"))) if pd.notna(row.get("status")) else None,
                    "datum": to_iso_dt(row.get("datum")),
                    "update_datum": to_iso_dt(row.get("update_datum")),
                    "jobbeschreibung": clean_text(str(row.get("jobbeschreibung"))) if pd.notna(row.get("jobbeschreibung")) else None,
                    "gut_am_arbeitgeber_finde_ich": clean_text(str(row.get("gut_am_arbeitgeber_finde_ich"))) if pd.notna(row.get("gut_am_arbeitgeber_finde_ich")) else None,
                    "schlecht_am_arbeitgeber_finde_ich": clean_text(str(row.get("schlecht_am_arbeitgeber_finde_ich"))) if pd.notna(row.get("schlecht_am_arbeitgeber_finde_ich")) else None,
                    "verbesserungsvorschlaege": clean_text(str(row.get("verbesserungsvorschlaege"))) if pd.notna(row.get("verbesserungsvorschlaege")) else None,
                    "company_id": company_id,
                }

                # Topic comments (text)
                for c in topic_text_cols:
                    v = row.get(c)
                    if pd.notna(v):
                        data[c] = clean_text(str(v))

                # Ratings
                vals: List[float] = []
                for c in star_columns:
                    v = row.get(c)
                    if pd.notna(v):
                        fv = float(v)
                        data[c] = fv
                        vals.append(fv)

                # Average: prefer Excel values; else compute
                avg_excel = row.get("durchschnittsbewertung")
                rnd_excel = row.get("gerundete_durchschnittsbewertung")

                avg = float(avg_excel) if pd.notna(avg_excel) else (sum(vals) / len(vals) if vals else None)
                rnd = float(rnd_excel) if pd.notna(rnd_excel) else (round(avg, 1) if avg is not None else None)

                data["durchschnittsbewertung"] = avg
                data["gerundete_durchschnittsbewertung"] = rnd

                # Whitelist (critical)
                data = {k: v for k, v in data.items() if k in EMPLOYEE_ALLOWED}

                rows_to_insert.append(data)

            except Exception as e:
                errors.append(f"employees row {idx}: {e}")

        if rows_to_insert:
            try:
                # Your table name is "employee" per schema
                self.supabase.table("employee").insert(rows_to_insert).execute()
            except Exception as e:
                errors.append(f"employees bulk insert failed: {e}")
                return 0, errors

        return len(rows_to_insert), errors
