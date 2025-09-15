# type: ignore

import datetime as dt

import pytest

from project_types import DailyWeightEntry
from utils import (
    # to_signed_amt_str,
    filter_daily_entries,
    get_latest_daily_entry,
    get_latest_entry_date,
    is_valid_weeks_filter,
    is_valid_goal_selection,
    is_valid_data_source,
    parse_iso_date,
    validate_date_range,
    DateRangeError,
    InvalidDateError,
    parse_date_filters,
)


class TestDailyEntriesManipulation:
    @pytest.fixture
    def sample_daily_entries(self) -> list[DailyWeightEntry]:
        return [
            {"date": dt.date(2025, 8, 30), "weight": 72.5},
            {"date": dt.date(2025, 8, 29), "weight": 73.5},
            {"date": dt.date(2025, 8, 25), "weight": 74.5},
            {"date": dt.date(2025, 5, 29), "weight": 72.3},
            {"date": dt.date(2025, 5, 27), "weight": 71.5},
        ]

    @pytest.mark.parametrize(
        "daily_entries, date_from, date_to, expected_count",
        [
            ([], None, None, 0),
            ([], dt.date.fromisoformat("2025-08-30"), None, 0),
            ([], None, dt.date.fromisoformat("2025-08-30"), 0),
        ],
    )
    def test_filter_empty_daily_entries(
        self, daily_entries, date_from, date_to, expected_count
    ):
        filtered: list[DailyWeightEntry] = filter_daily_entries(
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
        filtered: list[DailyWeightEntry] = filter_daily_entries(
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
        ],  # type: ignore
    )
    def test_get_latest_date(self, entries, expected_value):
        result = get_latest_entry_date(entries)
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
        ],  # type: ignore
    )
    def test_get_latest_daily_entry(self, entries, expected_value):
        result = get_latest_daily_entry(entries)
        assert result == expected_value


@pytest.mark.parametrize(
    "value, outcome",
    [
        ("5", True),
        (5, True),
        (5.0, True),
        (0, False),
        ("-3", False),
        (-2, False),
        (-2.5, False),
        (None, False),
        ("abcd", False),
    ],
)
def test_weeks_limit_validation(value, outcome):
    assert is_valid_weeks_filter(value) == outcome


@pytest.mark.parametrize(
    "goal, outcome",
    [
        ("gain", True),
        ("GaIn", True),
        ("lose", True),
        ("LOSE", True),
        ("maintain", True),
        ("maintain weight", False),
        ("None", False),
        ("bulk", False),
        ("2.5", False),
    ],
)
def test_goal_validation(goal, outcome):
    assert is_valid_goal_selection(goal) == outcome


@pytest.mark.parametrize(
    "source, outcome",
    [
        ("GFIT", True),
        ("gfit", True),
        ("MFp", True),
        ("mfp", True),
        ("Myfitnesspal", False),
        ("Apple Fit", False),
        (None, False),
        (3, False),
    ],
)
def test_data_source_validation(source, outcome):
    assert is_valid_data_source(source) == outcome


@pytest.mark.parametrize(
    "date_str, output",
    [
        ("2025-06-10", dt.date(2025, 6, 10)),
        (None, None),
        ("", None),
    ],
)
def test_parsing_iso_date(date_str, output):
    assert parse_iso_date(date_str=date_str) == output


def test_parsing_invalid_iso_date_str():
    with pytest.raises(ValueError):
        parse_iso_date("abc/22")
    with pytest.raises(ValueError):
        parse_iso_date(20251011)


@pytest.mark.parametrize(
    "date_from, date_to",
    [
        (None, None),
        (dt.date(2025, 5, 1), None),
        (None, dt.date(2024, 1, 1)),
        (dt.date(2023, 11, 24), dt.date(2024, 1, 1)),
        (dt.date(2023, 11, 24), dt.date(2023, 11, 24)),
    ],
)
def test_valid_date_range_validation(date_from, date_to):
    assert validate_date_range(date_from, date_to) == None


def test_invaid_date_range_validation():
    with pytest.raises(DateRangeError):
        validate_date_range(date_from=dt.date(2025, 5, 2), date_to=dt.date(2025, 5, 1))

@pytest.mark.parametrize(
        "date_from, date_to, result",
        [
            (None, None, (None, None)),
            ("2025-02-20", None, (dt.date(2025,2,20), None)),
            (None, "2025-02-20", (None, dt.date(2025,2,20))),
            ("2025-02-20", "2025-02-22", (dt.date(2025,2,20), dt.date(2025,2,22))),
        ]
)
def test_valid_dates_parse_date_filters(date_from, date_to, result):
    assert parse_date_filters(date_from=date_from, date_to=date_to) == result

@pytest.mark.parametrize(
        "date_from, date_to, expected_exception",
        [
            ("2025-02-32", None, InvalidDateError),
            (20251123, "2001-01-01", InvalidDateError),
            ("2001-01-01", 20251123, InvalidDateError),
            ("2001-01-01", "abcd", InvalidDateError),
            ("2001-01-01", "1991-02-10", DateRangeError),
        ]
)
def test_invalid_dates_parse_date_filters(date_from, date_to, expected_exception):
    with pytest.raises(expected_exception):
        parse_date_filters(date_from=date_from, date_to=date_to)
