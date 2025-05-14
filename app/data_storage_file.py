import json
import os
import datetime as dt
import utils
import pandas as pd

DAILY_ENTRIES_CSV_FILE_PATH = "data/daily_history.csv"
DAILY_ENTRIES_CLEAN_FILE_PATH = "data/daily_data.json"


def get_weight_entries():
    weight_entries = _load_weights_from_file()
    return weight_entries


def get_weight_entry(date):
    weight_entries = get_weight_entries()
    filtered = [entry for entry in weight_entries if entry["date"] == date]
    return filtered[0] if filtered else None


def create_weight_entry(date, weight):
    weight_entries = get_weight_entries()
    existing = [entry for entry in weight_entries if entry["date"] == date]
    if existing:
        raise ValueError(
            "Weight entry already exists for this date. "
            "Use update method to replace it."
        )

    weight_entries.append({date: weight})
    _store_weight_entries_in_file(weight_entries)


def delete_weight_entry(date):
    weight_entries = get_weight_entries()
    to_keep = [entry for entry in weight_entries if entry["date"] != date]
    _store_weight_entries_in_file(to_keep)


def update_weight_entry(date, weight):
    weight_entries = get_weight_entries()
    existing = [entry for entry in weight_entries if entry["date"] == date]
    if not existing:
        raise ValueError(
            "Weight entry doesn't exist for this date. ' \
        'Use create method to create it."
        )

    existing[0][date] = weight
    _store_weight_entries_in_file(weight_entries)


def data_refresh_needed():
    weight_entries = get_weight_entries()
    if not weight_entries:
        return True

    try:
        return utils.get_latest_entry_date(weight_entries) < dt.date.today()
    except (KeyError, ValueError):
        return True


def _store_weight_entries_in_file(weight_entries, csv_copy=True):
    with open(DAILY_ENTRIES_CLEAN_FILE_PATH, "w") as file:
        json.dump(weight_entries, file)

    if csv_copy:
        pd.DataFrame(weight_entries).set_index("date").to_csv(
            DAILY_ENTRIES_CSV_FILE_PATH
        )


def _load_weights_from_file():
    with open(DAILY_ENTRIES_CLEAN_FILE_PATH, "r") as file:
        try:
            return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return None
