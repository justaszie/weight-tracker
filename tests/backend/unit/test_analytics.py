# type: ignore
import datetime as dt
import pytest
from pydantic import TypeAdapter
from typing import Any
from uuid import UUID

from app.analytics import (
    get_weekly_aggregates,
    get_summary,
    calculate_result,
)
from app.project_types import (
    WeightEntry,
    WeeklyAggregateEntry,
    ProgressMetrics,
    ProgressSummary,
)

TEST_USER_ID = UUID("3760183f-61fa-4ee1-badf-2668fbec152d")


@pytest.fixture
def sample_daily_entries() -> Any:
    data = [
        {"entry_date": dt.date(2025, 8, 18), "weight": 73.0, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 19), "weight": 72.9, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 20), "weight": 72.3, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 21), "weight": 72.7, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 22), "weight": 72.5, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 25), "weight": 73.0, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 26), "weight": 73.6, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 27), "weight": 73.0, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 28), "weight": 73.6, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 29), "weight": 73.6, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 30), "weight": 73.5, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 9, 1), "weight": 73, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 9, 2), "weight": 72, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 9, 3), "weight": 72.5, "user_id": TEST_USER_ID},
    ]
    return TypeAdapter(list[WeightEntry]).validate_python(data)


def test_weekly_aggregates(sample_daily_entries):
    goal = "lose"
    expected = TypeAdapter(list[WeeklyAggregateEntry]).validate_python(
        [
            {
                "week_start": dt.date(2025, 8, 18),
                "avg_weight": 72.68,
                "weight_change": 0.0,
                "weight_change_prc": 0.0,
                "net_calories": 0,
                "result": "negative",
            },
            {
                "week_start": dt.date(2025, 8, 25),
                "avg_weight": 73.38,
                "weight_change": 0.7,
                "weight_change_prc": 0.96,
                "net_calories": 778,
                "result": "negative",
            },
            {
                "week_start": dt.date(2025, 9, 1),
                "avg_weight": 72.50,
                "weight_change": -0.88,
                "weight_change_prc": -1.2,
                "net_calories": -978,
                "result": "positive",
            },
        ]
    )
    weekly_aggregates = get_weekly_aggregates(sample_daily_entries, goal)
    assert weekly_aggregates == expected


def test_weekly_aggregates_empty_dataset():
    entries = get_weekly_aggregates([], "lose")
    assert len(entries) == 0


def test_weekly_aggregates_single_week():
    daily_entries = TypeAdapter(list[WeightEntry]).validate_python(
        [
            {
                "entry_date": dt.date(2025, 8, 25),
                "weight": 73.0,
                "user_id": TEST_USER_ID,
            },
            {
                "entry_date": dt.date(2025, 8, 26),
                "weight": 73.6,
                "user_id": TEST_USER_ID,
            },
            {
                "entry_date": dt.date(2025, 8, 27),
                "weight": 73.0,
                "user_id": TEST_USER_ID,
            },
            {
                "entry_date": dt.date(2025, 8, 28),
                "weight": 73.6,
                "user_id": TEST_USER_ID,
            },
            {
                "entry_date": dt.date(2025, 8, 29),
                "weight": 73.6,
                "user_id": TEST_USER_ID,
            },
            {
                "entry_date": dt.date(2025, 8, 30),
                "weight": 73.5,
                "user_id": TEST_USER_ID,
            },
            {
                "entry_date": dt.date(2025, 8, 31),
                "weight": 72.5,
                "user_id": TEST_USER_ID,
            },
        ]
    )
    expected = TypeAdapter(list[WeeklyAggregateEntry]).validate_python(
        [
            {
                "week_start": dt.date(2025, 8, 25),
                "avg_weight": 73.26,
                "weight_change": 0.0,
                "weight_change_prc": 0.0,
                "net_calories": 0,
                "result": "negative",
            }
        ]
    )
    goal = "gain"
    assert get_weekly_aggregates(daily_entries=daily_entries, goal=goal) == expected


def test_weekly_aggregates_single_day():
    daily_entries = TypeAdapter(list[WeightEntry]).validate_python(
        [{"entry_date": dt.date(2025, 8, 27), "weight": 72.18, "user_id": TEST_USER_ID}]
    )
    expected = TypeAdapter(list[WeeklyAggregateEntry]).validate_python(
        [
            {
                "week_start": dt.date(2025, 8, 25),
                "avg_weight": 72.18,
                "weight_change": 0.0,
                "weight_change_prc": 0.0,
                "net_calories": 0,
                "result": "negative",
            }
        ]
    )
    goal = "lose"
    assert get_weekly_aggregates(daily_entries=daily_entries, goal=goal) == expected


@pytest.mark.parametrize(
    "weight_change, goal, expected_result",
    [
        (0.25, "lose", "negative"),
        (0, "lose", "negative"),
        (-0.01, "lose", "positive"),
        (-1.5, "lose", "positive"),
        (-0.01, "gain", "negative"),
        (-1.31, "gain", "negative"),
        (2.5, "gain", "positive"),
        (0.0, "gain", "negative"),
        (0.3, "gain", "positive"),
    ],
)
def test_calculate_result(weight_change, goal, expected_result):
    assert calculate_result(weight_change, goal) == expected_result


@pytest.mark.parametrize(
    "maintain_positive_range, weight_change, expected_result",
    [
        (0.25, 0.3, "negative"),
        (0.25, 0.2, "positive"),
        (0.25, 0.25, "positive"),
        (0.25, -0.1, "positive"),
        (0.25, -0.2, "positive"),
        (0.25, -0.3, "negative"),
        (0.25, -0.23, "positive"),
        (0.25, -1.5, "negative"),
    ],
)
def test_calculate_maintain_result(
    mocker, maintain_positive_range, weight_change, expected_result
):
    mocker.patch("app.analytics.MAINTAIN_ACCEPTABLE_CHANGE", maintain_positive_range)
    assert (
        calculate_result(weight_change=weight_change, goal="maintain")
        == expected_result
    )


def test_calculate_result_invalid_goal():
    assert calculate_result(weight_change=1.2, goal="bulk") == None
    assert calculate_result(weight_change=1.2, goal="stabiliZe") == None


def test_get_summary():
    weekly_entries = TypeAdapter(list[WeeklyAggregateEntry]).validate_python(
        [
            {
                "week_start": dt.date(2025, 8, 18),
                "avg_weight": 72.68,
                "weight_change": 0.0,
                "weight_change_prc": 0.0,
                "net_calories": 0,
                "result": "negative",
            },
            {
                "week_start": dt.date(2025, 8, 25),
                "avg_weight": 73.88,
                "weight_change": 1.2,
                "weight_change_prc": 1.65,
                "net_calories": 1333,
                "result": "negative",
            },
            {
                "week_start": dt.date(2025, 9, 1),
                "avg_weight": 72.50,
                "weight_change": -1.38,
                "weight_change_prc": -1.87,
                "net_calories": -2078,
                "result": "positive",
            },
        ]
    )
    expected = ProgressMetrics.model_validate(
        {
            "total_change": -0.18,
            "avg_change": -0.09,
            "avg_change_prc": -0.11,
            "avg_net_calories": -372,
        }
    )
    assert get_summary(weekly_entries=weekly_entries) == expected


def test_get_summary_empty_dataset():
    assert get_summary([]) == None


def test_get_summary_single_week():
    weekly_entries = TypeAdapter(list[WeeklyAggregateEntry]).validate_python(
        [
            {
                "week_start": dt.date(2025, 9, 1),
                "avg_weight": 72.50,
                "weight_change": -1.38,
                "weight_change_prc": -1.87,
                "net_calories": -2078,
                "result": "positive",
            },
            {
                "week_start": dt.date(2025, 8, 18),
                "avg_weight": 72.68,
                "weight_change": 0.0,
                "weight_change_prc": 0.0,
                "net_calories": 0,
                "result": "negative",
            },
        ]
    )
    expected = ProgressMetrics.model_validate(
        {
            "total_change": -1.38,
            "avg_change": -1.38,
            "avg_change_prc": -1.87,
            "avg_net_calories": -2078,
        }
    )
    assert get_summary(weekly_entries=weekly_entries) == expected
