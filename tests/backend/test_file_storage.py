# type: ignore

import datetime as dt
import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from app.file_storage import FileStorage
from app.project_types import WeightEntry


class TestWeightStorageUsingFile:
    def test_load_weights_from_nonexistent_file(self, mocker):
        mock_file_path = Path(__file__).resolve().parent / "non_existing.json"
        mocker.patch(
            "app.file_storage.FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH",
            new=mock_file_path,
        )
        entries = FileStorage._load_weights_from_file()
        assert entries == []
        if not Path(mock_file_path).is_file():
            print("Expected the storage file to be created but it was not")
            assert False

        if mock_file_path.exists():
            mock_file_path.unlink(missing_ok=True)

    def test_load_weights_from_wrong_format_file(self, mocker, tmp_path):
        test_file_data = ""
        tmp_path = tmp_path / "test_data.json"
        mocker.patch(
            "app.file_storage.FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH", new=tmp_path
        )
        tmp_path.write_text(test_file_data)

        with pytest.raises(ValidationError):
            FileStorage._load_weights_from_file()

    def test_load_weights_from_file(self, mocker, tmp_path):
        # 1. Mock the filepath to the tmp_path value
        tmp_path = tmp_path / "test_data.json"
        mocker.patch(
            "app.file_storage.FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH", new=tmp_path
        )
        # 2. dump test data to the temp test file
        test_file_data = json.dumps(
            [
                {"date": "2025-08-28", "weight": 73.6},
                {"date": "2025-08-29", "weight": 73.6},
                {"date": "2025-08-30", "weight": 73.5},
                {"date": "2025-09-01", "weight": 73.0},
            ]
        )
        tmp_path.write_text(test_file_data)

        actual_entries = FileStorage._load_weights_from_file()

        expected_entries = TypeAdapter(list[WeightEntry]).validate_python(
            [
                {"date": dt.date(2025, 8, 28), "weight": 73.6},
                {"date": dt.date(2025, 8, 29), "weight": 73.6},
                {"date": dt.date(2025, 8, 30), "weight": 73.5},
                {"date": dt.date(2025, 9, 1), "weight": 73.0},
            ]
        )
        assert actual_entries == expected_entries


class TestWeightStorageProtocol:
    @pytest.fixture
    def sample_weight_entries(self):
        data = [
            {"date": dt.date(2025, 8, 28), "weight": 73.6},
            {"date": dt.date(2025, 8, 29), "weight": 73.6},
            {"date": dt.date(2025, 8, 30), "weight": 73.5},
            {"date": dt.date(2025, 9, 1), "weight": 73.0},
        ]
        return TypeAdapter(list[WeightEntry]).validate_python(data)

    @pytest.fixture
    def mock_load_data_function(self, mocker):
        return mocker.patch("app.file_storage.FileStorage._load_weights_from_file")

    @pytest.fixture
    def sample_storage(self, mocker, mock_load_data_function, sample_weight_entries):
        mock_load_data_function.return_value = sample_weight_entries
        return FileStorage()

    @pytest.fixture
    def empty_storage(self, mocker, mock_load_data_function):
        mock_load_data_function.return_value = []
        return FileStorage()

    def test_get_weight_entries(self, sample_storage, sample_weight_entries):
        assert sample_storage.get_weight_entries() == sample_weight_entries

    def test_get_existing_weight_entry(self, sample_storage):
        expected = {"date": dt.date(2025, 8, 28), "weight": 73.6}
        expected = WeightEntry.model_validate(expected)
        assert sample_storage.get_weight_entry(date=dt.date(2025, 8, 28)) == expected

    def test_get_nonexistent_weight_entry(self, sample_storage):
        assert sample_storage.get_weight_entry(date=dt.date(2027, 1, 28)) == None

    @pytest.mark.parametrize(
        "date, weight",
        [
            (dt.date(2025, 9, 2), 76),
            (dt.date(2025, 9, 3), 74.5),
        ],
    )
    def test_create_weight_entry(self, sample_storage, date, weight) -> None:
        count_before_create = len(sample_storage.get_weight_entries())
        sample_storage.create_weight_entry(date, weight)
        assert len(sample_storage.get_weight_entries()) == count_before_create + 1

        expected_entry_after_creation = WeightEntry.model_validate(
            {
                "date": date,
                "weight": weight,
            }
        )
        assert (
            sample_storage.get_weight_entry(date=date) == expected_entry_after_creation
        )

    def test_create_duplicate_weight_entry(self, sample_storage):
        existing_entries = sample_storage.get_weight_entries()
        assert len(existing_entries) > 0

        sample_entry = existing_entries[0]
        date = sample_entry.date
        weight = 99.9

        count_before_create = len(sample_storage.get_weight_entries())
        with pytest.raises(ValueError):
            sample_storage.create_weight_entry(date, weight)

        assert len(sample_storage.get_weight_entries()) == count_before_create

    @pytest.mark.parametrize(
        "date, weight",
        [
            (dt.date(2025, 8, 28), 72.5),
            (dt.date(2025, 8, 28), 71),
        ],
    )
    def test_update_valid_weight_entry(self, sample_storage, date, weight):
        sample_storage.update_weight_entry(date, weight)
        updated_entry = sample_storage.get_weight_entry(date=date)

        new_weight = updated_entry.weight
        assert new_weight == weight

    def test_update_nonexistent_weight_entry(self, sample_storage):
        date = dt.date(1990, 1, 1)
        weight = 98.1
        assert sample_storage.get_weight_entry(date) == None
        with pytest.raises(ValueError):
            sample_storage.update_weight_entry(date, weight)

    def test_delete_existing_weight_entry(self, sample_storage):
        entries = sample_storage.get_weight_entries()
        count_before = len(entries)
        assert count_before > 0

        sample_entry = entries[0]
        date = sample_entry.date

        sample_storage.delete_weight_entry(date=date)
        assert len(sample_storage.get_weight_entries()) == count_before - 1
        assert sample_storage.get_weight_entry(date) == None

    def test_delete_all_weight_entries(self, sample_storage):
        dates = [entry.date for entry in sample_storage.get_weight_entries()]
        assert len(sample_storage.get_weight_entries()) == len(dates)

        for date in dates:
            sample_storage.delete_weight_entry(date)

        assert len(sample_storage.get_weight_entries()) == 0

    def test_delete_nonexisting_weight_entry(self, sample_storage):
        date = dt.date(1990, 1, 1)
        count_before = len(sample_storage.get_weight_entries())
        assert sample_storage.get_weight_entry(date) == None
        with pytest.raises(ValueError):
            sample_storage.delete_weight_entry(date)
        assert len(sample_storage.get_weight_entries()) == count_before

    @pytest.mark.parametrize(
        "dates_in_db, expected_output",
        [
            ([dt.date.today() - dt.timedelta(days=1), dt.date.today()], False),
            (
                [
                    dt.date.today() - dt.timedelta(days=2),
                    dt.date.today() - dt.timedelta(days=1),
                ],
                True,
            ),
            (
                [
                    dt.date.today() - dt.timedelta(days=3),
                    dt.date.today() - dt.timedelta(days=2),
                ],
                True,
            ),
            ([dt.date.today() - dt.timedelta(days=120)], True),
        ],
    )
    def test_data_refresh_needed(self, empty_storage, dates_in_db, expected_output):
        weight = 80.2
        for date in dates_in_db:
            empty_storage.create_weight_entry(date=date, weight=weight)
        assert len(empty_storage.get_weight_entries()) == len(dates_in_db)

        assert empty_storage.data_refresh_needed() == expected_output

    # Empty Storage Cases
    def test_get_weight_entry_empty_storage(self, empty_storage):
        assert empty_storage.get_weight_entry(date=dt.date(2027, 1, 28)) == None

    def test_get_weight_entries_empty_storage(self, empty_storage):
        assert empty_storage.get_weight_entries() == []

    def test_create_weight_entry_empty_storage(self, empty_storage):
        date = dt.date(2025, 8, 28)
        weight = 74.5
        empty_storage.create_weight_entry(date, weight)
        assert len(empty_storage.get_weight_entries()) == 1
        expected_entry = WeightEntry.model_validate(
            {
                "date": date,
                "weight": weight,
            }
        )
        assert empty_storage.get_weight_entry(date=date) == expected_entry

    def test_update_weight_entry_empty_storage(self, empty_storage):
        date = dt.date(1990, 1, 1)
        weight = 98.1
        assert empty_storage.get_weight_entry(date) == None
        with pytest.raises(ValueError):
            empty_storage.update_weight_entry(date, weight)

    def test_delete_weight_entry_empty_storage(self, empty_storage):
        date = dt.date(1990, 1, 1)
        assert empty_storage.get_weight_entry(date) == None
        with pytest.raises(ValueError):
            empty_storage.delete_weight_entry(date)
        assert len(empty_storage.get_weight_entries()) == 0

    def test_data_refresh_needed_empty_storage(self, empty_storage):
        assert len(empty_storage.get_weight_entries()) == 0
        assert empty_storage.data_refresh_needed() == True
