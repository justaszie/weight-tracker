# pyright: reportMissingTypeStubs=false, reportUnknownVariableType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportMissingParameterType=false, reportUnknownMemberType=false

import datetime as dt

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.api import (
    get_filtered_daily_entries,
    get_filtered_weekly_entries,
    get_data_storage,
    NoCredentialsError,
)
from app.data_integration import DataSyncError, SourceFetchError, SourceNoDataError
from app.main import app
from app.project_types import (
    WeightEntry,
    WeeklyAggregateEntry,
)
from app.utils import DEFAULT_GOAL

DATE_PARAMS_TEST_CASES = [
    (None, "2025-01-20"),
    ("2024-05-12", None),
    ("2012-02-09", "2013-01-01"),
    ("2024-12-31", "2025-01-01"),
    ("2024-12-01", "2024-12-01"),
    (None, None),
]
WEEKLY_PARAMS_TEST_CASES = [
    (None, "2"),
    ("lose", "1"),
    ("maintain", "4"),
    ("gain", "10"),
    ("gain", None),
]


@pytest.fixture
def sample_daily_entries():
    data = [
        {"date": dt.date(2024, 10, 2), "weight": 73.81},
        {"date": dt.date(2025, 1, 12), "weight": 72},
        {"date": dt.date(2025, 8, 28), "weight": 71.12},
        {"date": dt.date(2025, 8, 30), "weight": 73.5},
        {"date": dt.date(2025, 9, 2), "weight": 72},
    ]
    return TypeAdapter(list[WeightEntry]).validate_python(data)


@pytest.fixture
def sample_daily_entries_extended():
    data = [
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
    return TypeAdapter(list[WeightEntry]).validate_python(data)


@pytest.fixture
def sample_weekly_entries():
    data = [
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
    ]
    return TypeAdapter(list[WeeklyAggregateEntry]).validate_python(data)


class TestHelperFunctions:
    @pytest.mark.parametrize(
        "date_from, date_to, expected_entries",
        [
            (
                dt.date(2025, 8, 28),
                None,
                [
                    {"date": dt.date(2025, 8, 28), "weight": 71.12},
                    {"date": dt.date(2025, 8, 30), "weight": 73.5},
                    {"date": dt.date(2025, 9, 2), "weight": 72},
                ],
            ),
            (
                "",
                dt.date(2025, 2, 1),
                [
                    {"date": dt.date(2024, 10, 2), "weight": 73.81},
                    {"date": dt.date(2025, 1, 12), "weight": 72},
                ],
            ),
            (
                dt.date(2025, 5, 1),
                dt.date(2025, 9, 1),
                [
                    {"date": dt.date(2025, 8, 28), "weight": 71.12},
                    {"date": dt.date(2025, 8, 30), "weight": 73.5},
                ],
            ),
            (
                None,
                None,
                [
                    {"date": dt.date(2024, 10, 2), "weight": 73.81},
                    {"date": dt.date(2025, 1, 12), "weight": 72},
                    {"date": dt.date(2025, 8, 28), "weight": 71.12},
                    {"date": dt.date(2025, 8, 30), "weight": 73.5},
                    {"date": dt.date(2025, 9, 2), "weight": 72},
                ],
            ),
            (
                dt.date(2024, 1, 10),
                dt.date(2024, 10, 1),
                [],
            ),
            (
                dt.date(2024, 10, 2),
                dt.date(2024, 10, 2),
                [
                    {"date": dt.date(2024, 10, 2), "weight": 73.81},
                ],
            ),
        ],
    )
    def test_get_filtered_daily_entries(
        self, mocker, sample_daily_entries, date_from, date_to, expected_entries
    ) -> None:
        mock_storage = mocker.MagicMock()
        mock_storage.get_weight_entries.return_value = sample_daily_entries
        app.dependency_overrides[get_data_storage] = lambda: mock_storage

        daily_entries = get_filtered_daily_entries(mock_storage, date_from, date_to)
        expected_entries = TypeAdapter(list[WeightEntry]).validate_python(
            expected_entries
        )
        assert daily_entries == expected_entries

        app.dependency_overrides.pop(get_data_storage, None)

    @pytest.mark.parametrize(
        "weeks_limit, expected_entries",
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
                1,
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
                2,
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
        self, mocker, weeks_limit, sample_daily_entries_extended, expected_entries
    ):
        expected_entries = TypeAdapter(list[WeeklyAggregateEntry]).validate_python(
            expected_entries
        )
        assert (
            get_filtered_weekly_entries(
                sample_daily_entries_extended, "lose", weeks_limit
            )
            == expected_entries
        )

    def test_get_filtered_weekly_entries_empty_dataset(self):
        daily_entries = []
        assert get_filtered_weekly_entries(daily_entries, "lose", 2) == []


class TestAPIEndpoints:
    ENDPOINT_URLS = {
        "latest-entry": app.url_path_for("get_latest_entry"),
        "daily-entries": app.url_path_for("get_daily_entries"),
        "weekly-aggregates": app.url_path_for("get_weekly_aggregates"),
        "summary": app.url_path_for("get_summary"),
        "sync-data": app.url_path_for("sync_data"),
    }

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_storage(self, mocker):
        mock_storage = mocker.MagicMock()
        app.dependency_overrides[get_data_storage] = lambda: mock_storage
        yield mock_storage
        app.dependency_overrides.pop(get_data_storage, None)

    @pytest.fixture
    def mock_storage_refresh_needed(self, mocker):
        mock_storage = mocker.MagicMock()
        mock_storage.data_refresh_needed.return_value = True

        # Override get_data_storage function with a lambda that just returns mock storage
        app.dependency_overrides[get_data_storage] = lambda: mock_storage
        yield mock_storage

        # Make sure to remove the dependency override after the tests run
        app.dependency_overrides.pop(get_data_storage, None)


    @pytest.mark.parametrize(
        "latest_entry, expected_return",
        [
            (
                WeightEntry(date=dt.date(2025, 9, 1), weight=72.56),
                {"date": "2025-09-01", "weight": 72.56},
            ),
            (None, None),
        ],
    )
    def test_get_latest_entry(self, client, mocker, latest_entry, expected_return):
        mocker.patch("app.api.utils.get_latest_daily_entry").return_value = latest_entry

        response = client.get(self.ENDPOINT_URLS["latest-entry"])

        assert response.status_code == 200
        assert response.json() == expected_return

    def test_get_latest_entry_error(self, client, mocker):
        mocker.patch("app.api.utils.get_latest_daily_entry").side_effect = Exception(
            "Random Error"
        )

        response = client.get(self.ENDPOINT_URLS["latest-entry"])

        assert response.status_code == 500
        assert "detail" in response.json()

    def _test_dates_params_usage(
        self, client, mocker, mock_storage, endpoint_name, date_from, date_to
    ):
        fetch_daily_fn = mocker.patch("app.api.get_filtered_daily_entries")

        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        endpoint_url = self.ENDPOINT_URLS[endpoint_name]
        response = client.get(endpoint_url, params=params)

        assert response.status_code == 200
        fetch_daily_fn.assert_called_once_with(
            mock_storage,
            dt.date.fromisoformat(date_from) if date_from else None,
            dt.date.fromisoformat(date_to) if date_to else None,
        )

    def _test_weekly_aggregate_params_usage(
        self, client, mocker, endpoint_name, sample_daily_entries, goal, weeks_limit
    ):
        fetch_daily_fn = mocker.patch("app.api.get_filtered_daily_entries")
        fetch_daily_fn.return_value = sample_daily_entries
        fetch_weekly_fn = mocker.patch("app.api.get_filtered_weekly_entries")

        params = {}
        if weeks_limit:
            params["weeks_limit"] = weeks_limit
        if goal:
            params["goal"] = goal

        endpoint_url = self.ENDPOINT_URLS[endpoint_name]
        response = client.get(endpoint_url, params=params)

        assert response.status_code == 200
        fetch_weekly_fn.assert_called_once_with(
            sample_daily_entries,
            params.get("goal", DEFAULT_GOAL),
            int(weeks_limit) if weeks_limit else None,
        )

    @pytest.mark.parametrize("date_from, date_to", DATE_PARAMS_TEST_CASES)
    def test_daily_entries_date_params_usage(
        self, client, mocker, mock_storage, date_from, date_to
    ) -> None:
        self._test_dates_params_usage(
            client, mocker, mock_storage, "daily-entries", date_from, date_to
        )

    @pytest.mark.parametrize("date_from, date_to", DATE_PARAMS_TEST_CASES)
    def test_weekly_aggregates_date_params_usage(
        self, client, mocker, mock_storage, date_from, date_to
    ):
        self._test_dates_params_usage(
            client, mocker, mock_storage, "weekly-aggregates", date_from, date_to
        )

    @pytest.mark.parametrize("date_from, date_to", DATE_PARAMS_TEST_CASES)
    def test_summary_date_params_usage(self, client, mocker, mock_storage, date_from, date_to):
        self._test_dates_params_usage(client, mocker, mock_storage, "summary", date_from, date_to)

    @pytest.mark.parametrize("goal, weeks_limit", WEEKLY_PARAMS_TEST_CASES)
    def test_weekly_aggregates_weekly_params_usage(
        self, client, mocker, sample_daily_entries, goal, weeks_limit
    ):
        self._test_weekly_aggregate_params_usage(
            client, mocker, "weekly-aggregates", sample_daily_entries, goal, weeks_limit
        )

    @pytest.mark.parametrize("weeks_limit", ["1", "10", "3"])
    def test_summary_weekly_params_usage(
        self, client, mocker, sample_daily_entries, weeks_limit
    ):
        self._test_weekly_aggregate_params_usage(
            client, mocker, "summary", sample_daily_entries, None, weeks_limit
        )

    def test_get_daily_entries(self, client, mocker, sample_daily_entries):
        fetch_data_fn = mocker.patch("app.api.get_filtered_daily_entries")
        fetch_data_fn.return_value = sample_daily_entries

        response = client.get(self.ENDPOINT_URLS["daily-entries"])

        expected_return = [
            entry.model_dump(mode="json") for entry in sample_daily_entries
        ]

        assert response.status_code == 200
        assert response.json() == expected_return

    def test_get_daily_entries_invalid_dates_range(self, client):
        invalid_params = {"date_from": "2026-01-01", "date_to": "2025-12-02"}

        response = client.get(
            self.ENDPOINT_URLS["daily-entries"], params=invalid_params
        )

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_get_daily_entries_exceptions(self, client, mocker):
        mocker.patch("app.api.get_filtered_daily_entries").side_effect = Exception(
            "Random Error"
        )

        response = client.get(self.ENDPOINT_URLS["daily-entries"])

        assert response.status_code == 500
        assert "detail" in response.json()

    def test_weekly_aggregates_return_value(
        self, client, sample_weekly_entries, mocker
    ):
        fetch_weekly_fn = mocker.patch("app.api.get_filtered_weekly_entries")
        fetch_weekly_fn.return_value = sample_weekly_entries
        mocker.patch("app.api.get_filtered_daily_entries")

        params = {"goal": "lose", "weeks_limit": "4"}

        expected_return = {
            "weekly_data": [
                entry.model_dump(mode="json")
                for entry in sorted(
                    sample_weekly_entries,
                    key=lambda week: week.week_start,
                    reverse=True,
                )
            ],
            "goal": params["goal"],
        }

        response = client.get(self.ENDPOINT_URLS["weekly-aggregates"])

        assert response.status_code == 200
        assert response.json() == expected_return

    def test_weekly_aggregates_invalid_dates(self, client):
        params = {
            "date_from": "2025-10-02",
            "date_to": "2025-10-01",
        }

        response = client.get(self.ENDPOINT_URLS["weekly-aggregates"], params=params)

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_weekly_aggregates_invalid_goal(self, client):
        params = {"goal": "Whatever"}

        response = client.get(self.ENDPOINT_URLS["weekly-aggregates"], params=params)

        assert response.status_code == 422
        assert "detail" in response.json()

    @pytest.mark.parametrize("invalid_weeks_limit", ["-1", "0", "-10"])
    def test_weekly_aggregates_invalid_weeks_limit(self, client, invalid_weeks_limit):
        params = {
            "goal": "lose",
            "weeks_limit": invalid_weeks_limit,
        }

        response = client.get(self.ENDPOINT_URLS["weekly-aggregates"], params=params)

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_weekly_aggregates_exceptions(self, client, mocker):
        mocker.patch("app.api.get_filtered_daily_entries").side_effect = Exception(
            "Random Error"
        )

        response = client.get(self.ENDPOINT_URLS["weekly-aggregates"])

        assert response.status_code == 500
        assert "detail" in response.json()

    def test_summary_invalid_dates(self, client):
        params = {
            "date_from": "2025-10-02",
            "date_to": "2025-10-01",
        }

        response = client.get(self.ENDPOINT_URLS["summary"], params=params)

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_summary_exceptions(self, client, mocker):
        mocker.patch("app.api.get_filtered_daily_entries").side_effect = Exception(
            "Random Error"
        )

        response = client.get(self.ENDPOINT_URLS["summary"])

        assert response.status_code == 500
        assert "detail" in response.json()

    @pytest.mark.parametrize("data_source_client_name", ["gfit", "mfp"])
    def test_sync_data_data_source_creation(
        self, client, data_source_client_name, mocker, mock_storage_refresh_needed
    ):
        mocker.patch(
            "app.api.GoogleFitAuth"
        ).return_value.load_auth_token.return_value = "creds123"
        mocker.patch("app.api.DataIntegrationService")

        # Mocking the appropriate data source constructor based on the request params
        data_soure_client_mapping = {
            "gfit": "app.api.GoogleFitClient",
            "mfp": "app.api.MyFitnessPalClient",
        }
        mock_data_source_client_constructor = mocker.patch(
            data_soure_client_mapping[data_source_client_name]
        )

        # Setting up HTTP request body
        request_body = {
            "data_source": data_source_client_name,
        }

        # Acting
        response = client.post(self.ENDPOINT_URLS["sync-data"], json=request_body)

        # Assertions
        assert response.status_code == 200
        mock_data_source_client_constructor.assert_called_once()

    def test_sync_data_invalid_data_source(self, client):
        request_body = {"data_source": "invalid_src"}
        response = client.post(self.ENDPOINT_URLS["sync-data"], json=request_body)

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_sync_data_success(self, client, mocker, sample_daily_entries, mock_storage_refresh_needed):
        mocker.patch("app.api.GoogleFitAuth")
        mock_service = mocker.patch("app.api.DataIntegrationService").return_value
        mock_service.refresh_weight_entries.return_value = sample_daily_entries

        mocker.patch("app.api.GoogleFitClient")

        request_body = {
            "data_source": "gfit",
        }

        response = client.post(self.ENDPOINT_URLS["sync-data"], json=request_body)

        expected_response = {
            "status": "sync_success",
            "new_entries_count": len(sample_daily_entries),
        }
        actual_response = response.json()

        assert response.status_code == 200
        assert all(actual_response[k] == v for k, v in expected_response.items())

    def test_sync_data_refresh_not_needed(self, client, mocker, mock_storage):
        mock_storage.data_refresh_needed.return_value = False

        response = client.post(
            self.ENDPOINT_URLS["sync-data"], json={"data_source": "gfit"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "data_up_to_date"

    def test_sync_data_auth_needed(self, client, mocker, mock_storage_refresh_needed):

        mocker.patch(
            "app.api.get_data_source_client"
        ).side_effect = NoCredentialsError

        response = client.post(
            self.ENDPOINT_URLS["sync-data"], json={"data_source": "gfit"}
        )

        actual_response = response.json()

        assert response.status_code == 401
        assert "auth_url" in actual_response
        assert actual_response["auth_url"] ==  app.url_path_for("google_signin")

    def test_sync_data_no_new_data(self, client, mocker, mock_storage_refresh_needed):
        mocker.patch("app.api.GoogleFitAuth")
        mock_service = mocker.patch("app.api.DataIntegrationService").return_value
        mock_service.refresh_weight_entries.return_value = []

        mocker.patch("app.api.GoogleFitClient")

        response = client.post(
            self.ENDPOINT_URLS["sync-data"], json={"data_source": "gfit"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "no_new_data"

    def test_sync_data_no_data_found(self, client, mocker, mock_storage_refresh_needed):
        mocker.patch("app.api.GoogleFitAuth")
        mock_service = mocker.patch("app.api.DataIntegrationService").return_value
        mock_service.refresh_weight_entries.side_effect = SourceNoDataError("no data")

        mocker.patch("app.api.GoogleFitClient")

        response = client.post(
            self.ENDPOINT_URLS["sync-data"], json={"data_source": "gfit"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "no_data_received"

    @pytest.mark.parametrize("exc",
        [SourceFetchError('test'), DataSyncError('test')]
    )
    def test_sync_data_refresh_exceptions(self, client, mocker, mock_storage_refresh_needed, exc):
        mocker.patch("app.api.GoogleFitAuth")
        mock_service = mocker.patch("app.api.DataIntegrationService").return_value
        mock_service.refresh_weight_entries.side_effect = exc

        mocker.patch("app.api.GoogleFitClient")

        response = client.post(
            self.ENDPOINT_URLS["sync-data"], json={"data_source": "gfit"}
        )

        assert response.status_code == 500
        assert "detail" in response.json()
