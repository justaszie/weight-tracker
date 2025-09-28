import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.analytics import (
    get_weekly_aggregates,
    get_summary,
)
from app.demo import DemoStorage, DemoDataSourceClient
from app.project_types import (
    WeightEntry,
    WeeklyAggregateEntry,
)


@pytest.fixture(autouse=True)
def enable_demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")


@pytest.fixture
def demo_storage_entries():
    return DemoStorage().get_weight_entries()


@pytest.fixture
def client():
    from app.main import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client


class TestDemoGetData:
    # Goal: testing that the API endpoints will work as expected,
    # when DEMO_MODE is set to true, and the data will be fetched using DemoStorage

    def test_get_latest_entry(self, client, demo_storage_entries):
        response = client.get("/api/latest-entry")
        expected_last_entry = sorted(
            demo_storage_entries, key=lambda entry: entry.entry_date
        )[-1]

        assert response.status_code == 200
        assert response.json() == expected_last_entry.model_dump(mode="json")

    def test_get_daily_entries(self, client, demo_storage_entries):
        response = client.get("/api/daily-entries")

        expected = TypeAdapter(list[WeightEntry]).validate_python(demo_storage_entries)
        expected_json = TypeAdapter(list[WeightEntry]).dump_python(
            expected, mode="json"
        )

        assert response.status_code == 200
        assert response.json() == expected_json

    def test_get_weekly_aggregates(self, client, demo_storage_entries):
        # Given: demo storage daily entries, weeks_limit param, and goal param
        # Expected: one entry for each week, sorted from the latest, with one additional reference week
        response = client.get(
            "/api/weekly-aggregates",
            params={
                "weeks_limit": "1",
                "goal": "lose",
            },
        )

        analytics_data = get_weekly_aggregates(demo_storage_entries, goal="lose")
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

    def test_get_summary(self, client, demo_storage_entries):
        # Given: demo storage daily entries, weeks_limit param
        # Expected: a JSON response with a property "metrics" which contains
        # the metrics calculated over N weeks using analytics module

        response = client.get(
            "/api/summary",
            params={
                "weeks_limit": "2",
            },
        )

        analytics_data = get_weekly_aggregates(demo_storage_entries, goal="lose")
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

        expected_json = {"metrics": metrics_data.model_dump(mode="json")}

        assert response.status_code == 200
        assert response.json() == expected_json


class TestDemoSyncData:
    def test_sync_data_new_entries(self, client, demo_storage_entries):
        """
        GIVEN:
            - DemoStorage daily entries
            - Converted daily entries from DemoDataSourceClient
        EXPECTED:
            - /sync-data returns success with the number of new entries
            - new entries are available when /daily-entries is called
            - existing entries in DemoStorage were not changed
        """
        existing_entries = DemoStorage().get_weight_entries()
        existing_dates = {entry.entry_date for entry in existing_entries}
        data_source_entries = DemoDataSourceClient().convert_to_daily_entries(None)
        data_source_dates = {entry.entry_date for entry in data_source_entries}

        new_entries = [
            entry
            for entry in data_source_entries
            if entry.entry_date not in existing_dates
        ]

        expected_delta_count = len(new_entries)
        expected_new_entry = new_entries[0]

        expected_unchanged_entry = [
            entry for entry in existing_entries if entry.entry_date in data_source_dates
        ][0]

        response = client.post("/api/sync-data", json={"data_source": "gfit"})

        assert response.status_code == 200
        assert response.json()["status"] == "sync_success"
        assert response.json()["new_entries_count"] == expected_delta_count

        response = client.get("/api/daily-entries")

        assert response.status_code == 200
        assert len(response.json()) == len(existing_entries) + expected_delta_count

        response = client.get(
            "api/daily-entries",
            params={
                "date_from": expected_new_entry.entry_date.isoformat(),
                "date_to": expected_new_entry.entry_date.isoformat(),
            },
        )
        assert response.status_code == 200
        assert response.json()[0]["weight"] == expected_new_entry.weight

        response = client.get(
            "api/daily-entries",
            params={
                "date_from": expected_unchanged_entry.entry_date.isoformat(),
                "date_to": expected_unchanged_entry.entry_date.isoformat(),
            },
        )
        assert response.status_code == 200
        assert response.json()[0]["weight"] == expected_unchanged_entry.weight
