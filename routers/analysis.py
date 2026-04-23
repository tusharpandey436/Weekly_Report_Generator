"""
Analysis router — exposes POST /analyze.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from core.exceptions import (
    AIServiceError,
    EmptyDateRangeError,
    InvalidFileFormatError,
    MissingDateColumnError,
)
from schemas.analysis import (
    AnalysisResponse,
    ErrorResponse,
    WeeklyStatRecord,
    WeeklySummaryRecord,
)
from services.ai_service import generate_weekly_summary
from services.data_processor import (
    build_weekly_stats,
    filter_by_date_range,
    parse_and_validate_excel,
    resample_weekly,
)

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",  # Some clients send .xlsx with this type
}


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request / validation error"},
        422: {"model": ErrorResponse, "description": "Unprocessable file or date range"},
        500: {"model": ErrorResponse, "description": "Internal / AI service error"},
    },
    summary="Analyze an Excel file and return AI-powered weekly summaries",
)
async def analyze_excel(
    file: UploadFile = File(..., description="Excel file (.xlsx) containing a 'Date' column"),
    start_date: str = Form(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Form(..., description="End date in YYYY-MM-DD format"),
) -> AnalysisResponse:
    """
    **Pipeline**

    1. Validate & read the uploaded `.xlsx` file.
    2. Parse and coerce the `Date` column.
    3. Filter rows to `[start_date, end_date]`.
    4. Resample into weekly (Mon-Sun) buckets.
    5. For each week, call the AI service to produce a narrative summary.
    6. Return raw stats + AI summaries as structured JSON.
    """

    # ── 0. Validate dates ─────────────────────────────────────────────────────
    from datetime import date as date_type
    try:
        parsed_start = date_type.fromisoformat(start_date)
        parsed_end = date_type.fromisoformat(end_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format. Use YYYY-MM-DD. Error: {exc}",
        )

    if parsed_end < parsed_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be on or after start_date.",
        )

    # ── 1. Validate file type ─────────────────────────────────────────────────
    filename = file.filename or ""
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx files are supported.",
        )

    # ── 2. Read file bytes ────────────────────────────────────────────────────
    file_bytes = await file.read()

    # ── 3. Parse & validate Excel ─────────────────────────────────────────────
    try:
        df = parse_and_validate_excel(file_bytes)
    except InvalidFileFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_type": "InvalidFileFormat", "message": str(exc)},
        )
    except MissingDateColumnError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_type": "MissingDateColumn",
                "message": str(exc),
                "available_columns": exc.available_columns,
            },
        )

    # ── 4. Filter to date range ───────────────────────────────────────────────
    try:
        filtered_df = filter_by_date_range(df, parsed_start, parsed_end)
    except EmptyDateRangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_type": "EmptyDateRange", "message": str(exc)},
        )

    # ── 5. Resample weekly ────────────────────────────────────────────────────
    weekly_agg, weekly_slices = resample_weekly(filtered_df)
    weekly_stats = build_weekly_stats(weekly_agg, weekly_slices)

    if not weekly_stats:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_type": "EmptyDateRange",
                "message": "No weekly buckets could be created from the filtered data.",
            },
        )

    # ── 6. AI summaries ───────────────────────────────────────────────────────
    weekly_results: list[WeeklySummaryRecord] = []

    for i, week_data in enumerate(weekly_stats):
        previous_week_data = weekly_stats[i - 1] if i > 0 else None

        try:
            ai_result = generate_weekly_summary(
                current_week=week_data,
                previous_week=previous_week_data,
            )
        except AIServiceError as exc:
            logger.warning("AI service failed for week %s: %s", week_data["week_ending"], exc)
            ai_result = {
                "summary": "AI summary unavailable — using the local weekly summary instead.",
                "week_summary": "This week summary was generated locally from the Description section.",
                "week_summary_sections": [
                    {"title": "What Happened", "text": "The workbook used the local description-based summary."},
                    {"title": "Main Focus", "text": "The summary is based on the Description entries available for the week."},
                    {"title": "Outcome", "text": "The app fell back to the local summary because AI generation was unavailable."},
                ],
                "summary_points": [
                    "AI summary was unavailable, so the app generated a local bullet-point recap from the uploaded data."
                ],
                "peak_day": week_data.get("peak_day"),
                "trend_vs_previous_week": "Unavailable.",
                "theme_groups": [],
            }

        weekly_results.append(
            WeeklySummaryRecord(
                week_ending=week_data["week_ending"],
                stats=WeeklyStatRecord(
                    week_ending=week_data["week_ending"],
                    metrics=week_data["metrics"],
                ),
                description_entries=week_data.get("description_entries", []),
                theme_groups=ai_result.get("theme_groups", []),
                week_summary=ai_result.get("week_summary", ai_result["summary"]),
                week_summary_sections=ai_result.get("week_summary_sections", []),
                ai_summary=ai_result["summary"],
                summary_points=ai_result.get("summary_points", []),
                peak_day=ai_result.get("peak_day") or week_data.get("peak_day"),
                trend_vs_previous_week=ai_result.get("trend_vs_previous_week"),
            )
        )

    # ── 7. Return structured response ─────────────────────────────────────────
    return AnalysisResponse(
        file_name=filename,
        start_date=str(parsed_start),
        end_date=str(parsed_end),
        total_weeks_analyzed=len(weekly_results),
        weekly_results=weekly_results,
    )
