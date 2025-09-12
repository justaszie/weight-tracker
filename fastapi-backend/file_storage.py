import datetime as dt
import json
import traceback
from pathlib import Path
from typing import TypedDict

import pandas as pd

import utils
from project_types import WeightEntry


class JSONPersistedWeightEntry(TypedDict):
    date: str
    weight: float | int


class FileStorage:
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR = "data"
    CSV_FILE_NAME = "daily_history.csv"
    MAIN_FILE_NAME = "daily_data.json"
    DAILY_ENTRIES_CSV_FILE_PATH: Path = Path.joinpath(BASE_DIR, DATA_DIR, CSV_FILE_NAME)
    DAILY_ENTRIES_MAIN_FILE_PATH: Path = Path.joinpath(
        BASE_DIR, DATA_DIR, MAIN_FILE_NAME
    )

    def __init__(self) -> None:
        self._data: list[WeightEntry] = FileStorage._load_weights_from_file()

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
                f"Weight entry already exists for date {date.strftime("%Y-%m-%d")}. "
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

    def save(self) -> None:
        with open(FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH, "w") as file:
            entries: list[JSONPersistedWeightEntry] = [
                {
                    "date": entry.date.isoformat(),
                    "weight": entry.weight,
                }
                for entry in self._data
            ]
            json.dump(entries, file)

    def export_to_csv(self) -> None:
        try:
            pd.DataFrame(
                self._data
            ).set_index(  # pyright: ignore[reportUnknownMemberType]
                "date"
            ).to_csv(
                FileStorage.DAILY_ENTRIES_CSV_FILE_PATH
            )
        except Exception:
            traceback.print_exc()

    def data_refresh_needed(self) -> bool:
        if not self._data:
            return True

        latest_entry_date: dt.date | None = utils.get_latest_entry_date(self._data)
        return latest_entry_date < dt.date.today() if latest_entry_date else True

    @classmethod
    def _load_weights_from_file(cls) -> list[WeightEntry]:
        try:
            with open(cls.DAILY_ENTRIES_MAIN_FILE_PATH) as file:
                file_entries: list[JSONPersistedWeightEntry] = json.load(file)
                result: list[WeightEntry] = [
                    WeightEntry(
                        date=dt.date.fromisoformat(entry["date"]),
                        weight=float(entry["weight"]),
                    )
                    for entry in file_entries
                ]
                return result
        except FileNotFoundError:
            with open(cls.DAILY_ENTRIES_MAIN_FILE_PATH, "w") as file:
                json.dump([], file)
                traceback.print_exc()
                print("Data file missing. Creating empty file")
                return []
        except (json.JSONDecodeError, Exception):
            raise
