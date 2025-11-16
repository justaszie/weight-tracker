import datetime as dt
import json

import pytest
from pydantic import TypeAdapter

# from app.mfp import (
#     MyFitnessPalClient,
#     DEFAULT_LOOKBACK_YEARS,
# )
from app.project_types import WeightEntry


@pytest.fixture
def client():
    return MyFitnessPalClient()


@pytest.fixture
def sample_raw_data():
    return {
        dt.date(2025, 1, 2): 72.562,
        dt.date(2025, 2, 15): 70.2,
        dt.date(2025, 5, 28): 80.1111,
        dt.date(2025, 9, 5): 75.4,
    }


@pytest.mark.skip
def test_get_raw_data_default_date_from(mocker, client, sample_raw_data):
    mocker.patch("app.mfp.browser_cookie3.chrome")

    mock_mfp_client = mocker.patch("app.mfp.myfitnesspal.Client").return_value
    mock_get_measurements = mocker.patch.object(
        mock_mfp_client, "get_measurements", return_value=sample_raw_data
    )

    today_timestamp = dt.datetime.now()
    mocker.patch("app.mfp.dt.datetime").now.return_value = today_timestamp
    expected_default_date_from = (
        today_timestamp - dt.timedelta(days=365 * DEFAULT_LOOKBACK_YEARS)
    ).date()

    raw_data = client.get_raw_data()

    mock_get_measurements.assert_called_once_with(
        "Weight", lower_bound=expected_default_date_from
    )
    assert raw_data == sample_raw_data


@pytest.mark.skip
def test_get_raw_data_provided_date_from(mocker, client, sample_raw_data):
    mocker.patch("app.mfp.browser_cookie3.chrome")

    mock_mfp_client = mocker.patch("app.mfp.myfitnesspal.Client").return_value
    mock_get_measurements = mocker.patch.object(
        mock_mfp_client, "get_measurements", return_value=sample_raw_data
    )

    test_date_from = "2024-12-01"
    raw_data = client.get_raw_data(date_from=test_date_from)

    mock_get_measurements.assert_called_once_with(
        "Weight", lower_bound=dt.date.fromisoformat(test_date_from)
    )
    assert raw_data == sample_raw_data


@pytest.mark.skip
def test_get_raw_data_no_data(mocker, client):
    mocker.patch("app.mfp.browser_cookie3.chrome")

    mock_mfp_client = mocker.patch("app.mfp.myfitnesspal.Client").return_value
    mock_get_measurements = mocker.patch.object(
        mock_mfp_client, "get_measurements", return_value={}
    )

    raw_data = client.get_raw_data()

    assert raw_data == {}


@pytest.mark.skip
def test_convert_to_daily_entries(client, sample_raw_data):
    expected_return = TypeAdapter(list[WeightEntry]).validate_python(
        [
            {
                "entry_date": dt.date(2025, 1, 2),
                "weight": 72.56,
            },
            {
                "entry_date": dt.date(2025, 2, 15),
                "weight": 70.2,
            },
            {
                "entry_date": dt.date(2025, 5, 28),
                "weight": 80.11,
            },
            {
                "entry_date": dt.date(2025, 9, 5),
                "weight": 75.4,
            },
        ]
    )
    assert client.convert_to_daily_entries(sample_raw_data) == expected_return


@pytest.mark.skip
def test_convert_to_daily_entries_empty_dataset(mocker, client):
    assert client.convert_to_daily_entries({}) == []


@pytest.mark.skip
def test_store_raw_data(mocker, client, sample_raw_data, tmp_path):
    test_file = tmp_path / "test_raw_data.json"
    mocker.patch("app.mfp.RAW_DATA_FILE_PATH", test_file)

    expected_stored_format = json.dumps(
        {
            "2025-01-02": 72.562,
            "2025-02-15": 70.2,
            "2025-05-28": 80.1111,
            "2025-09-05": 75.4,
        }
    )

    client.store_raw_data(sample_raw_data)

    assert test_file.exists()
    written_text = test_file.read_text()
    assert written_text == expected_stored_format


@pytest.mark.skip
def test_store_raw_data_empty_dataset(mocker, client, tmp_path):
    test_file = tmp_path / "test_raw_data.json"
    mocker.patch("app.mfp.RAW_DATA_FILE_PATH", test_file)
    empty_dataset = {}
    client.store_raw_data(empty_dataset)

    assert test_file.exists()
    assert test_file.read_text() == "{}"
