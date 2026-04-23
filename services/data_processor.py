"""
Data processing service.

Responsibilities
────────────────
1. Parse the uploaded Excel bytes into a Pandas DataFrame.
2. Validate the presence and parseability of the 'Date' column.
3. Filter rows to the requested date range.
4. Resample into weekly (Mon-Sun) buckets and return aggregated stats.
"""

from __future__ import annotations

import io
from datetime import date

import pandas as pd

from core.config import settings
from core.exceptions import (
    EmptyDateRangeError,
    InvalidFileFormatError,
    MissingDateColumnError,
)

DESCRIPTION_HINTS = (
    "description",
    "desc",
    "details",
    "detail",
    "notes",
    "note",
    "summary",
    "work",
)


# ── Public API ────────────────────────────────────────────────────────────────

def parse_and_validate_excel(file_bytes: bytes) -> pd.DataFrame:
    """
    Read Excel bytes into a DataFrame and ensure the Date column exists
    and is properly typed.

    Raises
    ------
    InvalidFileFormatError  – file cannot be parsed by openpyxl/pandas.
    MissingDateColumnError  – Date column absent or not convertible.
    """
    try:
        df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
    except Exception as exc:
        raise InvalidFileFormatError(detail=str(exc)) from exc

    col = settings.DATE_COLUMN_NAME
    if col not in df.columns:
        raise MissingDateColumnError(
            column_name=col,
            available_columns=list(df.columns),
        )

    try:
        parsed_dates = pd.to_datetime(df[col], errors="coerce", format="mixed")
        if parsed_dates.isna().any():
            raise ValueError("One or more rows could not be parsed as dates.")
        df[col] = parsed_dates
    except Exception as exc:
        raise MissingDateColumnError(
            column_name=col,
            available_columns=list(df.columns),
        ) from exc

    df = df.set_index(col).sort_index()
    return df


def filter_by_date_range(
    df: pd.DataFrame,
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """
    Slice the DataFrame to [start_date, end_date] (inclusive).

    Raises
    ------
    EmptyDateRangeError – no rows survive the filter.
    """
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    filtered = df.loc[start_ts:end_ts]

    if filtered.empty:
        raise EmptyDateRangeError(
            start_date=str(start_date),
            end_date=str(end_date),
        )

    return filtered


def resample_weekly(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Group data into Mon-Sun weekly buckets using resample('W').

    Returns a mapping of  ``week_ending_iso_str -> daily_slice_df``
    so the AI layer has access to individual day rows for peak-day detection.

    Also returns a parallel aggregated frame for numeric stats.
    """
    # 'W' anchors to Sunday by default (period ending Sunday)
    numeric_df = df.select_dtypes(include="number")

    weekly_agg: pd.DataFrame = numeric_df.resample("W").agg(["sum", "mean"]).round(4)

    # Flatten multi-level columns: (col, agg) → "col_sum" / "col_mean"
    weekly_agg.columns = ["_".join(c).strip() for c in weekly_agg.columns]

    weekly_slices: dict[str, pd.DataFrame] = {}
    for period_end, group in df.resample("W"):
        if not group.empty:
            weekly_slices[period_end.strftime("%Y-%m-%d")] = group

    return weekly_agg, weekly_slices


def _get_description_columns(df: pd.DataFrame) -> list[str]:
    preferred = []
    target = settings.DESCRIPTION_COLUMN_NAME.strip().lower()
    for column in df.columns:
        normalized = str(column).strip().lower()
        if normalized == target:
            preferred.append(column)
    if preferred:
        return preferred

    fallback = []
    for column in df.columns:
        normalized = str(column).strip().lower()
        if any(hint in normalized for hint in DESCRIPTION_HINTS):
            fallback.append(column)
    return fallback


def _collect_description_entries(daily_slice: pd.DataFrame) -> list[str]:
    description_columns = _get_description_columns(daily_slice)
    if not description_columns:
        return []

    entries: list[str] = []
    for column in description_columns:
        for value in daily_slice[column].dropna().tolist():
            text = str(value).strip()
            if text:
                entries.append(text)

    deduped: list[str] = []
    seen = set()
    for entry in entries:
        normalized = entry.lower()
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(entry)
    return deduped


def build_weekly_stats(
    weekly_agg: pd.DataFrame,
    weekly_slices: dict[str, pd.DataFrame],
) -> list[dict]:
    """
    Convert the aggregated frame + daily slices into a list of dicts
    ready for Pydantic and AI consumption.
    """
    results = []
    for ts, row in weekly_agg.iterrows():
        week_key = ts.strftime("%Y-%m-%d")
        daily_slice = weekly_slices.get(week_key)
        description_entries = _collect_description_entries(daily_slice) if daily_slice is not None else []

        # Identify peak day (day with highest sum of numeric values)
        peak_day: str | None = None
        if daily_slice is not None and not daily_slice.empty:
            numeric_cols = daily_slice.select_dtypes(include="number")
            if not numeric_cols.empty:
                peak_idx = numeric_cols.sum(axis=1).idxmax()
                peak_day = peak_idx.strftime("%Y-%m-%d (%A)")

        results.append(
            {
                "week_ending": week_key,
                "metrics": row.to_dict(),
                "daily_data": (
                    daily_slice.reset_index()
                    .assign(Date=lambda x: x["Date"].dt.strftime("%Y-%m-%d"))
                    .to_dict(orient="records")
                    if daily_slice is not None
                    else []
                ),
                "description_entries": description_entries,
                "peak_day": peak_day,
            }
        )

    return results
