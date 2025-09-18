import datetime as dt
import json
import traceback
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
