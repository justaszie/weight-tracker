import datetime as dt
import json
import pytest

from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.api import get_data_storage
from app.file_storage import FileStorage
from app.google_fit import GoogleFitClient
from app.main import app
from app.mfp import MyFitnessPalClient
from app.project_types import WeightEntry

TEST_DB_CONN_STRING = (
    "postgresql+psycopg2://postgres@localhost:5432/test_weight_tracker"
)


@pytest.fixture
def sample_daily_entries():
    return [
        {"entry_date": dt.date(2025, 2, 12), "weight": 73.0},
        {"entry_date": dt.date(2025, 3, 2), "weight": 73.0},
        {"entry_date": dt.date(2025, 8, 18), "weight": 73.0},
        {"entry_date": dt.date(2025, 8, 19), "weight": 72.9},
        {"entry_date": dt.date(2025, 8, 20), "weight": 72.3},
        {"entry_date": dt.date(2025, 8, 21), "weight": 72.7},
        {"entry_date": dt.date(2025, 8, 22), "weight": 72.5},
        {"entry_date": dt.date(2025, 8, 25), "weight": 73.0},
        {"entry_date": dt.date(2025, 8, 28), "weight": 73.6},
        {"entry_date": dt.date(2025, 8, 29), "weight": 73.6},
        {"entry_date": dt.date(2025, 8, 30), "weight": 73.5},
        {"entry_date": dt.date(2025, 9, 1), "weight": 73},
        {"entry_date": dt.date(2025, 9, 2), "weight": 72},
        {"entry_date": dt.date(2025, 9, 3), "weight": 72.5},
    ]


@pytest.fixture(autouse=True)
def setup_env_variables(monkeypatch):
    monkeypatch.setenv("DB_CONNECTION_STRING", TEST_DB_CONN_STRING)


def _insert_daily_entries(engine, daily_entries):
    entries_as_sqlmodels = [
        DBWeightEntry.model_validate(entry, from_attributes=True)
        for entry in daily_entries
    ]
    with Session(engine) as test_session:
        test_session.add_all(entries_as_sqlmodels)
        test_session.commit()


def _get_test_file_storage(mocker, sample_daily_entries, tmp_path):
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


@pytest.fixture(params=["file", "database"])
def get_test_storage(request, mocker, sample_daily_entries, tmp_path):
    storage_type = request.param

    if storage_type == "file":
        yield _get_test_file_storage(mocker, sample_daily_entries, tmp_path)
    elif storage_type == "database":
        engine = create_engine(TEST_DB_CONN_STRING)
        SQLModel.metadata.create_all(engine)
        try:
            _insert_daily_entries(engine, sample_daily_entries)
            yield DatabaseStorage()
        finally:
            SQLModel.metadata.drop_all(engine)


@pytest.fixture
def get_test_storage(mocker, sample_daily_entries, tmp_path) -> FileStorage:
    return _get_test_file_storage(mocker, sample_daily_entries, tmp_path)


@pytest.fixture
def client_with_storage(get_test_storage):
    app.dependency_overrides[get_data_storage] = lambda: get_test_storage
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def mock_gfit_client(mocker, tmp_path):
    raw_data_file_path = tmp_path / "test_raw_data.json"
    mocker.patch("app.google_fit.RAW_DATA_FILE_PATH", raw_data_file_path)
    client = GoogleFitClient()
    return client


@pytest.fixture
def mock_mfp_client(mocker, tmp_path):
    raw_data_file_path = tmp_path / "test_raw_data.json"
    mocker.patch("app.mfp.RAW_DATA_FILE_PATH", raw_data_file_path)
    client = MyFitnessPalClient()
    return client


def test_gfit_sync_new_entries(
    mocker, client_with_storage, sample_daily_entries, mock_gfit_client
):
    test_raw_dataset = {
        "minStartTimeNs": "0",
        "maxEndTimeNs": "1757050801266618112",
        "dataSourceId": "derived:com.google.weight:com.google.android.gms:merge_weight",
        "point": [
            {
                "startTimeNanos": "1740873600000000000",  # 2025-03-02
                "endTimeNanos": "1740873600000000000",
                "dataTypeName": "com.google.weight",
                "originDataSourceId": "raw:com.google.weight:com.google.android.apps.fitness:user_input",
                "value": [{"fpVal": 73.0, "mapVal": []}],
                "modifiedTimeMillis": "1740873618250",
            },
            {
                "startTimeNanos": "1740960000000000000",  # 2025-03-03
                "endTimeNanos": "1740960000000000000",
                "dataTypeName": "com.google.weight",
                "originDataSourceId": "raw:com.google.weight:com.google.android.apps.fitness:user_input",
                "value": [{"fpVal": 72.9, "mapVal": []}],
                "modifiedTimeMillis": "1740960018250",
            },
            {
                "startTimeNanos": "1755907200000000000",  # 2025-08-23
                "endTimeNanos": "1755907200000000000",
                "dataTypeName": "com.google.weight",
                "originDataSourceId": "raw:com.google.weight:com.google.android.apps.fitness:user_input",
                "value": [{"fpVal": 72.8, "mapVal": []}],
                "modifiedTimeMillis": "1755907218250",
            },
            {
                "startTimeNanos": "1755993600000000000",  # 2025-08-24
                "endTimeNanos": "1755993600000000000",
                "dataTypeName": "com.google.weight",
                "originDataSourceId": "raw:com.google.weight:com.google.android.apps.fitness:user_input",
                "value": [{"fpVal": 72.7, "mapVal": []}],
                "modifiedTimeMillis": "1755993618250",
            },
            {
                "startTimeNanos": "1756080000000000000",  # 2025-08-25
                "endTimeNanos": "1756080000000000000",
                "dataTypeName": "com.google.weight",
                "originDataSourceId": "raw:com.google.weight:com.google.android.apps.fitness:user_input",
                "value": [{"fpVal": 72.6, "mapVal": []}],
                "modifiedTimeMillis": "1756080018250",
            },
            {
                "startTimeNanos": "1756166400000000000",  # 2025-08-26
                "endTimeNanos": "1756166400000000000",
                "dataTypeName": "com.google.weight",
                "originDataSourceId": "raw:com.google.weight:com.google.android.apps.fitness:user_input",
                "value": [{"fpVal": 72.5, "mapVal": []}],
                "modifiedTimeMillis": "1756166418250",
            },
            {
                "startTimeNanos": "1756986900000000000",  # 2025-09-04
                "endTimeNanos": "1756986900000000000",
                "dataTypeName": "com.google.weight",
                "originDataSourceId": "raw:com.google.weight:com.google.android.apps.fitness:user_input",
                "value": [{"fpVal": 72.4, "mapVal": []}],
                "modifiedTimeMillis": "1756986900000",
            },
        ],
    }

    mocker.patch("app.api.get_data_source_client").return_value = mock_gfit_client
    mocker.patch.object(
        mock_gfit_client, "get_raw_data"
    ).return_value = test_raw_dataset

    response = client_with_storage.post(
        "/api/v1/sync-data", json={"data_source": "gfit"}
    )
    response_body = response.json()

    assert response.status_code == 200

    # In the test gfit raw data there are 5 new entries
    assert response_body["new_entries_count"] == 5

    response = client_with_storage.get("/api/v1/daily-entries")
    updated_daily_entries = response.json()

    assert response.status_code == 200
    assert len(updated_daily_entries) == len(sample_daily_entries) + 5
    print(updated_daily_entries)
    new_entry = [
        entry for entry in updated_daily_entries if entry["entry_date"] == "2025-09-04"
    ][0]
    assert new_entry["weight"] == 72.4

    # The sync-data should not update existing entries' weight value
    response = client_with_storage.get(
        "/api/v1/daily-entries",
        params={
            "date_from": "2025-08-25",
            "date_to": "2025-08-25",
        },
    )

    assert response.status_code == 200
    assert response.json()[0]["weight"] == 73.0


def test_mfp_sync_new_entries(
    mocker, client_with_storage, sample_daily_entries, mock_mfp_client
):
    test_raw_dataset = {
        "2025-03-02": 70.8,
        "2025-03-03": 70.4,
        "2025-08-23": 70.5,
        "2025-08-24": 70.2,
        "2025-08-25": 70.2,
        "2025-08-26": 70.2,
        "2025-09-04": 70.2,
    }

    mocker.patch("app.api.get_data_source_client").return_value = mock_mfp_client
    mocker.patch.object(mock_mfp_client, "get_raw_data").return_value = test_raw_dataset

    response = client_with_storage.post(
        "/api/v1/sync-data", json={"data_source": "gfit"}
    )
    response_body = response.json()

    assert response.status_code == 200

    # In the test gfit raw data there are 5 new entries
    assert response_body["new_entries_count"] == 5

    response = client_with_storage.get("/api/v1/daily-entries")
    updated_daily_entries = response.json()

    assert response.status_code == 200
    assert len(updated_daily_entries) == len(sample_daily_entries) + 5
    new_entry = [
        entry for entry in updated_daily_entries if entry["entry_date"] == "2025-09-04"
    ][0]
    assert new_entry["weight"] == 70.2

    # The sync-data should not update existing entries' weight value
    response = client_with_storage.get(
        "/api/v1/daily-entries",
        params={
            "date_from": "2025-08-25",
            "date_to": "2025-08-25",
        },
    )

    assert response.status_code == 200
    assert response.json()[0]["weight"] == 73.0
