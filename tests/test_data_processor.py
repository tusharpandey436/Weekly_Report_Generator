"""
Unit tests for the data processing service.
Run with: pytest tests/ -v
"""

from __future__ import annotations

import io
from datetime import date

import pandas as pd
import pytest

from ai_weekly_analyst.core.exceptions import (
    EmptyDateRangeError,
    InvalidFileFormatError,
    MissingDateColumnError,
)
from ai_weekly_analyst.services.data_processor import (
    build_weekly_stats,
    filter_by_date_range,
    parse_and_validate_excel,
    resample_weekly,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """10 rows of daily sales data spanning two full weeks."""
    return pd.DataFrame(
        {
            "Date": pd.date_range("2024-07-01", periods=14, freq="D"),
            "Sales": range(100, 114),
            "Units": range(10, 24),
        }
    )


@pytest.fixture
def sample_excel(sample_df) -> bytes:
    return _make_excel_bytes(sample_df)


# ── Tests: parse_and_validate_excel ───────────────────────────────────────────

class TestParseAndValidateExcel:
    def test_valid_file_returns_dataframe(self, sample_excel):
        df = parse_and_validate_excel(sample_excel)
        assert isinstance(df, pd.DataFrame)
        assert df.index.name == "Date"

    def test_missing_date_column_raises(self):
        bad_df = pd.DataFrame({"Revenue": [1, 2, 3]})
        with pytest.raises(MissingDateColumnError) as exc_info:
            parse_and_validate_excel(_make_excel_bytes(bad_df))
        assert "Date" in str(exc_info.value)

    def test_invalid_bytes_raises(self):
        with pytest.raises(InvalidFileFormatError):
            parse_and_validate_excel(b"this is not an excel file")

    def test_non_parseable_date_column_raises(self):
        bad_df = pd.DataFrame({"Date": ["not-a-date", "also-not"]})
        with pytest.raises(MissingDateColumnError):
            parse_and_validate_excel(_make_excel_bytes(bad_df))


# ── Tests: filter_by_date_range ───────────────────────────────────────────────

class TestFilterByDateRange:
    def test_returns_correct_rows(self, sample_df):
        df = sample_df.set_index("Date").sort_index()
        filtered = filter_by_date_range(df, date(2024, 7, 1), date(2024, 7, 7))
        assert len(filtered) == 7

    def test_empty_range_raises(self, sample_df):
        df = sample_df.set_index("Date").sort_index()
        with pytest.raises(EmptyDateRangeError):
            filter_by_date_range(df, date(2025, 1, 1), date(2025, 1, 31))

    def test_inclusive_boundaries(self, sample_df):
        df = sample_df.set_index("Date").sort_index()
        filtered = filter_by_date_range(df, date(2024, 7, 1), date(2024, 7, 1))
        assert len(filtered) == 1


# ── Tests: resample_weekly ────────────────────────────────────────────────────

class TestResampleWeekly:
    def test_returns_two_weekly_buckets(self, sample_df):
        df = sample_df.set_index("Date").sort_index()
        filtered = filter_by_date_range(df, date(2024, 7, 1), date(2024, 7, 14))
        weekly_agg, weekly_slices = resample_weekly(filtered)
        # 2024-07-01 to 2024-07-14 spans parts of 2-3 ISO weeks
        assert len(weekly_agg) >= 2

    def test_aggregated_columns_contain_sum_and_mean(self, sample_df):
        df = sample_df.set_index("Date").sort_index()
        filtered = filter_by_date_range(df, date(2024, 7, 1), date(2024, 7, 14))
        weekly_agg, _ = resample_weekly(filtered)
        cols = list(weekly_agg.columns)
        assert any("_sum" in c for c in cols)
        assert any("_mean" in c for c in cols)


# ── Tests: build_weekly_stats ─────────────────────────────────────────────────

class TestBuildWeeklyStats:
    def test_output_structure(self, sample_df):
        df = sample_df.set_index("Date").sort_index()
        filtered = filter_by_date_range(df, date(2024, 7, 1), date(2024, 7, 14))
        weekly_agg, weekly_slices = resample_weekly(filtered)
        stats = build_weekly_stats(weekly_agg, weekly_slices)
        assert isinstance(stats, list)
        for week in stats:
            assert "week_ending" in week
            assert "metrics" in week
            assert "peak_day" in week
