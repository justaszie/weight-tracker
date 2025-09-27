import datetime as dt
import json

import pytest
from pydantic import TypeAdapter

from app.google_fit import (
    GoogleFitAuth,
    GoogleFitClient,
    HttpError,
    NoCredentialsError,
    TOKEN_FILE_PATH,
)
from app.project_types import WeightEntry


@pytest.fixture
def client_no_creds():
    return GoogleFitClient()


@pytest.fixture
def client():
    return GoogleFitClient("testcreds")


@pytest.fixture
def sample_raw_dataset():
    return {
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
def empty_raw_dataset():
    return {
        "minStartTimeNs": "0",
        "maxEndTimeNs": "1757050801266618112",
        "dataSourceId": "derived:com.google.weight:com.google.android.gms:merge_weight",
        "point": [],
    }


@pytest.fixture
def auth_client():
    return GoogleFitAuth()


@pytest.fixture
def test_token_file_data():
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


def test_get_raw_data_no_creds(client_no_creds):
    with pytest.raises(NoCredentialsError):
        result = client_no_creds.get_raw_data()


def test_get_raw_data(mocker, client, sample_raw_dataset):
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
    result = client.get_raw_data()

    # Testing the function return value and the 3rd party function calls with expected params
    mock_service_build_fn.assert_called_once_with(
        "fitness", "v1", credentials=client.creds
    )
    mock_get_request_fn.assert_called_once_with(**get_requets_params)
    mock_execute_fn.assert_called_once()
    assert result == sample_raw_dataset


def test_get_empty_raw_dataset(mocker, client, empty_raw_dataset):
    mock_service = mocker.patch("app.google_fit.build").return_value
    mock_execute_fn = (
        mock_service.users().dataSources().datasets().get.return_value.execute
    )
    mock_execute_fn.return_value = empty_raw_dataset

    result = client.get_raw_data()

    mock_execute_fn.assert_called_once()
    assert result == empty_raw_dataset


def test_get_raw_data_api_http_errors(mocker, client):
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
        client.get_raw_data()


def test_extract_datapoints(client_no_creds, sample_raw_dataset):
    datapoints = client_no_creds._extract_datapoints(sample_raw_dataset)
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


def test_convert_to_daily_entries(client_no_creds, sample_raw_dataset):
    actual_return = client_no_creds.convert_to_daily_entries(sample_raw_dataset)
    expected_return = TypeAdapter(list[WeightEntry]).validate_python(
        [
            {
                "entry_date": dt.date(2025, 9, 3),
                "weight": 73.56,
            },
            {
                "entry_date": dt.date(2025, 9, 4),
                "weight": 73.10,
            },
        ]
    )
    assert actual_return == expected_return


def test_convert_to_daily_entries_empty_dataset(client_no_creds, empty_raw_dataset):
    assert client_no_creds.convert_to_daily_entries(empty_raw_dataset) == []


def test_store_raw_data(mocker, client, sample_raw_dataset, tmp_path):
    test_file = tmp_path / "test_raw_data.json"
    mocker.patch("app.google_fit.RAW_DATA_FILE_PATH", new=test_file)

    client.store_raw_data(sample_raw_dataset)

    expected_written_data = json.dumps(sample_raw_dataset)
    test_file.read_text() == expected_written_data


def test_load_creds_no_file(mocker, auth_client):
    test_filename = "app/nonexisting_file.json"
    mocker.patch("app.google_fit.TOKEN_FILE_PATH", test_filename)
    file_open_fn = mocker.patch("app.google_fit.open", mocker.mock_open())
    creds = auth_client.load_auth_token()

    assert creds == None
    # Function stopped before trying to open nonexisting files
    assert not file_open_fn.called


def test_load_valid_creds(mocker, auth_client, test_token_file_data, tmp_path):
    test_file = tmp_path / "test_token.json"
    test_file.write_text(test_token_file_data)

    mocker.patch("app.google_fit.TOKEN_FILE_PATH", new=test_file)

    mock_creds_load_fn = mocker.patch(
        "app.google_fit.Credentials.from_authorized_user_info"
    )
    mock_creds = mock_creds_load_fn.return_value
    mock_creds.valid = True

    creds = auth_client.load_auth_token()

    mock_creds_load_fn.assert_called_once_with(json.loads(test_token_file_data))
    assert creds == mock_creds
    assert creds.valid == True


def test_load_creds_with_refresh_success(mocker, auth_client, test_token_file_data):
    mocker.patch("app.google_fit.os.path.exists").return_value = True

    token_file_load_fn = mocker.patch(
        "app.google_fit.open", mocker.mock_open(read_data=test_token_file_data)
    )
    creds_load_fn = mocker.patch("app.google_fit.Credentials.from_authorized_user_info")
    creds_object = creds_load_fn.return_value

    creds_object.valid = False
    creds_object.expired = True
    creds_object.refresh_token = "abc567"

    refresh_fn = mocker.patch.object(creds_object, "refresh")
    save_token_fn = mocker.patch.object(auth_client, "save_auth_token_to_file")

    creds = auth_client.load_auth_token()

    refresh_fn.assert_called_once()
    save_token_fn.assert_called_once_with(creds_object)
    assert creds == creds_object


def test_load_creds_with_refresh_fail(mocker, auth_client, test_token_file_data):
    mocker.patch("app.google_fit.os.path.exists").return_value = True

    token_file_load_fn = mocker.patch(
        "app.google_fit.open", mocker.mock_open(read_data=test_token_file_data)
    )
    creds_load_fn = mocker.patch("app.google_fit.Credentials.from_authorized_user_info")
    creds_object = creds_load_fn.return_value

    creds_object.valid = False
    creds_object.expired = True
    creds_object.refresh_token = "abc567"

    refresh_fn = mocker.patch.object(creds_object, "refresh")
    refresh_fn.side_effect = Exception()

    creds = auth_client.load_auth_token()

    refresh_fn.assert_called_once()
    assert creds == None


def test_load_creds_no_refresh_token(mocker, auth_client, test_token_file_data):
    mocker.patch("app.google_fit.os.path.exists").return_value = True

    token_file_load_fn = mocker.patch(
        "app.google_fit.open", mocker.mock_open(read_data=test_token_file_data)
    )
    creds_load_fn = mocker.patch("app.google_fit.Credentials.from_authorized_user_info")
    creds_object = creds_load_fn.return_value

    creds_object.valid = False
    creds_object.expired = True
    creds_object.refresh_token = None

    creds = auth_client.load_auth_token()

    assert creds == None


def test_save_auth_token(mocker, auth_client, test_token_file_data, tmp_path):
    # Mock the token filepath
    test_file = tmp_path / "test_token.json"
    mocker.patch("app.google_fit.TOKEN_FILE_PATH", new=test_file)

    mock_creds = mocker.Mock()
    mock_creds.to_json.return_value = test_token_file_data

    auth_client.save_auth_token_to_file(mock_creds)

    written_text = test_file.read_text()
    assert written_text == test_token_file_data
