import datetime as dt
import json
import pytest

from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.api import get_data_storage
from app.file_storage import FileStorage
from app.main import app
from app.project_types import WeightEntry


@pytest.fixture
def sample_daily_entries():
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


@pytest.fixture
def get_test_storage(mocker, sample_daily_entries, tmp_path):
    test_file_path = tmp_path / "test_storage.json"

    sample_data: list[WeightEntry] = TypeAdapter(list[WeightEntry]).validate_python(
        sample_daily_entries
    )
    serialized_data = TypeAdapter(list[WeightEntry]).dump_json(sample_data)

    test_file_path.write_bytes(serialized_data)
    mocker.patch(
        "app.file_storage.FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH", test_file_path
    )
    return FileStorage()


@pytest.fixture
def client_with_storage(get_test_storage):
    app.dependency_overrides[get_data_storage] = lambda: get_test_storage
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


def test_get_daily_entries(client_with_storage):
    response = client_with_storage.get(
        "/api/daily-entries",
        params={"date_from": "2025-08-20", "date_to": "2025-09-01"},
    )

    expected = [
        {"date": "2025-08-20", "weight": 72.3},
        {"date": "2025-08-21", "weight": 72.7},
        {"date": "2025-08-22", "weight": 72.5},
        {"date": "2025-08-25", "weight": 73.0},
        {"date": "2025-08-26", "weight": 73.6},
        {"date": "2025-08-27", "weight": 73.0},
        {"date": "2025-08-28", "weight": 73.6},
        {"date": "2025-08-29", "weight": 73.6},
        {"date": "2025-08-30", "weight": 73.5},
        {"date": "2025-09-01", "weight": 73.0},
    ]

    assert response.status_code == 200
    assert response.json() == expected


def test_get_weekly_entries_daily_filters(client_with_storage):
    response = client_with_storage.get(
        "/api/weekly-aggregates",
        params={"date_from": "2025-08-20", "date_to": "2025-09-01", "goal": "lose"},
    )

    expected = {
        "weekly_data": [
            {
                "week_start": "2025-09-01",
                "avg_weight": 73.0,
                "weight_change": -0.38,
                "weight_change_prc": -0.52,
                "net_calories": -422,
                "result": "positive",
            },
            {
                "week_start": "2025-08-25",
                "avg_weight": 73.38,
                "weight_change": 0.88,
                "weight_change_prc": 1.21,
                "net_calories": 978,
                "result": "negative",
            },
            {
                "week_start": "2025-08-18",
                "avg_weight": 72.5,
                "weight_change": 0.0,
                "weight_change_prc": 0.0,
                "net_calories": 0,
                "result": None,
            },
        ],
        "goal": "lose",
    }

    assert response.status_code == 200
    assert response.json() == expected


def test_get_weekly_entries_weekly_filter(client_with_storage):
    response = client_with_storage.get(
        "/api/weekly-aggregates",
        params={"weeks_limit": "1", "goal": "gain"},
    )

    expected = {
        "weekly_data": [
            {
                "week_start": "2025-09-01",
                "avg_weight": 72.5,
                "weight_change": -0.88,
                "weight_change_prc": -1.2,
                "net_calories": -978,
                "result": "negative",
            },
            {
                "week_start": "2025-08-25",
                "avg_weight": 73.38,
                "weight_change": 0.0,
                "weight_change_prc": 0.0,
                "net_calories": 0,
                "result": None,
            },
        ],
        "goal": "gain",
    }

    assert response.status_code == 200
    assert response.json() == expected


def test_summary_daily_filter(client_with_storage):
    response = client_with_storage.get(
        "api/summary", params={"date_from": "2025-08-20", "date_to": "2025-09-01"}
    )

    expected = {
        "metrics": {
            "total_change": 0.5,
            "avg_change": 0.25,
            "avg_change_prc": 0.34,
            "avg_net_calories": 278,
        }
    }

    assert response.status_code == 200
    assert response.json() == expected


def test_summary_weekly_filter(client_with_storage):
    response = client_with_storage.get("api/summary", params={"weeks_limit": "1"})

    expected = {
        "metrics": {
            "total_change": -0.88,
            "avg_change": -0.88,
            "avg_change_prc": -1.2,
            "avg_net_calories": -978,
        }
    }

    assert response.status_code == 200
    assert response.json() == expected


def test_latest_entry(client_with_storage):
    response = client_with_storage.get("api/latest-entry")

    assert response.status_code == 200
    assert response.json() == {"date": "2025-09-03", "weight": 72.5}
