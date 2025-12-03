import datetime as dt
import os
from uuid import UUID

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from pydantic import TypeAdapter
from sqlmodel import create_engine, SQLModel, Session

from app.analytics import (
    get_weekly_aggregates,
    get_summary,
)
from app.api import get_current_user
from app.db_storage import DatabaseStorage, DBWeightEntry
from app.demo import DemoDataSourceClient
from app.project_types import (
    WeightEntry,
    WeeklyAggregateEntry,
)

# Integration tests when running with demo user id

load_dotenv()


DEMO_USER_ID = UUID(os.environ.get("DEMO_USER_ID"))
TEST_DB_CONN_STRING = (
    "postgresql+psycopg2://postgres@localhost:5432/test_weight_tracker"
)


@pytest.fixture
def sample_daily_entries():
    raw_entries = [
        {"entry_date": dt.date(2025, 4, 7), "weight": 71.5, "user_id": DEMO_USER_ID},
        {"entry_date": dt.date(2025, 4, 8), "weight": 70.7, "user_id": DEMO_USER_ID},
        {"entry_date": dt.date(2025, 4, 9), "weight": 70.7, "user_id": DEMO_USER_ID},
        {"entry_date": dt.date(2025, 4, 10), "weight": 70.0, "user_id": DEMO_USER_ID},
        {"entry_date": dt.date(2025, 4, 11), "weight": 70.4, "user_id": DEMO_USER_ID},
        {"entry_date": dt.date(2025, 4, 12), "weight": 70.2, "user_id": DEMO_USER_ID},
        {"entry_date": dt.date(2025, 4, 13), "weight": 70.5, "user_id": DEMO_USER_ID},
        {"entry_date": dt.date(2025, 4, 14), "weight": 70.7, "user_id": DEMO_USER_ID},
        {"entry_date": dt.date(2025, 4, 15), "weight": 70.5, "user_id": DEMO_USER_ID},
        {"entry_date": dt.date(2025, 4, 16), "weight": 70.3, "user_id": DEMO_USER_ID},
        {"entry_date": dt.date(2025, 4, 17), "weight": 70.2, "user_id": DEMO_USER_ID},
        {"entry_date": dt.date(2025, 4, 18), "weight": 69.9, "user_id": DEMO_USER_ID},
        {"entry_date": dt.date(2025, 4, 23), "weight": 70.12, "user_id": DEMO_USER_ID},
    ]
    return TypeAdapter(list[WeightEntry]).validate_python(raw_entries)


@pytest.fixture(autouse=True)
def setup_env_variables(monkeypatch):
    # For the tests we use the database storage
    # even the real app is using other storage system
    monkeypatch.setenv("STORAGE_TYPE", "database")
    monkeypatch.setenv("DB_CONNECTION_STRING", TEST_DB_CONN_STRING)


@pytest.fixture
def storage_empty():
    engine = create_engine(TEST_DB_CONN_STRING)
    SQLModel.metadata.create_all(engine)
    try:
        yield DatabaseStorage()
    finally:
        SQLModel.metadata.drop_all(engine)


@pytest.fixture
def storage_sample(sample_daily_entries):
    engine = create_engine(TEST_DB_CONN_STRING)
    SQLModel.metadata.create_all(engine)
    try:
        _insert_daily_entries(engine, sample_daily_entries)
        yield DatabaseStorage()
    finally:
        SQLModel.metadata.drop_all(engine)


def _insert_daily_entries(engine, daily_entries):
    entries_as_sqlmodels = [
        DBWeightEntry.model_validate(entry, from_attributes=True)
        for entry in daily_entries
    ]
    with Session(engine) as test_session:
        test_session.add_all(entries_as_sqlmodels)
        test_session.commit()


@pytest.fixture
def client_empty_storage(storage_empty):
    from app.main import create_app

    app = create_app()
    with TestClient(app) as client:
        app.dependency_overrides[get_current_user] = lambda: DEMO_USER_ID
        yield client
        app.dependency_overrides.clear()


@pytest.fixture
def client_sample_storage(storage_sample):
    from app.main import create_app

    app = create_app()
    with TestClient(app) as client:
        app.dependency_overrides[get_current_user] = lambda: DEMO_USER_ID
        yield client
        app.dependency_overrides.clear()


class TestDemoGetData:
    # Goal: testing that the API endpoints will work as expected
    # when the logged in user is DEMO_USER_ID
    def test_get_latest_entry(self, client_sample_storage, sample_daily_entries):
        response = client_sample_storage.get("/api/v1/latest-entry")
        expected_last_entry = sorted(
            sample_daily_entries, key=lambda entry: entry.entry_date
        )[-1]

        assert response.status_code == 200
        assert response.json() == expected_last_entry.model_dump(mode="json")

    def test_get_daily_entries(self, client_sample_storage, sample_daily_entries):
        response = client_sample_storage.get("/api/v1/daily-entries")

        expected = TypeAdapter(list[WeightEntry]).validate_python(sample_daily_entries)
        expected_json = TypeAdapter(list[WeightEntry]).dump_python(
            expected, mode="json"
        )

        assert response.status_code == 200
        assert response.json() == expected_json

    def test_get_weekly_aggregates(self, client_sample_storage, sample_daily_entries):
        # Given: demo storage daily entries, weeks_limit param, and goal param
        # Expected: one entry for each week, sorted from the latest, with one additional reference week
        response = client_sample_storage.get(
            "/api/v1/weekly-aggregates",
            params={
                "weeks_limit": "1",
                "goal": "lose",
            },
        )

        analytics_data = get_weekly_aggregates(sample_daily_entries, goal="lose")
        analytics_data.sort(key=lambda entry: entry.week_start, reverse=True)

        weekly_data = analytics_data[:2]
        weekly_data[-1] = weekly_data[-1].model_copy(
            update={
                "weight_change": 0.0,
                "weight_change_prc": 0.0,
                "net_calories": 0,
                "result": None,
            }
        )
        expected_json = {
            "goal": "lose",
            "weekly_data": TypeAdapter(list[WeeklyAggregateEntry]).dump_python(
                weekly_data, mode="json"
            ),
        }

        assert response.status_code == 200
        assert response.json() == expected_json

    def test_get_summary(self, client_sample_storage, sample_daily_entries):
        # Given: demo storage daily entries, weeks_limit param
        # Expected: a JSON response with a property "metrics" which contains
        # the metrics calculated over N weeks using analytics module

        response = client_sample_storage.get(
            "/api/v1/summary",
            params={
                "weeks_limit": "2",
            },
        )

        analytics_data = get_weekly_aggregates(sample_daily_entries, goal="lose")
        analytics_data.sort(key=lambda entry: entry.week_start, reverse=True)

        weekly_data = analytics_data[:3]
        weekly_data[-1] = weekly_data[-1].model_copy(
            update={
                "weight_change": 0.0,
                "weight_change_prc": 0.0,
                "net_calories": 0,
                "result": None,
            }
        )

        metrics_data = get_summary(weekly_data)
        latest_week = sorted(
            weekly_data, key=lambda week: week.week_start, reverse=True
        )[0]

        expected_json = {
            "latest_week": latest_week.model_dump(mode="json"),
            "metrics": metrics_data.model_dump(mode="json"),
        }

        assert response.status_code == 200
        assert response.json() == expected_json


class TestDemoSyncData:
    def test_sync_data_new_entries(self, client_sample_storage, sample_daily_entries):
        """
        GIVEN:
            - sample_daily_entries
            - Converted daily entries from DemoDataSourceClient (hardcoded + current date's data)
        EXPECTED:
            - /sync-data returns success with the number of new entries
            - new entries are available when /daily-entries is called
            - existing entries in DatabaseStorage were not changed
        """
        existing_entries = {
            (entry.user_id, entry.entry_date) for entry in sample_daily_entries
        }
        data_source_entries = DemoDataSourceClient(
            DEMO_USER_ID
        ).convert_to_daily_entries(None)

        new_entries = [
            entry
            for entry in data_source_entries
            if (entry.user_id, entry.entry_date) not in existing_entries
        ]

        expected_delta_count = len(new_entries)
        expected_new_entry = new_entries[-1]

        expected_unchanged_entry = sample_daily_entries[0]

        response = client_sample_storage.post(
            "/api/v1/sync-data", json={"data_source": "gfit"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "sync_success"
        assert response.json()["new_entries_count"] == expected_delta_count

        response = client_sample_storage.get("/api/v1/daily-entries")

        assert response.status_code == 200
        assert len(response.json()) == len(existing_entries) + expected_delta_count

        response = client_sample_storage.get(
            "/api/v1/daily-entries",
            params={
                "date_from": expected_new_entry.entry_date.isoformat(),
                "date_to": expected_new_entry.entry_date.isoformat(),
            },
        )
        returned_new_entry = response.json()[0]
        assert response.status_code == 200
        assert (
            returned_new_entry["entry_date"]
            == expected_new_entry.entry_date.isoformat()
            and returned_new_entry["user_id"] == str(expected_new_entry.user_id)
            and 70 <= returned_new_entry["weight"] <= 71
        )

        response = client_sample_storage.get(
            "/api/v1/daily-entries",
            params={
                "date_from": expected_unchanged_entry.entry_date.isoformat(),
                "date_to": expected_unchanged_entry.entry_date.isoformat(),
            },
        )
        assert response.status_code == 200
        assert response.json()[0]["weight"] == expected_unchanged_entry.weight

    def test_sync_data_empty_storage(self, client_empty_storage):
        """
        GIVEN:
            - DB with no entries
            - Converted daily entries from DemoDataSourceClient (hardcoded + current date's data)
        EXPECTED:
            - /sync-data returns success with the number of new entries
            - new entries are available when /daily-entries is called
        """
        data_source_entries = DemoDataSourceClient(
            DEMO_USER_ID
        ).convert_to_daily_entries(None)

        expected_delta_count = len(data_source_entries)
        expected_new_entry = data_source_entries[-1]

        response = client_empty_storage.post(
            "/api/v1/sync-data", json={"data_source": "gfit"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "sync_success"
        assert response.json()["new_entries_count"] == expected_delta_count

        response = client_empty_storage.get("/api/v1/daily-entries")

        assert response.status_code == 200
        assert len(response.json()) == expected_delta_count

        response = client_empty_storage.get(
            "/api/v1/daily-entries",
            params={
                "date_from": expected_new_entry.entry_date.isoformat(),
                "date_to": expected_new_entry.entry_date.isoformat(),
            },
        )
        returned_new_entry = response.json()[0]
        assert response.status_code == 200
        assert (
            returned_new_entry["entry_date"]
            == expected_new_entry.entry_date.isoformat()
            and returned_new_entry["user_id"] == str(expected_new_entry.user_id)
            and 70 <= returned_new_entry["weight"] <= 71
        )
