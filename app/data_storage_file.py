import json
import os
import datetime as dt
import utils
import pandas as pd

class FileStorage:
    DAILY_ENTRIES_CSV_FILE_PATH = "data/daily_history.csv"
    DAILY_ENTRIES_MAIN_FILE_PATH = "data/daily_data.json"

    def __init__(self):
        self.data =  self._load_weights_from_file()

    def get_weight_entries(self):
        return self.data

    def get_weight_entry(self, date):
        filtered = [entry for entry in self.data if entry["date"] == date]
        return filtered[0] if filtered else None

    def create_weight_entry(self, date, weight):
        existing = [entry for entry in self.data if entry["date"] == date]
        if existing:
            raise ValueError(
                f"Weight entry already exists for date {date}. " \
                f"Use update method to replace it."
            )

        self.data.append({'date': date, 'weight': weight})
        # self.save()


    def delete_weight_entry(self, date):
        self.data = [entry for entry in self.data if entry["date"] != date]
        # self.save()


    def update_weight_entry(self, date, weight):
        existing = [entry for entry in self.data if entry["date"] == date]
        if not existing:
            raise ValueError(
                "Weight entry doesn't exist for this date. ' \
            'Use create method to create it."
            )

        row_to_update = existing[0]
        row_to_update['weight'] = weight
        # self.save()


    def save(self, csv_copy=True):
        with open(FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH, "w") as file:
            json.dump(self.data, file)

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
                return json.load(file)
            except (json.JSONDecodeError, FileNotFoundError):
                return None
