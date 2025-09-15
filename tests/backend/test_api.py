import datetime as dt
import pytest

from app.api import (
    get_filtered_daily_entries,
    get_filtered_weekly_entries,
)

@pytest.fixture
def sample_daily_entries():
    return [
        {"date": dt.date(2024, 10, 2), "weight": 73.81},
        {"date": dt.date(2025, 1, 12), "weight": 72},
        {"date": dt.date(2025, 8, 28), "weight": 71.12},
        {"date": dt.date(2025, 8, 30), "weight": 73.5},
        {"date": dt.date(2025, 9, 2), "weight": 72},
    ]


@pytest.fixture
def sample_daily_entries_extended():
    return [
        {"date": dt.date(2025, 8, 18), "weight": 73.0},
        {"date": dt.date(2025, 8, 19), "weight": 72.9},
        {"date": dt.date(2025, 8, 20), "weight": 72.3},
        {"date": dt.date(2025, 8, 21), "weight": 72.7},
        {"date": dt.date(2025, 8, 22), "weight": 72.5},
        {"date": dt.date(2025, 8, 25), "weight": 73.0},
        {"date": dt.date(2025, 8, 26), "weight": 73.6},
        {"date": dt.date(2025, 8, 27), "weight": 73.0},
        {"date": dt.date(2025, 8, 28), "weight": 73.6},
        {"date": dt.date(2025, 8, 29), "weight": 73.6},
        {"date": dt.date(2025, 8, 30), "weight": 73.5},
        {"date": dt.date(2025, 9, 1), "weight": 73},
        {"date": dt.date(2025, 9, 2), "weight": 72},
        {"date": dt.date(2025, 9, 3), "weight": 72.5},
    ]


# @pytest.fixture
# def sample_weekly_entries():
#     return [
#         ""
#     ]


@pytest.mark.parametrize(
    "date_from_param, date_to_param, expected_entries",
    [
        (
            "2025-08-28",
            None,
            [
                {"date": dt.date(2025, 8, 28), "weight": 71.12},
                {"date": dt.date(2025, 8, 30), "weight": 73.5},
                {"date": dt.date(2025, 9, 2), "weight": 72},
            ],
        ),
        (
            "",
            "2025-02-01",
            [
                {"date": dt.date(2024, 10, 2), "weight": 73.81},
                {"date": dt.date(2025, 1, 12), "weight": 72},
            ],
        ),
        (
            "2025-05-01",
            "2025-09-01",
            [
                {"date": dt.date(2025, 8, 28), "weight": 71.12},
                {"date": dt.date(2025, 8, 30), "weight": 73.5},
            ],
        ),
        (
            None,
            "",
            [
                {"date": dt.date(2024, 10, 2), "weight": 73.81},
                {"date": dt.date(2025, 1, 12), "weight": 72},
                {"date": dt.date(2025, 8, 28), "weight": 71.12},
                {"date": dt.date(2025, 8, 30), "weight": 73.5},
                {"date": dt.date(2025, 9, 2), "weight": 72},
            ],
        ),
        (
            "2024-01-10",
            "2024-10-01",
            [],
        ),
        (
            "2024-10-02",
            "2024-10-02",
            [
                {"date": dt.date(2024, 10, 2), "weight": 73.81},
            ],
        ),
    ],
)
def test_get_filtered_daily_entries(
    mocker, sample_daily_entries, date_from_param, date_to_param, expected_entries
) -> None:
    mocker.patch("app.api.FileStorage").return_value.get_weight_entries.return_value = (
        sample_daily_entries
    )

    daily_entries = get_filtered_daily_entries(date_from_param, date_to_param)

    assert daily_entries == expected_entries


@pytest.mark.parametrize(
    "date_from_param, date_to_param, expected_exception",
    [
        ("2024-12-40", "2025-10-10", InvalidDateError),
        ("2024-12-01", "2025911111", InvalidDateError),
        (2024010, "2025-01-01", InvalidDateError),
        ("2025-12-01", "2023-01-01", DateRangeError),
        ("2025-12-01", "2025-11-30", DateRangeError),
    ],
)
def test_get_filtered_daily_entries_invalid_params(
    date_from_param, date_to_param, expected_exception
):
    with pytest.raises(expected_exception):
        get_filtered_daily_entries(date_from_param, date_to_param)


@pytest.mark.parametrize(
    "weeks_limit_param, expected_entries",
    [
        (
            None,
            [
                {
                    "week_start": dt.date(2025, 9, 1),
                    "avg_weight": 72.50,
                    "weight_change": -0.88,
                    "weight_change_prc": -1.2,
                    "net_calories": -978,
                    "result": "positive",
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
                    "week_start": dt.date(2025, 8, 18),
                    "avg_weight": 72.68,
                    "weight_change": 0.0,
                    "weight_change_prc": 0.0,
                    "net_calories": 0,
                    "result": None,
                },
            ],
        ),
        (
            "1",
            [
                {
                    "week_start": dt.date(2025, 9, 1),
                    "avg_weight": 72.50,
                    "weight_change": -0.88,
                    "weight_change_prc": -1.2,
                    "net_calories": -978,
                    "result": "positive",
                },
                {
                    "week_start": dt.date(2025, 8, 25),
                    "avg_weight": 73.38,
                    "weight_change": 0.00,
                    "weight_change_prc": 0.00,
                    "net_calories": 0,
                    "result": None,
                },
            ],
        ),
        (
            "2",
            [
                {
                    "week_start": dt.date(2025, 9, 1),
                    "avg_weight": 72.50,
                    "weight_change": -0.88,
                    "weight_change_prc": -1.2,
                    "net_calories": -978,
                    "result": "positive",
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
                    "week_start": dt.date(2025, 8, 18),
                    "avg_weight": 72.68,
                    "weight_change": 0.0,
                    "weight_change_prc": 0.0,
                    "net_calories": 0,
                    "result": None,
                },
            ],
        ),
    ],
)
def test_get_filtered_weekly_entries(
    mocker, weeks_limit_param, sample_daily_entries_extended, expected_entries
):
    assert (
        get_filtered_weekly_entries(
            sample_daily_entries_extended, "lose", weeks_limit_param
        )
        == expected_entries
    )


@pytest.mark.parametrize("weeks_limit_param", ["-1", "0", "-20"])
def test_get_filtered_weekly_entries_invalid_filter(
    weeks_limit_param, sample_daily_entries
):
    with pytest.raises(InvalidWeeksLimit):
        get_filtered_weekly_entries(sample_daily_entries, "lose", weeks_limit_param)


def test_get_filtered_weekly_entries_empty_dataset():
    daily_entries = []
    assert get_filtered_weekly_entries(daily_entries, "lose", "2") == []
