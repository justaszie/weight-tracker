# type: ignore

import datetime as dt

import pytest
from pydantic import TypeAdapter

from app.project_types import WeightEntry
from app.utils import (
    filter_daily_entries,
    get_latest_daily_entry,
    get_latest_entry_date,
)

class TestDailyEntriesManipulation:
    @pytest.fixture
    def sample_daily_entries(self) -> list[WeightEntry]:
        data = [
            {"date": dt.date(2025, 8, 30), "weight": 72.5},
            {"date": dt.date(2025, 8, 29), "weight": 73.5},
            {"date": dt.date(2025, 8, 25), "weight": 74.5},
            {"date": dt.date(2025, 5, 29), "weight": 72.3},
            {"date": dt.date(2025, 5, 27), "weight": 71.5},
        ]
        return TypeAdapter(list[WeightEntry]).validate_python(data)

    @pytest.mark.parametrize(
        "daily_entries, date_from, date_to, expected_count",
        [
            ([], None, None, 0),
            ([], dt.date(2025,8,30), None, 0),
            ([], None, dt.date(2025,8,30), 0),
        ],
    )
    def test_filter_empty_daily_entries(
        self, daily_entries, date_from, date_to, expected_count
    ):
        filtered: list[WeightEntry] = filter_daily_entries(
            daily_entries=daily_entries, date_from=date_from, date_to=date_to
        )
        assert len(filtered) == expected_count

    @pytest.mark.parametrize(
        "date_from, date_to, expected_count",
        [
            (dt.date(2025, 8, 1), dt.date(2025, 9, 1), 3),
            (dt.date(2025, 5, 28), dt.date(2025, 9, 1), 4),
            (dt.date(2025, 5, 28), None, 4),
            (None, dt.date(2025, 6, 1), 2),
            (None, None, 5),
            (dt.date(2025, 5, 28), dt.date(2025, 1, 1), 0),
        ],
    )
    def test_filter_sample_daily_entries(
        self, sample_daily_entries, date_from, date_to, expected_count
    ):
        filtered: list[WeightEntry] = filter_daily_entries(
            daily_entries=sample_daily_entries, date_from=date_from, date_to=date_to
        )
        assert len(filtered) == expected_count

    @pytest.mark.parametrize(
        "entries, expected_value",
        [
            ([], None),
            ([{"date": dt.date(2025, 5, 20), "weight": 72.5}], dt.date(2025, 5, 20)),
            (
                [
                    {"date": dt.date(2024, 5, 20), "weight": 72.5},
                    {"date": dt.date(2025, 1, 15), "weight": 72.5},
                ],
                dt.date(2025, 1, 15),
            ),
        ],
    )
    def test_get_latest_date(self, entries, expected_value):
        daily_entries = TypeAdapter(list[WeightEntry]).validate_python(entries)
        result = get_latest_entry_date(daily_entries)
        assert result == expected_value

    @pytest.mark.parametrize(
        "entries, expected_value",
        [
            ([], None),
            (
                [{"date": dt.date(2025, 5, 20), "weight": 72.5}],
                {"date": dt.date(2025, 5, 20), "weight": 72.5},
            ),
            (
                [
                    {"date": dt.date(2024, 5, 20), "weight": 75.5},
                    {"date": dt.date(2025, 1, 15), "weight": 71.5},
                ],
                {"date": dt.date(2025, 1, 15), "weight": 71.5},
            ),
        ],
    )
    def test_get_latest_daily_entry(self, entries, expected_value):
        daily_entries = TypeAdapter(list[WeightEntry]).validate_python(entries)
        result = get_latest_daily_entry(daily_entries)
        expected_latest_entry = WeightEntry.model_validate(expected_value) if expected_value else None
        assert result == expected_latest_entry
