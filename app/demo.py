import datetime as dt
import json
import traceback
from typing import Any
from pathlib import Path

from pydantic import TypeAdapter

from . import utils
from .project_types import WeightEntry


class DemoStorage:
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR = "demo"
    MAIN_FILE_NAME = "demo_seed_storage.json"
    DAILY_ENTRIES_MAIN_FILE_PATH: Path = BASE_DIR / DATA_DIR / MAIN_FILE_NAME

    def __init__(self) -> None:
        self._data: list[WeightEntry] = DemoStorage._load_weights_from_file()

    def get_weight_entries(self) -> list[WeightEntry]:
        return self._data

    def get_weight_entry(self, date: dt.date) -> WeightEntry | None:
        filtered: list[WeightEntry] = [
            entry for entry in self._data if entry.date == date
        ]
        return filtered[0] if filtered else None

    def create_weight_entry(self, date: dt.date, weight: float | int) -> None:
        existing: list[WeightEntry] = [
            entry for entry in self._data if entry.date == date
        ]
        if existing:
            raise ValueError(
                f"Weight entry already exists for date {date.strftime('%Y-%m-%d')}. "
                f"Use update method to replace it."
            )

        self._data.append(WeightEntry(date=date, weight=float(weight)))

    def delete_weight_entry(self, date: dt.date) -> None:
        existing: list[WeightEntry] = [
            entry for entry in self._data if entry.date == date
        ]
        if not existing:
            raise ValueError("Weight entry doesn't exist for this date.")

        self._data = [entry for entry in self._data if entry.date != date]

    def update_weight_entry(self, date: dt.date, weight: float | int) -> None:
        existing: list[WeightEntry] = [
            entry for entry in self._data if entry.date == date
        ]
        if not existing:
            raise ValueError(
                "Weight entry doesn't exist for this date. ' \
            'Use create method to create it."
            )

        row_to_update: WeightEntry = existing[0]
        row_to_update.weight = float(weight)

    def export_to_csv(self) -> None:
        pass

    def data_refresh_needed(self) -> bool:
        if not self._data:
            return True

        latest_entry_date: dt.date | None = utils.get_latest_entry_date(self._data)
        return latest_entry_date < dt.date.today() if latest_entry_date else True

    @classmethod
    def _load_weights_from_file(cls) -> list[WeightEntry]:
        try:
            json_string = cls.DAILY_ENTRIES_MAIN_FILE_PATH.read_bytes()
            weight_entries = TypeAdapter(list[WeightEntry]).validate_json(json_string)

            return weight_entries
        except FileNotFoundError:
            traceback.print_exc()
            print("Data file missing. Creating empty file")
            cls.DAILY_ENTRIES_MAIN_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            cls.DAILY_ENTRIES_MAIN_FILE_PATH.write_text(json.dumps([]))

            return []

        except (json.JSONDecodeError, Exception):
            raise


class DemoDataSourceClient:
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR = "demo"
    RAW_DATA_FILE_NAME = "demo_raw_gfit_data.json"
    RAW_DATA_FILE_PATH: Path = BASE_DIR / DATA_DIR / RAW_DATA_FILE_NAME

    def get_raw_data(
        self, date_from: str | None = None, date_to: str | None = None
    ) -> Any:
        raw_data = json.loads(self.RAW_DATA_FILE_PATH.read_text())
        return raw_data

    def store_raw_data(self, raw_dataset: Any) -> None:
        pass

    def convert_to_daily_entries(self, raw_dataset: Any) -> list[WeightEntry]:
        return TypeAdapter(list[WeightEntry]).validate_python(self._dummy_daily_entries())

    def _dummy_daily_entries(self) -> list[dict[str, str | float]]:
        data: list[dict[str, str | float]] = [
            {"date": "2025-04-11", "weight": 73.0},
            {"date": "2025-04-12", "weight": 72.9},
            {"date": "2025-04-13", "weight": 72.8},
            {"date": "2025-04-14", "weight": 72.7},
            {"date": "2025-04-15", "weight": 72.6},
            {"date": "2025-04-16", "weight": 72.5},
            {"date": "2025-04-17", "weight": 72.4},
            {"date": "2025-04-18", "weight": 72.3},
            {"date": "2025-04-19", "weight": 72.2},
            {"date": "2025-04-20", "weight": 72.1},
            {"date": "2025-04-21", "weight": 72.0},
            {"date": "2025-04-22", "weight": 71.9},
            {"date": "2025-04-23", "weight": 71.8},
            {"date": "2025-04-24", "weight": 71.7},
            {"date": "2025-04-25", "weight": 71.6},
            {"date": "2025-04-26", "weight": 71.5},
            {"date": "2025-04-27", "weight": 71.4},
            {"date": "2025-04-28", "weight": 71.3},
            {"date": "2025-04-29", "weight": 71.2},
            {"date": "2025-04-30", "weight": 71.1},
            {"date": "2025-05-01", "weight": 71.0},
            {"date": "2025-05-02", "weight": 70.9},
            {"date": "2025-05-03", "weight": 70.8},
            {"date": "2025-05-04", "weight": 70.7},
            {"date": "2025-05-05", "weight": 70.6},
        ]
        return data
