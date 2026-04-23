"""
Description-first weekly summary generation.

The service groups workbook `Description` rows into themes, surfaces the raw
description log, and builds readable weekly bullets from the actual work notes.
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from typing import Any

from core.config import settings

logger = logging.getLogger(__name__)

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "your",
    "our",
    "you",
    "are",
    "was",
    "were",
    "been",
    "will",
    "have",
    "has",
    "had",
    "done",
    "work",
    "worked",
    "working",
    "task",
    "tasks",
    "project",
    "projects",
    "description",
    "descriptions",
    "details",
    "detail",
    "note",
    "notes",
    "activity",
    "activities",
    "item",
    "items",
    "week",
    "day",
    "days",
    "today",
    "yesterday",
    "daily",
    "total",
    "totals",
    "summary",
    "summaries",
    "report",
    "reports",
}

ACTION_WORDS = {
    "reviewed",
    "review",
    "updated",
    "update",
    "prepared",
    "prepare",
    "fixed",
    "fix",
    "wrote",
    "write",
    "created",
    "create",
    "added",
    "add",
    "improved",
    "improve",
    "handled",
    "handle",
    "completed",
    "complete",
    "checked",
    "check",
    "tested",
    "test",
    "built",
    "build",
    "implemented",
    "implement",
    "coordinated",
    "coordinate",
    "documented",
    "document",
    "investigated",
    "investigate",
    "resolved",
    "resolve",
    "followed",
    "follow",
    "sent",
    "send",
    "shared",
    "share",
    "planned",
    "plan",
    "discussed",
    "discuss",
}

GENERIC_DESCRIPTION_PHRASES = (
    "weekly off",
    "day off",
    "leave",
    "holiday",
    "week off",
    "no work",
    "not working",
    "off",
)

THEME_RULES = (
    {
        "theme": "Client Work",
        "keywords": (
            "client",
            "customer",
            "feedback",
            "onboarding",
            "stakeholder",
            "meeting",
            "demo",
            "call",
            "review",
        ),
    },
    {
        "theme": "Deployment & Release",
        "keywords": (
            "deploy",
            "deployment",
            "release",
            "rollout",
            "production",
            "publish",
            "launch",
            "checklist",
        ),
    },
    {
        "theme": "Bug Fixes & Data Flow",
        "keywords": (
            "fix",
            "bug",
            "issue",
            "error",
            "import",
            "flow",
            "crash",
            "troubleshoot",
            "resolve",
        ),
    },
    {
        "theme": "Reporting & Dashboard",
        "keywords": (
            "report",
            "dashboard",
            "analytics",
            "metric",
            "summary",
            "chart",
            "table",
        ),
    },
    {
        "theme": "Documentation & Planning",
        "keywords": (
            "document",
            "documentation",
            "notes",
            "doc",
            "planning",
            "plan",
            "spec",
            "wiki",
        ),
    },
    {
        "theme": "Communication & Follow-up",
        "keywords": (
            "email",
            "follow-up",
            "follow up",
            "message",
            "response",
            "reply",
            "ping",
            "communication",
        ),
    },
    {
        "theme": "Coordination & Review",
        "keywords": (
            "coordinate",
            "coordination",
            "sync",
            "discussion",
            "discussion",
            "planning",
            "review",
            "check",
        ),
    },
)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def _is_generic_description(text: str) -> bool:
    normalized = _clean_text(text).lower()
    if not normalized:
        return True
    if normalized in {"n/a", "na", "-", "--", "none", "nil"}:
        return True
    return any(phrase in normalized for phrase in GENERIC_DESCRIPTION_PHRASES)


def _normalize_description_entries(entries: list[Any], limit: int | None = None) -> list[str]:
    cleaned: list[str] = []
    seen = set()
    max_items = limit or settings.DESCRIPTION_LOG_LIMIT

    for entry in entries:
        text = _clean_text(entry)
        if not text or _is_generic_description(text):
            continue
        normalized = text.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(text)
        if len(cleaned) >= max_items:
            break

    return cleaned


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_+-]*", text.lower())
    return [word for word in words if len(word) >= 3 and word not in STOPWORDS]


def _fallback_theme_label(entry: str) -> str:
    tokens = [token for token in _tokenize(entry) if token not in ACTION_WORDS]
    if not tokens:
        return "Other Work"
    if len(tokens) == 1:
        return tokens[0].title()
    return f"{tokens[0].title()} {tokens[1].title()}"


def _theme_for_entry(entry: str) -> str:
    lower = entry.lower()
    scored: list[tuple[int, str]] = []

    for rule in THEME_RULES:
        score = 0
        for keyword in rule["keywords"]:
            if keyword in lower:
                score += 2 if " " in keyword else 1
        if score:
            scored.append((score, rule["theme"]))

    if scored:
        scored.sort(key=lambda item: (-item[0], item[1]))
        return scored[0][1]

    return _fallback_theme_label(entry)


def _build_theme_groups(entries: list[str]) -> list[dict[str, Any]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        buckets[_theme_for_entry(entry)].append(entry)

    grouped = []
    for theme, theme_entries in sorted(
        buckets.items(),
        key=lambda item: (-len(item[1]), item[0].lower()),
    ):
        grouped.append(
            {
                "theme": theme,
                "count": len(theme_entries),
                "entries": theme_entries[: settings.DESCRIPTION_LOG_LIMIT],
            }
        )
    return grouped


def _format_theme_intro(theme_groups: list[dict[str, Any]]) -> str:
    top = theme_groups[:4]
    return ", ".join(f"{group['theme']} ({group['count']})" for group in top)


def _build_summary_points(
    theme_groups: list[dict[str, Any]],
    description_entries: list[str],
) -> list[str]:
    if not description_entries:
        return [
            "No description entries were available for this week.",
        ]

    if not theme_groups:
        return description_entries[: settings.DESCRIPTION_BULLET_LIMIT]

    points: list[str] = []
    points.append(f"Main themes this week: {_format_theme_intro(theme_groups)}.")

    for group in theme_groups[: settings.DESCRIPTION_BULLET_LIMIT - 1]:
        examples = group["entries"][:2]
        if examples:
            if len(examples) == 1:
                detail = examples[0]
            else:
                detail = f"{examples[0]}; {examples[1]}"
            points.append(f"{group['theme']}: {detail}.")
        else:
            points.append(f"{group['theme']}: {group['count']} description entries.")

    return points[: settings.DESCRIPTION_BULLET_LIMIT]


def _build_week_summary(theme_groups: list[dict[str, Any]], description_entries: list[str]) -> str:
    if not description_entries:
        return "No description entries were available for this week."

    total = len(description_entries)
    if not theme_groups:
        examples = description_entries[:3]
        return "This week included " + str(total) + " description entries, including " + "; ".join(examples) + "."

    top = theme_groups[:3]
    theme_phrase = ", ".join(f"{group['theme']} ({group['count']})" for group in top)
    total_phrase = f"{total} description entr{'y' if total == 1 else 'ies'}"

    opening = f"This week centered on {theme_phrase}."
    if len(theme_groups) > 3:
        opening += f" Other work themes were captured across {len(theme_groups) - 3} additional groups."

    examples = []
    for group in top:
        if group["entries"]:
            examples.append(group["entries"][0])
    if examples:
        opening += " Key examples include " + "; ".join(examples[:3]) + "."

    opening += f" In total, the workbook captured {total_phrase}."
    return opening


def _build_week_summary_sections(
    theme_groups: list[dict[str, Any]],
    description_entries: list[str],
    peak_day: str | None,
    previous_groups: list[dict[str, Any]] | None,
) -> list[dict[str, str]]:
    if not description_entries:
        return [
            {
                "title": "What Happened",
                "text": "No description entries were available for this week.",
            },
            {
                "title": "Main Focus",
                "text": "There was not enough description detail to identify the main work themes.",
            },
            {
                "title": "Outcome",
                "text": "The summary is based on the workbook structure and any supporting metrics available.",
            },
        ]

    top_groups = theme_groups[:3]
    if top_groups:
        what_happened = "The week included " + ", ".join(
            f"{group['theme']} ({group['count']})" for group in top_groups
        ) + "."
        examples = []
        for group in top_groups:
            if group["entries"]:
                examples.append(group["entries"][0])
        if examples:
            what_happened += " Example entries: " + "; ".join(examples[:3]) + "."
    else:
        what_happened = "The week captured " + str(len(description_entries)) + " description entries."

    if top_groups:
        main_focus = "The work was mainly focused on " + ", ".join(
            group["theme"] for group in top_groups
        ) + "."
    else:
        main_focus = "The work was mainly captured in the Description section."

    if previous_groups:
        current_count = sum(group["count"] for group in theme_groups)
        previous_count = sum(group["count"] for group in previous_groups)
        if previous_count > 0:
            delta = current_count - previous_count
            if delta > 0:
                outcome = f"The week had {delta} more description entries than the previous week."
            elif delta < 0:
                outcome = f"The week had {abs(delta)} fewer description entries than the previous week."
            else:
                outcome = "The amount of logged work was similar to the previous week."
        else:
            outcome = "A previous week comparison was not available."
    else:
        outcome = "No previous week comparison was available."

    if peak_day:
        outcome += f" Peak activity landed on {peak_day}."

    return [
        {"title": "What Happened", "text": what_happened},
        {"title": "Main Focus", "text": main_focus},
        {"title": "Outcome", "text": outcome},
    ]


def _build_trend_statement(
    current_groups: list[dict[str, Any]],
    previous_groups: list[dict[str, Any]] | None,
) -> str:
    if not previous_groups:
        return "No previous week data available."

    current_count = sum(group["count"] for group in current_groups)
    previous_count = sum(group["count"] for group in previous_groups)

    if previous_count == 0:
        return "No previous week data available."

    delta = current_count - previous_count
    if delta == 0:
        prefix = "The number of description entries was unchanged versus last week."
    elif delta > 0:
        prefix = f"This week had {delta} more description entries than last week."
    else:
        prefix = f"This week had {abs(delta)} fewer description entries than last week."

    current_top = [group["theme"] for group in current_groups[:3]]
    previous_top = [group["theme"] for group in previous_groups[:3]]
    shared = [theme for theme in current_top if theme in previous_top]
    new_focus = [theme for theme in current_top if theme not in previous_top]

    if new_focus:
        return f"{prefix} New focus areas included {', '.join(new_focus)}."
    if shared:
        return f"{prefix} The biggest recurring themes were {', '.join(shared)}."
    return prefix


def generate_weekly_summary(
    current_week: dict[str, Any],
    previous_week: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a description-first weekly summary with grouped themes and raw log.
    """
    description_entries = _normalize_description_entries(
        current_week.get("description_entries", []),
    )
    previous_entries = _normalize_description_entries(
        previous_week.get("description_entries", []) if previous_week else [],
    )

    theme_groups = _build_theme_groups(description_entries)
    previous_theme_groups = _build_theme_groups(previous_entries) if previous_entries else []

    week_summary = _build_week_summary(theme_groups, description_entries)
    week_summary_sections = _build_week_summary_sections(
        theme_groups,
        description_entries,
        current_week.get("peak_day"),
        previous_theme_groups,
    )
    summary_points = _build_summary_points(theme_groups, description_entries)
    trend = _build_trend_statement(theme_groups, previous_theme_groups)
    peak_day = current_week.get("peak_day")

    summary = " ".join(summary_points[: settings.DESCRIPTION_BULLET_LIMIT])

    return {
        "summary_points": summary_points,
        "summary": summary,
        "week_summary": week_summary,
        "week_summary_sections": week_summary_sections,
        "peak_day": peak_day,
        "trend_vs_previous_week": trend,
        "theme_groups": theme_groups,
    }
