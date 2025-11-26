import copy
import datetime as dt
import json
from uuid import UUID

import pytest
from google.oauth2.credentials import Credentials
from sqlalchemy import func
from sqlmodel import create_engine, select, SQLModel, Session

from app.db_storage import (
    DatabaseStorage,
    DBWeightEntry,
    DBGoogleCredentials,
)
from app.project_types import WeightEntry

TEST_DB_CONN_STRING = (
    "postgresql+psycopg2://postgres@localhost:5432/test_weight_tracker"
)
TEST_USER_ID = UUID("3760183f-61fa-4ee1-badf-2668fbec152d")
RANDOM_UUID = UUID("5ebcce4b-e597-406e-9d93-8de7072bbc34")


@pytest.fixture
def valid_google_creds():
    return Credentials(
        token="abc123",
        refresh_token="dae/",
        client_id="client1",
        client_secret="secret1",
        scopes=["read", "write", "delete"],
        token_uri="https://url.sample",
        expiry=dt.datetime.fromisoformat("2030-01-01"),
    )


@pytest.fixture
def incomplete_google_creds():
    return Credentials(
        token="abc123",
        scopes=["read", "write", "delete"],
        token_uri="https://url.sample",
        expiry=dt.datetime.fromisoformat("2030-01-01"),
    )


@pytest.fixture
def sample_daily_entries():
    return [  # type: ignore
        {"entry_date": dt.date(2025, 8, 18), "weight": 73.0, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 19), "weight": 72.9, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 20), "weight": 72.3, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 21), "weight": 72.7, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 22), "weight": 72.5, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 25), "weight": 73.0, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 26), "weight": 73.6, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 27), "weight": 73.0, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 28), "weight": 73.6, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 29), "weight": 73.6, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 30), "weight": 73.5, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 9, 1), "weight": 73, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 9, 2), "weight": 72, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 9, 3), "weight": 72.5, "user_id": TEST_USER_ID},
        {"entry_date": dt.date(2025, 8, 30), "weight": 73.5, "user_id": RANDOM_UUID},
        {"entry_date": dt.date(2025, 8, 31), "weight": 73.5, "user_id": RANDOM_UUID},
        {"entry_date": dt.date(2025, 9, 1), "weight": 73, "user_id": RANDOM_UUID},
        {"entry_date": dt.date(2025, 9, 2), "weight": 72, "user_id": RANDOM_UUID},
        {"entry_date": dt.date(2025, 9, 3), "weight": 72.5, "user_id": RANDOM_UUID},
    ]


@pytest.fixture(autouse=True)
def setup_env_variables(monkeypatch):
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


@pytest.fixture
def storage_with_creds(valid_google_creds):
    engine = create_engine(TEST_DB_CONN_STRING)
    SQLModel.metadata.create_all(engine)
    try:
        with Session(engine) as test_session:
            creds_entry = DBGoogleCredentials.from_credentials_object(
                TEST_USER_ID, valid_google_creds
            )
            test_session.add(creds_entry)
            test_session.commit()
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


def test_create_weight_entries(storage_empty, sample_daily_entries):
    engine = create_engine(TEST_DB_CONN_STRING)
    with Session(engine) as test_session:
        count = test_session.exec(select(func.count()).select_from(DBWeightEntry)).one()
        assert count == 0

    test_user_daily_entries = [
        WeightEntry.model_validate(entry)
        for entry in sample_daily_entries
        if entry["user_id"] == TEST_USER_ID
    ][:5]
    storage_empty.create_weight_entries(test_user_daily_entries)

    # Checking that the entries were inserted
    with Session(engine) as test_session:
        results = test_session.exec(select(DBWeightEntry)).all()
        assert len(results) == 5

        for idx, sample_entry in enumerate(test_user_daily_entries[:5]):
            assert results[idx].model_dump() == sample_entry.model_dump()


@pytest.mark.parametrize(
    "user_id, date, weight",
    [
        (TEST_USER_ID, dt.date(2025, 9, 4), 76),
        (TEST_USER_ID, dt.date(2025, 9, 5), 74.5),
        (TEST_USER_ID, dt.date(2025, 8, 31), 73.5),
    ],
)
def test_create_weight_entry(storage_sample, user_id, date, weight) -> None:
    engine = create_engine(TEST_DB_CONN_STRING)

    count_before_create = len(storage_sample.get_weight_entries(user_id))
    storage_sample.create_weight_entry(user_id, date, weight)
    assert len(storage_sample.get_weight_entries(user_id)) == count_before_create + 1

    expected_entry_after_creation = DBWeightEntry.model_validate(
        {
            "entry_date": date,
            "weight": weight,
            "user_id": user_id,
        }
    )

    with Session(engine) as test_session:
        result = test_session.get(DBWeightEntry, (user_id, date))
        assert result == expected_entry_after_creation


def test_get_weight_entries(storage_sample, sample_daily_entries):
    expected_count = len(
        [entry for entry in sample_daily_entries if entry["user_id"] == TEST_USER_ID]
    )
    results = storage_sample.get_weight_entries(TEST_USER_ID)
    assert len(results) == expected_count

    sample_entry = sample_daily_entries[0]
    assert (
        sample_entry["user_id"],
        sample_entry["entry_date"],
        sample_entry["weight"],
    ) in [(entry.user_id, entry.entry_date, entry.weight) for entry in results]


def test_get_weight_entry(storage_sample, sample_daily_entries):
    existing_entry = sample_daily_entries[0]
    result = storage_sample.get_weight_entry(
        existing_entry["user_id"], existing_entry["entry_date"]
    )

    assert result is not None and existing_entry["weight"] == result.weight


def test_update_entry(storage_sample, sample_daily_entries):
    existing_entry = sample_daily_entries[0]
    updated_entry = {
        "user_id": existing_entry["user_id"],
        "entry_date": existing_entry["entry_date"],
        "weight": 99.9,
    }

    storage_sample.update_weight_entry(**updated_entry)

    engine = create_engine(TEST_DB_CONN_STRING)
    with Session(engine) as session:
        result = session.get(
            DBWeightEntry, (updated_entry["user_id"], updated_entry["entry_date"])
        )
        assert result is not None
        assert result.weight == updated_entry["weight"]


def test_delete_entry(storage_sample, sample_daily_entries):
    existing_entry = sample_daily_entries[0]
    storage_sample.delete_weight_entry(
        existing_entry["user_id"], existing_entry["entry_date"]
    )

    engine = create_engine(TEST_DB_CONN_STRING)
    with Session(engine) as session:
        result = session.get(
            DBWeightEntry, (existing_entry["user_id"], existing_entry["entry_date"])
        )
        assert result is None


def test_empty_get_weight_entries(storage_empty):
    assert len(storage_empty.get_weight_entries(TEST_USER_ID)) == 0


def test_get_nonexistent_weight_entry(storage_sample):
    result = storage_sample.get_weight_entry(TEST_USER_ID, dt.date(1900, 1, 1))
    assert result is None


def test_create_duplicate_weight_entry(storage_sample, sample_daily_entries):
    existent_entry = sample_daily_entries[0]

    with pytest.raises(ValueError):
        storage_sample.create_weight_entry(**existent_entry)


def test_update_nonexistent_weight_entry(storage_empty):
    with pytest.raises(ValueError):
        storage_empty.update_weight_entry(
            TEST_USER_ID, entry_date=dt.date(1990, 1, 1), weight=56
        )


def test_delete_nonexistent_weight_entry(storage_sample):
    with pytest.raises(ValueError):
        storage_sample.delete_weight_entry(TEST_USER_ID, entry_date=dt.date(1850, 2, 2))


@pytest.mark.parametrize(
    "test_case, expected_output", [("outdated_data", True), ("data_up_to_date", False)]
)
def test_data_refresh_needed(
    mocker, test_case, expected_output, storage_sample, sample_daily_entries
):
    latest_date = sorted(
        sample_daily_entries, key=lambda entry: entry["entry_date"], reverse=True
    )[0]["entry_date"]
    if test_case == "outdated_data":
        mock_today_date = latest_date + dt.timedelta(days=1)

    else:
        mock_today_date = latest_date

    mocker.patch("app.db_storage.dt").date.today.return_value = mock_today_date
    assert storage_sample.data_refresh_needed(TEST_USER_ID) == expected_output


def test_valid_creds_db_entry_to_credentials_object(monkeypatch):
    test_creds_db_entry = DBGoogleCredentials(
        token="abc123",
        refresh_token="dae/",
        scopes=json.dumps(["read", "write", "delete"]),
        token_uri="https://url.sample",
        expiry=dt.datetime.fromisoformat("2030-01-01"),
    )
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client1")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret2")

    result = test_creds_db_entry.to_credentials_object()

    assert isinstance(result, Credentials) and result.token and result.refresh_token


def test_creds_db_entry_to_credentials_object_invalid(monkeypatch):
    test_creds_db_entry = DBGoogleCredentials(
        scopes="abc",
        token_uri="https://url.sample",
        expiry=dt.datetime.fromisoformat("2030-01-01"),
    )
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client1")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret2")

    with pytest.raises(ValueError):
        result = test_creds_db_entry.to_credentials_object()


def test_creds_db_entry_to_credentials_object_missing_config(monkeypatch):
    test_creds_db_entry = DBGoogleCredentials(
        token="abc123",
        refresh_token="dae/",
        scopes=json.dumps(["read", "write", "delete"]),
        token_uri="https://url.sample",
        expiry=dt.datetime.fromisoformat("2030-01-01"),
    )
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)

    with pytest.raises(KeyError):
        result = test_creds_db_entry.to_credentials_object()


def test_creds_to_db_entry(valid_google_creds):
    result = DBGoogleCredentials.from_credentials_object(
        TEST_USER_ID, valid_google_creds
    )
    assert (
        isinstance(result, DBGoogleCredentials)
        and result.token == valid_google_creds.token
        and result.refresh_token == valid_google_creds.refresh_token
    )


def test_store_credentials_new_user(storage_empty, valid_google_creds):
    storage_empty.store_google_credentials(TEST_USER_ID, valid_google_creds)

    engine = create_engine(TEST_DB_CONN_STRING)
    with Session(engine) as test_session:
        inserted_creds = test_session.get(DBGoogleCredentials, TEST_USER_ID)
        assert (
            inserted_creds.token == valid_google_creds.token
            and inserted_creds.refresh_token == valid_google_creds.refresh_token
        )


def test_store_invalid_credentials(storage_empty, incomplete_google_creds):
    with pytest.raises(Exception):
        storage_empty.store_google_credentials(TEST_USER_ID, incomplete_google_creds)

    engine = create_engine(TEST_DB_CONN_STRING)
    with Session(engine) as test_session:
        inserted_creds = test_session.get(DBGoogleCredentials, TEST_USER_ID)
        assert inserted_creds is None


def test_store_credentials_existing_user(storage_with_creds, valid_google_creds):
    new_creds = copy.deepcopy(valid_google_creds)
    new_creds.token = "dee123"
    new_creds.expiry = dt.datetime.fromisoformat("2032-01-02")

    storage_with_creds.store_google_credentials(TEST_USER_ID, new_creds)

    engine = create_engine(TEST_DB_CONN_STRING)
    with Session(engine) as test_session:
        updated_creds = test_session.get(DBGoogleCredentials, TEST_USER_ID)
        assert (
            updated_creds.token == new_creds.token
            and updated_creds.refresh_token == new_creds.refresh_token
        )


def test_load_valid_credentials(storage_with_creds, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "abc123")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "ddd11")
    result = storage_with_creds.load_google_credentials(TEST_USER_ID)
    assert (
        isinstance(result, Credentials)
        and hasattr(result, "token")
        and hasattr(result, "refresh_token")
    )


def test_load_nonexisting_credentials(storage_empty, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "abc123")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "ddd11")
    result = storage_empty.load_google_credentials(TEST_USER_ID)
    assert result is None
