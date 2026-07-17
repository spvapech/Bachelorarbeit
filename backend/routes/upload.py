"""
API routes for file upload functionality.

Accepted formats: .xlsx, .xls, .csv
"""

import io
import math
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.excel_service import ExcelProcessor
from services.csv_service import read_csv_to_dataframe

router = APIRouter(prefix="/api", tags=["Upload"])

excel_processor = ExcelProcessor()

_EXCEL_EXTS = (".xlsx", ".xls")
_CSV_EXT    = ".csv"
_ALLOWED_EXTS = _EXCEL_EXTS + (_CSV_EXT,)


def _is_excel(filename: str) -> bool:
    return filename.lower().endswith(_EXCEL_EXTS)


def _is_csv(filename: str) -> bool:
    return filename.lower().endswith(_CSV_EXT)


@router.post("/upload-excel")
async def upload_excel(
    file: UploadFile = File(...),
    company_id: int = Form(...),
):
    """
    Accept an Excel (.xlsx / .xls) or CSV file and import its rows.

    CSV files are auto-detected for delimiter (comma, semicolon, tab) and
    encoding (UTF-8 preferred; Latin-1 fallback surfaced as a warning).
    Column matching is identical to the Excel importer.
    """
    if not file.filename.lower().endswith(_ALLOWED_EXTS):
        raise HTTPException(
            status_code=400,
            detail="Ungültiges Dateiformat. Erlaubt sind .xlsx, .xls und .csv.",
        )

    if _is_csv(file.filename):
        result = await excel_processor.process_csv_file(file, company_id=company_id)
    else:
        result = await excel_processor.process_excel_file(file, company_id=company_id)

    if result["status"] == "error":
        raise HTTPException(
            status_code=400,
            detail=result.get("errors", result.get("error", "Datei konnte nicht verarbeitet werden.")),
        )

    return result


@router.post("/preview-excel")
async def preview_excel(file: UploadFile = File(...)):
    """Return the first 10 rows of an Excel or CSV file without persisting any data."""
    if not file.filename.lower().endswith(_ALLOWED_EXTS):
        raise HTTPException(
            status_code=400,
            detail="Ungültiges Dateiformat. Erlaubt sind .xlsx, .xls und .csv.",
        )

    try:
        content = await file.read()
        warnings: list[str] = []

        if _is_csv(file.filename):
            df, warnings = read_csv_to_dataframe(content)
            df = df.head(10)
        else:
            df = pd.read_excel(io.BytesIO(content), nrows=10)

        columns = df.columns.tolist()

        def safe(v):
            if v is None:
                return None
            try:
                if isinstance(v, float) and math.isnan(v):
                    return None
            except TypeError:
                pass
            return str(v) if not isinstance(v, (int, float, bool, str)) else v

        rows = [[safe(cell) for cell in row] for row in df.values.tolist()]
        return {
            "filename": file.filename,
            "columns": columns,
            "rows": rows,
            "total_columns": len(columns),
            "warnings": warnings,
        }
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Datei konnte nicht gelesen werden: {exc}")
