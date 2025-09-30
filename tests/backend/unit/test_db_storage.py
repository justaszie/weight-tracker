import datetime as dt

import pytest
from sqlalchemy import func
from sqlmodel import create_engine, select, SQLModel, Session

from app.db_storage import (
    DatabaseStorage,
    DBWeightEntry,
)
from app.project_types import WeightEntry

TEST_DB_CONN_STRING = (
    "postgresql+psycopg2://postgres@localhost:5432/test_weight_tracker"
)


@pytest.fixture
def sample_daily_entries():
    return [
        {"entry_date": dt.date(2025, 8, 18), "weight": 73.0},
        {"entry_date": dt.date(2025, 8, 19), "weight": 72.9},
        {"entry_date": dt.date(2025, 8, 20), "weight": 72.3},
        {"entry_date": dt.date(2025, 8, 21), "weight": 72.7},
        {"entry_date": dt.date(2025, 8, 22), "weight": 72.5},
        {"entry_date": dt.date(2025, 8, 25), "weight": 73.0},
        {"entry_date": dt.date(2025, 8, 26), "weight": 73.6},
        {"entry_date": dt.date(2025, 8, 27), "weight": 73.0},
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


def test_create_weight_entries(storage_empty, sample_daily_entries):
    engine = create_engine(TEST_DB_CONN_STRING)
    with Session(engine) as test_session:
        count = test_session.exec(select(func.count()).select_from(DBWeightEntry)).one()
        assert count == 0

    for entry in sample_daily_entries[:2]:
        storage_empty.create_weight_entry(entry["entry_date"], entry["weight"])

    # Checking that the entries were inserted
    with Session(engine) as test_session:
        results = test_session.exec(select(DBWeightEntry)).all()
        assert len(results) == 2

        for idx, sample_entry in enumerate(sample_daily_entries[:2]):
            assert results[idx].model_dump() == sample_entry


def test_get_weight_entries(storage_sample, sample_daily_entries):
    results = storage_sample.get_weight_entries()
    assert len(results) == len(sample_daily_entries)

    sample_entry = sample_daily_entries[0]
    assert (sample_entry["entry_date"], sample_entry["weight"]) in [
        (entry.entry_date, entry.weight) for entry in results
    ]


def test_get_weight_entry(storage_sample, sample_daily_entries):
    existing_entry = sample_daily_entries[0]
    result = storage_sample.get_weight_entry(existing_entry["entry_date"])

    assert result is not None and existing_entry["weight"] == result.weight


def test_update_entry(storage_sample, sample_daily_entries):
    existing_entry = sample_daily_entries[0]
    updated_entry = {
        "entry_date": existing_entry["entry_date"],
        "weight": 99.9,
    }

    storage_sample.update_weight_entry(**updated_entry)

    engine = create_engine(TEST_DB_CONN_STRING)
    with Session(engine) as session:
        result = session.get(DBWeightEntry, updated_entry["entry_date"])
        assert result is not None
        assert result.weight == updated_entry["weight"]


def test_delete_entry(storage_sample, sample_daily_entries):
    existing_entry = sample_daily_entries[0]
    storage_sample.delete_weight_entry(existing_entry["entry_date"])

    engine = create_engine(TEST_DB_CONN_STRING)
    with Session(engine) as session:
        result = session.get(DBWeightEntry, existing_entry["entry_date"])
        assert result is None


def test_empty_get_weight_entries(storage_empty):
    assert len(storage_empty.get_weight_entries()) == 0


def test_get_nonexistent_weight_entry(storage_sample):
    result = storage_sample.get_weight_entry(dt.date(1900, 1, 1))
    assert result is None


def test_create_duplicate_weight_entry(storage_sample, sample_daily_entries):
    existent_entry = sample_daily_entries[0]

    with pytest.raises(ValueError):
        storage_sample.create_weight_entry(**existent_entry)


def test_update_nonexistent_weight_entry(storage_empty):
    with pytest.raises(ValueError):
        storage_empty.update_weight_entry(entry_date=dt.date(1990, 1, 1), weight=56)


def test_delete_nonexistent_weight_entry(storage_sample):
    with pytest.raises(ValueError):
        storage_sample.delete_weight_entry(entry_date=dt.date(1850, 2, 2))


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
    assert storage_sample.data_refresh_needed() == expected_output
