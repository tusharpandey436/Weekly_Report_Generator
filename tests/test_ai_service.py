from __future__ import annotations

from services.ai_service import generate_weekly_summary


def test_local_weekly_summary_returns_bullets():
    current_week = {
        "week_ending": "2026-02-01",
        "metrics": {
            "Minutes_sum": 0,
            "Minutes_mean": 0,
            "#_sum": 30,
            "#_mean": 30,
        },
        "daily_data": [
            {"Date": "2026-02-01", "#": 30, "Minutes": 0},
        ],
        "description_entries": [
            "Reviewed client feedback and updated onboarding notes",
            "Prepared deployment checklist for the release",
            "Reviewed client feedback and updated onboarding notes",
        ],
        "peak_day": "2026-02-01 (Sunday)",
    }

    result = generate_weekly_summary(current_week)

    assert isinstance(result["summary_points"], list)
    assert result["summary_points"]
    assert any("client" in point.lower() for point in result["summary_points"])
    assert any("deployment" in point.lower() for point in result["summary_points"])
    assert len(result["summary_points"]) >= 2
    assert "executive summary" not in result["week_summary"].lower()
    assert len(result["week_summary_sections"]) == 3
    assert [section["title"] for section in result["week_summary_sections"]] == [
        "What Happened",
        "Main Focus",
        "Outcome",
    ]
    assert result["peak_day"] == "2026-02-01 (Sunday)"


def test_local_weekly_summary_keeps_more_description_lines():
    current_week = {
        "week_ending": "2026-02-08",
        "metrics": {},
        "daily_data": [],
        "description_entries": [
            "Reviewed client feedback and updated onboarding notes",
            "Prepared deployment checklist for the release",
            "Fixed issue in data import flow",
            "Wrote follow-up email to the client",
            "Updated weekly report dashboard",
        ],
        "peak_day": None,
    }

    result = generate_weekly_summary(current_week)

    assert len(result["summary_points"]) >= 5
    assert any("updated weekly report dashboard" in point.lower() for point in result["summary_points"])
    assert result["theme_groups"]
    assert any(group["theme"] == "Client Work" for group in result["theme_groups"])
    assert "description entries" in result["week_summary"].lower()
    assert len(result["week_summary_sections"]) == 3


def test_local_weekly_summary_skips_generic_off_entries():
    current_week = {
        "week_ending": "2026-03-01",
        "metrics": {},
        "daily_data": [],
        "description_entries": [
            "Weekly Off",
            "Leave",
            "Reviewed client feedback and updated onboarding notes",
        ],
        "peak_day": None,
    }

    result = generate_weekly_summary(current_week)

    assert any("reviewed client feedback" in point.lower() for point in result["summary_points"])
    assert not any("weekly off" in point.lower() for point in result["summary_points"])


def test_theme_groups_preserve_original_entries():
    current_week = {
        "week_ending": "2026-03-08",
        "metrics": {},
        "daily_data": [],
        "description_entries": [
            "Prepared deployment checklist for the release",
            "Prepared deployment checklist for the release",
            "Fixed issue in data import flow",
        ],
        "peak_day": None,
    }

    result = generate_weekly_summary(current_week)

    assert result["theme_groups"]
    deployment_group = next(group for group in result["theme_groups"] if group["theme"] == "Deployment & Release")
    assert deployment_group["count"] == 1
    assert deployment_group["entries"][0] == "Prepared deployment checklist for the release"
