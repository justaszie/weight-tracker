import datetime as dt
import pytest
from pydantic import TypeAdapter

from app.google_fit import NoCredentialsError
from app.data_integration import (
    DataIntegrationService,
    DataSyncError,
    SourceNoDataError,
    SourceFetchError,
)
from app.file_storage import FileStorage
from app.project_types import WeightEntry


@pytest.fixture
def service(mocker):
    return DataIntegrationService(mocker.Mock(), mocker.Mock())


@pytest.fixture
def sample_raw_data():
    return {"data": {"2020-01-02": 78.56}}


@pytest.fixture
def sample_daily_entries():
    data = [
        {"date": dt.date(2025, 8, 28), "weight": 73.6},
        {"date": dt.date(2025, 8, 29), "weight": 73.6},
        {"date": dt.date(2025, 9, 1), "weight": 73.0},
    ]
    return TypeAdapter(list[WeightEntry]).validate_python(data)


def test_refresh_no_raw_data_found(mocker, service):
    mocker.patch(
        "app.data_integration.DataIntegrationService.convert_to_daily_entries",
        side_effect=SourceNoDataError,
    )

    with pytest.raises(SourceNoDataError):
        service.refresh_weight_entries()

    service.source.get_raw_data.assert_called_once()


@pytest.mark.parametrize(
    "test_entries",
    [
        [
            {"date": dt.date(2025, 8, 28), "weight": 73.6},
            {"date": dt.date(2025, 8, 29), "weight": 73.6},
        ],
        [
            {"date": dt.date(2025, 8, 28), "weight": 73.6},
        ],
        [
            {"date": dt.date(2025, 8, 28), "weight": 70.1},
            {"date": dt.date(2025, 8, 29), "weight": 70.2},
            {"date": dt.date(2025, 9, 1), "weight": 73.0},
        ],
    ],
)
def test_refresh_no_new_data(mocker, service, sample_daily_entries, test_entries):
    test_entries = TypeAdapter(list[WeightEntry]).validate_python(test_entries)
    mocker.patch(
        "app.data_integration.DataIntegrationService.convert_to_daily_entries"
    ).return_value = test_entries
    mocker.patch(
        "app.data_integration.DataIntegrationService.get_existing_weight_entries"
    ).return_value = sample_daily_entries
    mock_store_data = mocker.patch(
        "app.data_integration.DataIntegrationService.store_new_weight_entries"
    )

    new_entries = service.refresh_weight_entries()

    mock_store_data.assert_called_once_with([])
    assert new_entries == []


@pytest.mark.parametrize(
    "test_entries, expected_new_entries",
    [
        (
            [
                {"date": dt.date(2025, 9, 20), "weight": 70.9},
            ],
            [
                {"date": dt.date(2025, 9, 20), "weight": 70.9},
            ],
        ),
        (
            [
                {"date": dt.date(2025, 1, 5), "weight": 70.9},
                {"date": dt.date(2025, 8, 28), "weight": 70.9},
                {"date": dt.date(2025, 8, 29), "weight": 70.9},
                {"date": dt.date(2025, 8, 30), "weight": 72.9},
                {"date": dt.date(2025, 9, 28), "weight": 71.9},
            ],
            [
                {"date": dt.date(2025, 1, 5), "weight": 70.9},
                {"date": dt.date(2025, 8, 30), "weight": 72.9},
                {"date": dt.date(2025, 9, 28), "weight": 71.9},
            ],
        ),
    ],
)
def test_refresh_new_data(
    mocker, service, sample_daily_entries, test_entries, expected_new_entries
):
    test_entries = TypeAdapter(list[WeightEntry]).validate_python(test_entries)
    expected_new_entries = TypeAdapter(list[WeightEntry]).validate_python(
        expected_new_entries
    )

    mocker.patch(
        "app.data_integration.DataIntegrationService.convert_to_daily_entries"
    ).return_value = test_entries
    mocker.patch(
        "app.data_integration.DataIntegrationService.get_existing_weight_entries"
    ).return_value = sample_daily_entries
    mock_store_data = mocker.patch(
        "app.data_integration.DataIntegrationService.store_new_weight_entries"
    )

    new_entries = service.refresh_weight_entries()

    mock_store_data.assert_called_once_with(expected_new_entries)
    assert new_entries == expected_new_entries


def test_refresh_with_store_raw_copy_on(mocker, service):
    mocker.patch("app.data_integration.DataIntegrationService.get_raw_data")
    mocker.patch("app.data_integration.DataIntegrationService.convert_to_daily_entries")
    mocker.patch(
        "app.data_integration.DataIntegrationService.get_existing_weight_entries"
    )
    mocker.patch(
        "app.data_integration.DataIntegrationService.filter_new_weight_entries"
    )
    mocker.patch("app.data_integration.DataIntegrationService.store_new_weight_entries")
    mock_store_raw_copy_fn = mocker.patch(
        "app.data_integration.DataIntegrationService.store_raw_data"
    )
    mock_store_csv_copy_fn = mocker.patch.object(service.storage, "export_to_csv")

    service.refresh_weight_entries(store_csv_copy=False, store_raw_copy=True)

    mock_store_raw_copy_fn.assert_called_once()
    assert not mock_store_csv_copy_fn.called


def test_refresh_with_store_csv_on(mocker, service):
    mocker.patch("app.data_integration.DataIntegrationService.get_raw_data")
    mocker.patch("app.data_integration.DataIntegrationService.convert_to_daily_entries")
    mocker.patch(
        "app.data_integration.DataIntegrationService.get_existing_weight_entries"
    )
    mocker.patch(
        "app.data_integration.DataIntegrationService.filter_new_weight_entries"
    )
    mocker.patch("app.data_integration.DataIntegrationService.store_new_weight_entries")
    mock_store_raw_copy_fn = mocker.patch(
        "app.data_integration.DataIntegrationService.store_raw_data"
    )
    mock_store_csv_copy_fn = mocker.patch.object(service.storage, "export_to_csv")

    service.refresh_weight_entries(store_csv_copy=True, store_raw_copy=False)

    mock_store_csv_copy_fn.assert_called_once()
    assert not mock_store_raw_copy_fn.called


def test_get_raw_data(mocker, service, sample_raw_data):
    mock_source_fetch_fn = mocker.patch.object(service.source, "get_raw_data")
    mock_source_fetch_fn.return_value = sample_raw_data
    assert service.get_raw_data() == sample_raw_data


def test_get_raw_data_credentials_error(mocker, service):
    mock_source_fetch_fn = mocker.patch.object(service.source, "get_raw_data")
    mock_source_fetch_fn.side_effect = NoCredentialsError()

    with pytest.raises(SourceFetchError):
        raw_data = service.get_raw_data()


def test_get_raw_data_other_errors(mocker, service):
    mock_source_fetch_fn = mocker.patch.object(service.source, "get_raw_data")
    mock_source_fetch_fn.side_effect = Exception()

    with pytest.raises(SourceFetchError):
        raw_data = service.get_raw_data()


def test_store_raw_data(mocker, service, sample_raw_data):
    mock_source_fn = mocker.patch.object(service.source, "store_raw_data")
    service.store_raw_data(sample_raw_data)
    mock_source_fn.assert_called_once_with(sample_raw_data)


def test_convert_to_daily_entries(
    mocker, service, sample_raw_data, sample_daily_entries
):
    mock_source_fn = mocker.patch.object(service.source, "convert_to_daily_entries")
    mock_source_fn.return_value = sample_daily_entries

    result = service.convert_to_daily_entries(sample_raw_data)

    mock_source_fn.assert_called_once_with(sample_raw_data)
    assert result == sample_daily_entries


def test_convert_to_daily_entries_empty_dataset(mocker, service):
    mock_source_fn = mocker.patch.object(service.source, "convert_to_daily_entries")
    mock_source_fn.return_value = []
    test_raw_data = {}

    with pytest.raises(SourceNoDataError):
        result = service.convert_to_daily_entries(test_raw_data)

    mock_source_fn.assert_called_once_with(test_raw_data)


def test_get_existing_weight_entries(mocker, service, sample_daily_entries):
    mock_storage_fn = mocker.patch.object(service.storage, "get_weight_entries")
    mock_storage_fn.return_value = sample_daily_entries

    result = service.get_existing_weight_entries()

    mock_storage_fn.assert_called_once()
    assert result == sample_daily_entries


@pytest.mark.parametrize(
    "test_entries, expected_filtered_entries",
    [
        (
            [
                {"date": dt.date(2025, 9, 20), "weight": 70.9},
            ],
            [
                {"date": dt.date(2025, 9, 20), "weight": 70.9},
            ],
        ),
        (
            [
                {"date": dt.date(2025, 8, 28), "weight": 70.9},
                {"date": dt.date(2025, 8, 29), "weight": 70.9},
            ],
            [],
        ),
        (
            [
                {"date": dt.date(2025, 1, 5), "weight": 70.9},
                {"date": dt.date(2025, 8, 28), "weight": 70.9},
                {"date": dt.date(2025, 8, 29), "weight": 70.9},
                {"date": dt.date(2025, 8, 30), "weight": 72.9},
                {"date": dt.date(2025, 9, 28), "weight": 71.9},
            ],
            [
                {"date": dt.date(2025, 1, 5), "weight": 70.9},
                {"date": dt.date(2025, 8, 30), "weight": 72.9},
                {"date": dt.date(2025, 9, 28), "weight": 71.9},
            ],
        ),
    ],
)
def test_filter_new_weight_entries(
    mocker, service, test_entries, sample_daily_entries, expected_filtered_entries
):

    mocker.patch.object(service, "get_existing_weight_entries").return_value = (
        sample_daily_entries
    )

    test_entries = TypeAdapter(list[WeightEntry]).validate_python(test_entries)
    filtered_new_entries = service.filter_new_weight_entries(test_entries)

    expected_filtered_entries = TypeAdapter(list[WeightEntry]).validate_python(
        expected_filtered_entries
    )
    assert filtered_new_entries == expected_filtered_entries


def test_store_new_weight_entries(mocker, service, sample_daily_entries):
    mock_storage_fn = mocker.patch.object(service.storage, "create_weight_entry")
    sample_entry = sample_daily_entries[0]
    sample_entry_date, sample_entry_weight =  (sample_entry.date, sample_entry.weight)

    service.store_new_weight_entries(sample_daily_entries)

    assert mock_storage_fn.call_count == len(sample_daily_entries)
    mock_storage_fn.assert_any_call(sample_entry_date, sample_entry_weight)


def test_store_new_weight_entries_with_persist_command(mocker, sample_daily_entries):
    service = DataIntegrationService(FileStorage(), mocker.Mock())

    mock_storage_fn = mocker.patch.object(service.storage, "create_weight_entry")
    mock_persist_fn = mocker.patch.object(service.storage, "save")

    service.store_new_weight_entries(sample_daily_entries)

    mock_persist_fn.assert_called_once()
