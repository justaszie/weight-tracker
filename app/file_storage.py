import json
import os
import datetime as dt
import utils
import pandas as pd
from pathlib import Path
import traceback


class FileStorage:
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = "data"
    CSV_FILE_NAME = "daily_history.csv"
    MAIN_FILE_NAME = "daily_data.json"
    DAILY_ENTRIES_CSV_FILE_PATH = Path.joinpath(BASE_DIR, DATA_DIR, CSV_FILE_NAME)
    DAILY_ENTRIES_MAIN_FILE_PATH = Path.joinpath(BASE_DIR, DATA_DIR, MAIN_FILE_NAME)

    def __init__(self):
        self.data = self._load_weights_from_file()

    def get_weight_entries(self):
        return self.data

    def get_weight_entry(self, date):
        filtered = [
            entry for entry in self.data if entry["date"] == date.strftime("%Y-%m-%d")
        ]
        return filtered[0] if filtered else None

    def create_weight_entry(self, date, weight):
        existing = [
            entry for entry in self.data if entry["date"] == date.strftime("%Y-%m-%d")
        ]
        if existing:
            raise ValueError(
                f"Weight entry already exists for date {date.strftime("%Y-%m-%d")}. "
                f"Use update method to replace it."
            )

        self.data.append({"date": date, "weight": weight})

    def delete_weight_entry(self, date):
        self.data = [
            entry for entry in self.data if entry["date"] != date.strftime("%Y-%m-%d")
        ]

    def update_weight_entry(self, date, weight):
        existing = [
            entry for entry in self.data if entry["date"] == date.strftime("%Y-%m-%d")
        ]
        if not existing:
            raise ValueError(
                "Weight entry doesn't exist for this date. ' \
            'Use create method to create it."
            )

        row_to_update = existing[0]
        row_to_update["weight"] = weight

    def save(self, csv_copy=True):
        with open(FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH, "w") as file:
            entries = [
                {
                    "date": entry["date"].isoformat(),
                    "weight": entry["weight"],
                }
                for entry in self.data
            ]
            json.dump(entries, file)

        try:
            if csv_copy:
                pd.DataFrame(self.data).set_index("date").to_csv(
                    FileStorage.DAILY_ENTRIES_CSV_FILE_PATH
                )
        except:
            traceback.print_exc()

    def data_refresh_needed(self):
        if not self.data:
            return True

        latest_entry_date = utils.get_latest_entry_date(self.data)
        return latest_entry_date < dt.date.today() if latest_entry_date else True

    def _load_weights_from_file(self):
        entries = []
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
