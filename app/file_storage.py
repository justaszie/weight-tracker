import json
import datetime as dt
import utils
import pandas as pd
from pathlib import Path
import traceback
from typing import Optional
from project_types import DailyWeightEntry


class FileStorage:
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = "data"
    CSV_FILE_NAME = "daily_history.csv"
    MAIN_FILE_NAME = "daily_data.json"
    DAILY_ENTRIES_CSV_FILE_PATH = Path.joinpath(BASE_DIR, DATA_DIR, CSV_FILE_NAME)
    DAILY_ENTRIES_MAIN_FILE_PATH = Path.joinpath(BASE_DIR, DATA_DIR, MAIN_FILE_NAME)

    def __init__(self):
        self.data: list[DailyWeightEntry] = self._load_weights_from_file()

    def get_weight_entries(self) -> list[DailyWeightEntry]:
        return self.data

    def get_weight_entry(self, date: dt.date) -> Optional[DailyWeightEntry]:
        filtered: list[DailyWeightEntry] = [
            entry for entry in self.data if entry["date"] == date
        ]
        return filtered[0] if filtered else None

    def create_weight_entry(self, date: dt.date, weight: float | int) -> None:
        existing: list[DailyWeightEntry] = [
            entry for entry in self.data if entry["date"] == date
        ]
        if existing:
            raise ValueError(
                f"Weight entry already exists for date {date.strftime("%Y-%m-%d")}. "
                f"Use update method to replace it."
            )

        self.data.append({"date": date, "weight": float(weight)})

    def delete_weight_entry(self, date: dt.date) -> None:
        self.data = [entry for entry in self.data if entry["date"] != date]

    def update_weight_entry(self, date: dt.date, weight: float | int) -> None:
        existing: list[DailyWeightEntry] = [
            entry for entry in self.data if entry["date"] == date
        ]
        if not existing:
            raise ValueError(
                "Weight entry doesn't exist for this date. ' \
            'Use create method to create it."
            )

        row_to_update: DailyWeightEntry = existing[0]
        row_to_update["weight"] = float(weight)

    def save(self) -> None:
        with open(FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH, "w") as file:
            entries: list[dict[str, str | float | int]] = [
                {
                    "date": entry["date"].isoformat(),
                    "weight": entry["weight"],
                }
                for entry in self.data
            ]
            json.dump(entries, file)

    def export_to_csv(self) -> None:
        try:
            pd.DataFrame(self.data).set_index("date").to_csv(  # type: ignore
                FileStorage.DAILY_ENTRIES_CSV_FILE_PATH
            )
        except:
            traceback.print_exc()

    def data_refresh_needed(self) -> bool:
        if not self.data:
            return True

        latest_entry_date = utils.get_latest_entry_date(self.data)
        return latest_entry_date < dt.date.today() if latest_entry_date else True

    def _load_weights_from_file(self) -> list[DailyWeightEntry]:
        try:
            with open(FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH, "r") as file:
                entries = json.load(file)
                for entry in entries:
                    entry["date"] = dt.date.fromisoformat(entry["date"])
                return entries
        except FileNotFoundError:
            with open(FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH, "w") as file:
                json.dump([], file)
                traceback.print_exc()
                print("Data file missing. Creating empty file")
                return []
        except (json.JSONDecodeError, Exception) as e:
            raise
