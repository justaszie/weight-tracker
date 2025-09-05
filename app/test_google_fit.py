import datetime as dt
import json
import pytest

from google_fit import GoogleFitClient, NoCredentialsError

"""
 def __init__(self, creds: Credentials | None) -> None
#         # Stores credentials; does not validate them.

#     def get_raw_data(
#         self,
#         date_from: str | None = None,
#         date_to: str | None = None
#     ) -> Any
#         # Calls Google Fitness API, returns raw dataset dict or [] if empty.
#         # Currently ignores date_from/date_to (full range fetch).
#
#     def store_raw_data(self, raw_data: Any) -> None
#         # Persists raw JSON to RAW_DATA_FILE_PATH (creates dirs).
#
#     def convert_to_daily_entries(self, raw_data: Any) -> list[DailyWeightEntry]
#         # Normalizes raw API data into [{'date': date, 'weight': float}, ...]
#         # Keeps last weight per day, filters weight outliers (50 < w < 100).
#
#     def _is_empty_dataset(self, dataset: Any) -> bool
#         # Internal helper: True if dataset missing 'point' or empty.
 """


def test_get_raw_data_no_creds():
    client = GoogleFitClient()
    with pytest.raises(NoCredentialsError):
        assert client.get_raw_data()


def test_get_raw_data(mocker, sample_raw_dataset):
    # Setting up test parameters to the multiple function calls
    date_from_ns_timestamp = 0
    test_now_timestamp = dt.datetime.now()
    tomorrow: dt.datetime = test_now_timestamp + dt.timedelta(days=1)
    date_to_ns_timestamp = int(tomorrow.timestamp() * 1e9)
    user_id_param = "me"
    data_source_id_param = (
        "derived:com.google.weight:com.google.android.gms:merge_weight"
    )
    dataset_id_param = f"{date_from_ns_timestamp}-{date_to_ns_timestamp}"

    get_requets_params = {
        "userId": user_id_param,
        "dataSourceId": data_source_id_param,
        "datasetId": dataset_id_param,
    }

    # Mocking the datetime to compare fixed param values
    mocker.patch("google_fit.dt.datetime").now.return_value = test_now_timestamp

    # Mocking the 3rd party function objects
    mock_service_build_fn = mocker.patch("google_fit.build")
    mock_service = mock_service_build_fn.return_value

    mock_get_request_fn = mock_service.users().dataSources().datasets().get
    mock_request = mock_get_request_fn.return_value

    mock_execute_fn = mock_request.execute
    mock_execute_fn.return_value = sample_raw_dataset

    # Run the actual code
    credentials = "testcreds"
    client = GoogleFitClient(credentials)
    result = client.get_raw_data()

    # Testing the function return value and the 3rd party function calls
    mock_service_build_fn.assert_called_once_with(
        "fitness", "v1", credentials=credentials
    )
    mock_get_request_fn.assert_called_once_with(**get_requets_params)
    mock_execute_fn.assert_called_once()
    assert result == sample_raw_dataset


def test_get_empty_raw_dataset(mocker, empty_raw_dataset):
    mock_service = mocker.patch("google_fit.build").return_value
    mock_execute_fn = (
        mock_service.users().dataSources().datasets().get.return_value.execute
    )
    mock_execute_fn.return_value = empty_raw_dataset

    client = GoogleFitClient("testcreds")
    result = client.get_raw_data()

    mock_execute_fn.assert_called_once()
    assert result == []


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
                "value": [{"fpVal": 73.0999984741211, "mapVal": []}],
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
