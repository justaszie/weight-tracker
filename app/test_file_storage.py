import datetime as dt
import json
import os
from pathlib import Path
import pytest

from file_storage import (
    FileStorage,
)


"""
Generic protocol:
class DataStorage(Protocol):
    def get_weight_entries(self) -> list[DailyWeightEntry]: ...

    def get_weight_entry(self, date: dt.date) -> DailyWeightEntry | None: ...

    def create_weight_entry(self, date: dt.date, weight: float | int) -> None: ...

    def delete_weight_entry(self, date: dt.date) -> None: ...

    def update_weight_entry(self, date: dt.date, weight: float | int) -> None: ...

    def export_to_csv(self) -> None: ...

    def data_refresh_needed(self) -> bool: ...

 """


# TODO - it will try to load files, should we use mock here?
# @pytest.fixture
# def get_file_storage():
#     return FileStorage()


# class DataStorageProtocolTests:

class TesteightsLoadFromFile:
    def test_load_weights_from_non_existant_file(self, mocker):
        mock_file_path = Path(__file__).resolve().parent / "non_existing.json"
        mocker.patch(
            "file_storage.FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH",
            new=mock_file_path,
        )
        entries = FileStorage._load_weights_from_file()
        assert entries == []
        if not Path(mock_file_path).is_file():
            print("Expected the storage file to be created but it was not")
            assert False

        if mock_file_path.exists():
            mock_file_path.unlink(missing_ok=True)

    def test_load_weights_from_wrong_format_file(self, mocker):
        test_file_data = ""

        mock_storage_file = mocker.mock_open(read_data=test_file_data)
        mock_file_load = mocker.patch("file_storage.open", new=mock_storage_file)

        with pytest.raises(json.JSONDecodeError):
            FileStorage._load_weights_from_file()


    def test_load_weights_from_file(self, mocker):
        test_file_data = json.dumps(
            [
                {"date": "2025-08-28", "weight": 73.6},
                {"date": "2025-08-29", "weight": 73.6},
                {"date": "2025-08-30", "weight": 73.5},
                {"date": "2025-09-01", "weight": 73.0},
            ]
        )

        mock_storage_file = mocker.mock_open(read_data=test_file_data)
        mock_file_load = mocker.patch("file_storage.open", new=mock_storage_file)

        entries = FileStorage._load_weights_from_file()

        assert entries == [
            {"date": dt.date(2025, 8, 28), "weight": 73.6},
            {"date": dt.date(2025, 8, 29), "weight": 73.6},
            {"date": dt.date(2025, 8, 30), "weight": 73.5},
            {"date": dt.date(2025, 9, 1), "weight": 73.0},
        ]
        mock_file_load.assert_called_once_with(FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH)