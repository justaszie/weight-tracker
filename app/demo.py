import datetime as dt
import json
import logging
import os
import random
from pathlib import Path
from typing import Any
from uuid import UUID

from dotenv import load_dotenv
from pydantic import TypeAdapter

# from . import utils
from .project_types import WeightEntry

logger = logging.getLogger(__name__)


load_dotenv()
DEMO_USER_ID = UUID(os.environ.get("DEMO_USER_ID"))


# class DemoStorage:
#     BASE_DIR: Path = Path(__file__).resolve().parent
#     DATA_DIR = "demo"
#     MAIN_FILE_NAME = "demo_seed_storage.json"
#     DAILY_ENTRIES_MAIN_FILE_PATH: Path = BASE_DIR / DATA_DIR / MAIN_FILE_NAME

#     def __init__(self) -> None:
#         self._data: list[WeightEntry] = DemoStorage._load_weights_from_file()
#         logger.info(f"DemoStorage created with {len(self._data)} demo weight entries")

#     def get_weight_entries(self, user_id: UUID) -> list[WeightEntry]:
#         return self._data

#     def get_weight_entry(self, entry_date: dt.date) -> WeightEntry | None:
#         filtered: list[WeightEntry] = [
#             entry for entry in self._data if entry.entry_date == entry_date
#         ]
#         return filtered[0] if filtered else None

#     def create_weight_entry(self, entry_date: dt.date, weight: float | int) -> None:
#         existing: list[WeightEntry] = [
#             entry for entry in self._data if entry.entry_date == entry_date
#         ]
#         if existing:
#             raise ValueError(
#                 f"Weight entry already exists for date "
#                 f"{entry_date.strftime('%Y-%m-%d')}. "
#                 f"Use update method to replace it."
#             )

#         self._data.append(
#             WeightEntry(
#                 user_id=TEST_USER_ID, entry_date=entry_date, weight=float(weight)
#             )
#         )

#     def delete_weight_entry(self, entry_date: dt.date) -> None:
#         existing: list[WeightEntry] = [
#             entry for entry in self._data if entry.entry_date == entry_date
#         ]
#         if not existing:
#             raise ValueError("Weight entry doesn't exist for this date.")

#         self._data = [entry for entry in self._data if entry.entry_date != entry_date]

#     def update_weight_entry(self, entry_date: dt.date, weight: float | int) -> None:
#         existing: list[WeightEntry] = [
#             entry for entry in self._data if entry.entry_date == entry_date
#         ]
#         if not existing:
#             raise ValueError(
#                 "Weight entry doesn't exist for this date. ' \
#             'Use create method to create it."
#             )

#         row_to_update: WeightEntry = existing[0]
#         row_to_update.weight = float(weight)

#     def export_to_csv(self) -> None:
#         pass

#     def data_refresh_needed(self) -> bool:
#         if not self._data:
#             return True

#         latest_entry_date: dt.date | None = utils.get_latest_entry_date(self._data)
#         return latest_entry_date < dt.date.today() if latest_entry_date else True

#     @classmethod
#     def _load_weights_from_file(cls) -> list[WeightEntry]:
#         try:
#             json_string = cls.DAILY_ENTRIES_MAIN_FILE_PATH.read_bytes()
#             weight_entries = TypeAdapter(list[WeightEntry]).validate_json(json_string)

#             return weight_entries
#         except FileNotFoundError:
#             logger.warning(
#                 "Demo data file missing. Creating empty file",
#                 f"Filepath: {cls.DAILY_ENTRIES_MAIN_FILE_PATH}",
#             )
#             cls.DAILY_ENTRIES_MAIN_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
#             cls.DAILY_ENTRIES_MAIN_FILE_PATH.write_text(json.dumps([]))

#             return []

#         except (json.JSONDecodeError, Exception):
#             raise

#     def close_connection(self) -> None:
#         pass


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
        entries = TypeAdapter(list[WeightEntry]).validate_python(
            self._dummy_daily_entries()
        )
        # Add dummy weight for today so that update happens in demo
        today = dt.datetime.now().date()
        rand_decimal = random.randrange(1, 9) / 10
        dummy_weight = 70 + rand_decimal
        entries.append(
            WeightEntry(user_id=DEMO_USER_ID, entry_date=today, weight=dummy_weight)
        )
        print(f"DUMMY TODAYS ENTRY: {dummy_weight}")
        return entries

    def _dummy_daily_entries(self) -> list[dict[str, str | float | UUID]]:
        data: list[dict[str, str | float | UUID]] = [
            {"entry_date": "2025-04-11", "weight": 73.0, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-12", "weight": 72.9, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-13", "weight": 72.8, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-14", "weight": 72.7, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-15", "weight": 72.6, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-16", "weight": 72.5, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-17", "weight": 72.4, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-18", "weight": 72.3, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-19", "weight": 72.2, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-20", "weight": 72.1, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-21", "weight": 72.0, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-22", "weight": 71.9, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-23", "weight": 71.8, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-24", "weight": 71.7, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-25", "weight": 71.6, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-26", "weight": 71.5, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-27", "weight": 71.4, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-28", "weight": 71.3, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-29", "weight": 71.2, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-04-30", "weight": 71.1, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-01", "weight": 71.0, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-02", "weight": 70.9, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-03", "weight": 70.8, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-04", "weight": 70.7, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-05", "weight": 70.6, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-06", "weight": 70.5, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-07", "weight": 70.4, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-08", "weight": 70.3, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-09", "weight": 70.2, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-10", "weight": 70.1, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-11", "weight": 70.0, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-12", "weight": 69.9, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-13", "weight": 69.8, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-14", "weight": 69.7, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-15", "weight": 69.6, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-16", "weight": 69.5, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-17", "weight": 69.4, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-18", "weight": 69.3, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-19", "weight": 69.2, "user_id": DEMO_USER_ID},
            {"entry_date": "2025-05-20", "weight": 69.1, "user_id": DEMO_USER_ID},
        ]
        return data
