import json
import os
import datetime as dt
import utils
import pandas as pd
from pathlib import Path


class FileStorage:
    BASE_DIR = Path(__file__).parent
    DAILY_ENTRIES_CSV_FILE_PATH = os.path.join(BASE_DIR, "data/daily_history.csv")
    DAILY_ENTRIES_MAIN_FILE_PATH = os.path.join(BASE_DIR, "data/daily_data.json")

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
        # self.save()

    def delete_weight_entry(self, date):
        self.data = [
            entry for entry in self.data if entry["date"] != date.strftime("%Y-%m-%d")
        ]
        # self.save()

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
        # self.save()

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

        if csv_copy:
            pd.DataFrame(self.data).set_index("date").to_csv(
                FileStorage.DAILY_ENTRIES_CSV_FILE_PATH
            )

    def data_refresh_needed(self):
        if not self.data:
            return True

        try:
            return utils.get_latest_entry_date(self.data) < dt.date.today()
        except (KeyError, ValueError):
            return True

    def _load_weights_from_file(self):
        with open(FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH, "r") as file:
            try:
                entries = json.load(file)
                for entry in entries:
                    entry["date"] = dt.date.fromisoformat(entry["date"])
                return entries
            except (json.JSONDecodeError, FileNotFoundError):
                return None
            except Exception as e:
                print(e)
