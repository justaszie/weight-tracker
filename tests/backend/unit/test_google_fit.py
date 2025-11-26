import datetime as dt
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter
from typing import Any
from uuid import UUID

from app.google_fit import (
    GoogleClientConfigError,
    GoogleFitAuth,
    GoogleFitClient,
    handle_google_auth_callback,
    HttpError,
    NoCredentialsError,
)
from app.main import app
from app.project_types import WeightEntry

TEST_USER_ID = UUID("3760183f-61fa-4ee1-badf-2668fbec152d")


@pytest.fixture
def gfit_client_no_creds():
    return GoogleFitClient(user_id=TEST_USER_ID)


@pytest.fixture
def gfit_client():
    return GoogleFitClient(user_id=TEST_USER_ID, creds="testcreds")  # type: ignore


@pytest.fixture
def sample_raw_dataset() -> dict[str, Any]:
    return {  # type: ignore
        "minStartTimeNs": "0",
        "maxEndTimeNs": "1757050801266618112",
        "dataSourceId": "derived:com.google.weight:com.google.android.gms:merge_weight",
        "point": [
            {
                "startTimeNanos": "1756960320000000000",
                "endTimeNanos": "1756960320000000000",
                "dataTypeName": "com.google.weight",
                "originDataSourceId": "raw:com.google.weight:com.google.android.apps.fitness:user_input",
                "value": [{"fpVal": 73.0999984741211, "mapVal": []}],
                "modifiedTimeMillis": "1756960338250",
            },
            {
                "startTimeNanos": "1756874340000000000",
                "endTimeNanos": "1756874340000000000",
                "dataTypeName": "com.google.weight",
                "originDataSourceId": "raw:com.google.weight:com.google.android.apps.fitness:user_input",
                "value": [{"fpVal": 73.5599984741211, "mapVal": []}],
                "modifiedTimeMillis": "1756874454792",
            },
        ],
    }


@pytest.fixture
def empty_raw_dataset() -> dict[str, Any]:
    return {  # type: ignore
        "minStartTimeNs": "0",
        "maxEndTimeNs": "1757050801266618112",
        "dataSourceId": "derived:com.google.weight:com.google.android.gms:merge_weight",
        "point": [],
    }


@pytest.fixture
def auth_client():
    return GoogleFitAuth()


@pytest.fixture
def test_creds_data():
    return """
        {
            "token": "abca12",
            "refresh_token": "1//tjj5",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "aaa.apps.googleusercontent.com",
            "client_secret": "add444",
            "scopes": [
                "https://www.googleapis.com/auth/fitness.body.read",
                "https://www.googleapis.com/auth/fitness.activity.read"
            ],
            "universe_domain": "googleapis.com",
            "account": "",
            "expiry": "2025-09-08T07:06:53.565408Z"
        }"""


class TestGoogleFitClient:
    def test_get_raw_data_no_creds(self, gfit_client_no_creds):
        with pytest.raises(NoCredentialsError):
            gfit_client_no_creds.get_raw_data()

    def test_get_raw_data(self, mocker, gfit_client, sample_raw_dataset):
        # Setting up test parameters to the multiple function calls
        date_from_ns_timestamp = 0
        now = dt.datetime.now()
        tomorrow: dt.datetime = now + dt.timedelta(days=1)
        timestamp_to_ns = int(tomorrow.timestamp() * 1e9)
        user_id_param = "me"
        data_source_id_param = (
            "derived:com.google.weight:com.google.android.gms:merge_weight"
        )
        dataset_id_param = f"{date_from_ns_timestamp}-{timestamp_to_ns}"

        get_requets_params = {
            "userId": user_id_param,
            "dataSourceId": data_source_id_param,
            "datasetId": dataset_id_param,
        }

        # Mocking the datetime to compare fixed param values
        mocker.patch("app.google_fit.dt.datetime").now.return_value = now

        # Mocking the 3rd party function objects
        mock_service_build_fn = mocker.patch("app.google_fit.build")
        mock_service = mock_service_build_fn.return_value

        mock_get_request_fn = mock_service.users().dataSources().datasets().get
        mock_request = mock_get_request_fn.return_value

        mock_execute_fn = mock_request.execute
        mock_execute_fn.return_value = sample_raw_dataset

        # Run the actual code
        result = gfit_client.get_raw_data()

        # Testing the function return value and the 3rd party function calls with expected params
        mock_service_build_fn.assert_called_once_with(
            "fitness", "v1", credentials=gfit_client.creds
        )
        mock_get_request_fn.assert_called_once_with(**get_requets_params)
        mock_execute_fn.assert_called_once()
        assert result == sample_raw_dataset

    def test_get_empty_raw_dataset(self, mocker, gfit_client, empty_raw_dataset):
        mock_service = mocker.patch("app.google_fit.build").return_value
        mock_execute_fn = (
            mock_service.users().dataSources().datasets().get.return_value.execute
        )
        mock_execute_fn.return_value = empty_raw_dataset

        result = gfit_client.get_raw_data()

        mock_execute_fn.assert_called_once()
        assert result == empty_raw_dataset

    def test_get_raw_data_api_http_errors(self, mocker, gfit_client):
        mock_service = mocker.patch("app.google_fit.build").return_value
        mock_execute_fn = (
            mock_service.users().dataSources().datasets().get.return_value.execute
        )

        mock_err_response = mocker.Mock()
        mock_err_response.status = 404
        mock_execute_fn.side_effect = HttpError(
            mock_err_response, "Invalid Dataset".encode()
        )

        # get_raw_data expected to propagate HttpError
        with pytest.raises(HttpError):
            gfit_client.get_raw_data()

    def test_extract_datapoints(self, gfit_client_no_creds, sample_raw_dataset):
        datapoints = gfit_client_no_creds._extract_datapoints(sample_raw_dataset)
        expected_properties = ("value", "startTimeNanos", "endTimeNanos")
        # Checking that the datapoints extracted from the response contains all the properties we use in conversion
        assert type(datapoints) == list
        assert len(datapoints) == 2

        assert all(
            [
                all([key in datapoint for key in expected_properties])
                and "fpVal" in datapoint["value"][0]
                for datapoint in datapoints
            ]
        )

    def test_convert_to_daily_entries(self, gfit_client_no_creds, sample_raw_dataset):
        actual_return = gfit_client_no_creds.convert_to_daily_entries(
            sample_raw_dataset
        )
        expected_return = TypeAdapter(list[WeightEntry]).validate_python(
            [
                {
                    "entry_date": dt.date(2025, 9, 3),
                    "weight": 73.56,
                    "user_id": TEST_USER_ID,
                },
                {
                    "entry_date": dt.date(2025, 9, 4),
                    "weight": 73.10,
                    "user_id": TEST_USER_ID,
                },
            ]
        )
        assert actual_return == expected_return

    def test_convert_to_daily_entries_empty_dataset(
        self, gfit_client_no_creds, empty_raw_dataset
    ):
        assert gfit_client_no_creds.convert_to_daily_entries(empty_raw_dataset) == []


class TestGoogleFitAuth:
    def test_load_valid_creds(self, mocker, auth_client):
        mock_creds_object = mocker.Mock()
        mock_creds_object.valid = True

        mock_storage = mocker.Mock()
        mock_storage.load_google_credentials.return_value = mock_creds_object

        result = auth_client.load_credentials(mock_storage, TEST_USER_ID)
        assert result == mock_creds_object

    def test_load_creds_with_refresh_success(self, mocker, auth_client):
        mock_creds_object = mocker.Mock()
        mock_creds_object.valid = False
        mock_creds_object.expired = True
        mock_creds_object.refresh_token = "dae/123"

        mock_storage = mocker.Mock()
        mock_storage.load_google_credentials.return_value = mock_creds_object

        mock_save_creds_fn = mocker.patch.object(auth_client, "save_credentials")

        result = auth_client.load_credentials(mock_storage, TEST_USER_ID)
        assert result == mock_creds_object

        mock_creds_object.refresh.assert_called_once()

        mock_save_creds_fn.assert_called_once_with(
            mock_storage, TEST_USER_ID, mock_creds_object
        )

    def test_load_creds_with_refresh_fail(self, mocker, auth_client):
        mock_creds_object = mocker.Mock()
        mock_creds_object.valid = False
        mock_creds_object.expired = True
        mock_creds_object.refresh_token = "dae/123"

        mock_storage = mocker.Mock()
        mock_storage.load_google_credentials.return_value = mock_creds_object

        mock_save_creds_fn = mocker.patch.object(auth_client, "save_credentials")
        mock_creds_object.refresh.side_effect = Exception()

        result = auth_client.load_credentials(mock_storage, TEST_USER_ID)
        mock_creds_object.refresh.assert_called_once()
        assert result == None
        assert not mock_save_creds_fn.called

    def test_load_creds_no_refresh_token(self, mocker, auth_client):
        mock_creds_object = mocker.Mock()
        mock_creds_object.valid = False
        mock_creds_object.expired = True
        mock_creds_object.refresh_token = None

        mock_storage = mocker.Mock()
        mock_storage.load_google_credentials.return_value = mock_creds_object

        mock_save_creds_fn = mocker.patch.object(auth_client, "save_credentials")

        result = auth_client.load_credentials(mock_storage, TEST_USER_ID)
        assert result == None
        assert not mock_save_creds_fn.called

    def test_save_valid_credentials(self, mocker, auth_client):
        mock_storage = mocker.Mock()
        mock_creds_object = mocker.Mock()

        auth_client.save_credentials(mock_storage, TEST_USER_ID, mock_creds_object)

        mock_storage.store_google_credentials.assert_called_once_with(
            TEST_USER_ID, mock_creds_object
        )

    def test_save_invalid_credentials(self, mocker, auth_client):
        # What happens when we pass invalid creds to storage.store_google_credentials
        mock_storage = mocker.Mock()
        mock_creds_object = mocker.Mock()
        mock_storage.store_google_credentials.side_effect = Exception()

        with pytest.raises(Exception):
            auth_client.save_credentials(mock_storage, TEST_USER_ID, mock_creds_object)

    def test_create_client_config(self, mocker, auth_client):
        mock_env_vars = {
            "GOOGLE_CLIENT_ID": "ABC123",
            "GOOGLE_CLIENT_SECRET": "123ABC",
            "GOOGLE_PROJECT_ID": "SAMPLE",
            "GOOGLE_AUTH_URI": "http://domain.example",
            "GOOGLE_TOKEN_URI": "http://domain.example/token",
            "GOOGLE_REDIRECT_URIS": "http://app.sample,http://url.sample",
        }

        expected_client_config = {
            "web": {
                "client_id": "ABC123",
                "client_secret": "123ABC",
                "project_id": "SAMPLE",
                "auth_uri": "http://domain.example",
                "token_uri": "http://domain.example/token",
                "redirect_uris": ["http://app.sample", "http://url.sample"],
            },
        }
        mocker.patch.dict("os.environ", mock_env_vars, clear=True)

        result = auth_client.create_client_config()

        assert result == expected_client_config

    def test_create_client_config_missing(self, mocker, auth_client):
        mock_env_vars = {
            "GOOGLE_CLIENT_ID": "ABC123",
            "GOOGLE_PROJECT_ID": "SAMPLE",
            "GOOGLE_AUTH_URI": "http://domain.example",
            "GOOGLE_TOKEN_URI": "http://domain.example/token",
            "GOOGLE_REDIRECT_URIS": "http://app.sample,http://url.sample",
        }

        mocker.patch.dict("os.environ", mock_env_vars, clear=True)

        with pytest.raises(GoogleClientConfigError):
            auth_client.create_client_config()


class TestGoogleFitAuthEndpoints:
    def test_signing_flow(self, mocker):
        mock_get_current_user = mocker.patch("app.google_fit.get_current_user")
        mock_get_current_user.return_value = TEST_USER_ID
        mock_auth_client_constructor = mocker.patch("app.google_fit.GoogleFitAuth")
        mock_auth_client = mock_auth_client_constructor.return_value
        mock_flow_obj = mocker.patch(
            "app.google_fit.Flow"
        ).from_client_config.return_value

        test_auth_url = "https://url.test"
        test_state = "random123"

        mock_flow_obj.authorization_url.return_value = (test_auth_url, test_state)

        with TestClient(app) as api_client:
            response = api_client.get(
                app.url_path_for("google_signin"),
                headers={"Authorization": "Bearer abc123"},
                params={"user_id": TEST_USER_ID},
                follow_redirects=False,
            )

            mock_auth_client_constructor.assert_called_once()
            mock_auth_client.create_client_config.assert_called_once()

            assert response.status_code == 307
            assert response.headers["location"] == test_auth_url

    def test_signin_flow_config_errors(self, mocker):
        mock_get_current_user = mocker.patch("app.google_fit.get_current_user")
        mock_get_current_user.return_value = TEST_USER_ID

        mock_auth_client_constructor = mocker.patch("app.google_fit.GoogleFitAuth")
        mock_auth_client = mock_auth_client_constructor.return_value
        mock_auth_client.create_client_config.side_effect = GoogleClientConfigError()

        with TestClient(app) as api_client:
            response = api_client.get(
                app.url_path_for("google_signin"),
                headers={"Authorization": "Bearer abc123"},
                params={"user_id": TEST_USER_ID},
                follow_redirects=False,
            )

            mock_auth_client_constructor.assert_called_once()
            mock_auth_client.create_client_config.assert_called_once()

            assert response.status_code == 500

    def test_handle_callback(self, mocker, monkeypatch):
        mock_request_obj = mocker.Mock()
        mock_request_obj.session = {
            "state": "random_value",
            "user_id": str(TEST_USER_ID),
        }
        mock_storage_obj = mocker.Mock()
        mock_request_obj.app.state.data_storage = mock_storage_obj
        mock_request_obj.url = "https://url.sample"

        mock_flow_obj = mocker.patch(
            "app.google_fit.Flow.from_client_config"
        ).return_value
        fetch_token_fn = mock_flow_obj.fetch_token
        mock_creds_obj = mocker.Mock()
        mock_creds_obj.token = "test_token"
        mock_flow_obj.credentials = mock_creds_obj

        mock_auth_client = mocker.patch("app.google_fit.GoogleFitAuth").return_value

        redirect_url_host = "https:/fe.url"
        monkeypatch.setenv("FRONTEND_URL", redirect_url_host)

        result = handle_google_auth_callback(request=mock_request_obj)

        assert result.status_code == 307
        assert (
            result.headers["location"]
            == f"{redirect_url_host}?initiator=data_source_auth_success&source=gfit"
        )
        fetch_token_fn.assert_called_once_with(
            authorization_response=mock_request_obj.url
        )
        mock_auth_client.save_credentials.assert_called_once_with(
            mock_storage_obj, TEST_USER_ID, mock_creds_obj
        )
        assert (
            mock_request_obj.session.get("state") is None
            and mock_request_obj.session.get("user_id") is None
        )
