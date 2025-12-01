import datetime as dt
import json
import logging
from collections.abc import Iterable
from pathlib import Path
from typing import cast
from uuid import UUID

import pandas as pd
from google.oauth2.credentials import Credentials
from pydantic import TypeAdapter

from .project_types import DuplicateEntryError, WeightEntry

logger = logging.getLogger(__name__)


class FileStorage:
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR = "data"

    MAIN_FILE_NAME = "daily_data.json"
    DAILY_ENTRIES_MAIN_FILE_PATH: Path = Path.joinpath(
        BASE_DIR, DATA_DIR, MAIN_FILE_NAME
    )

    CSV_FILE_NAME = "daily_history.csv"
    DAILY_ENTRIES_CSV_DIR: Path = Path.joinpath(BASE_DIR, DATA_DIR, "csv")

    AUTH_DIR = "auth"
    CREDS_FILE_NAME = "token.json"
    CREDS_FILE_DIR: Path = Path.joinpath(BASE_DIR, AUTH_DIR)

    def __init__(self) -> None:
        self._data: list[WeightEntry] = FileStorage._load_weights_from_file()

    def get_weight_entries(self, user_id: UUID) -> list[WeightEntry]:
        filtered = [entry for entry in self._data if entry.user_id == user_id]
        return filtered

    def get_weight_entry(
        self, user_id: UUID, entry_date: dt.date
    ) -> WeightEntry | None:
        filtered: list[WeightEntry] = [
            entry
            for entry in self._data
            if entry.entry_date == entry_date and entry.user_id == user_id
        ]
        return filtered[0] if filtered else None

    def create_weight_entry(
        self, user_id: UUID, entry_date: dt.date, weight: float | int
    ) -> None:
        existing: list[WeightEntry] = [
            entry
            for entry in self._data
            if entry.entry_date == entry_date and entry.user_id == user_id
        ]
        if existing:
            logger.warning(
                "Duplicate weight entry creation attempted "
                f"| Date: {entry_date} | User: {user_id}"
            )
            raise DuplicateEntryError(
                f"Weight entry already exists for date"
                f" {entry_date.strftime('%Y-%m-%d')}."
                f"Use update method to replace it."
            )

        self._data.append(
            WeightEntry(user_id=user_id, entry_date=entry_date, weight=float(weight))
        )

    def create_weight_entries(self, entries: Iterable[WeightEntry]) -> None:
        existing: set[tuple[UUID, dt.date]] = {
            (entry.user_id, entry.entry_date) for entry in self._data
        }

        for entry in entries:
            if (entry.user_id, entry.entry_date) in existing:
                logger.warning(
                    f"({entry.user_id, entry.entry_date}) pair already exists. Skipping"
                )
                continue

            self._data.append(entry)

    def delete_weight_entry(self, user_id: UUID, entry_date: dt.date) -> None:
        existing: list[WeightEntry] = [
            entry
            for entry in self._data
            if entry.entry_date == entry_date and entry.user_id == user_id
        ]
        if not existing:
            logger.warning(
                f"Delete on non-existing weight entry attempted."
                f"Date: {entry_date} User: {user_id}"
            )
            raise ValueError("Weight entry doesn't exist for this date.")

        self._data = [
            entry
            for entry in self._data
            if entry.entry_date != entry_date or entry.user_id != user_id
        ]

    def update_weight_entry(
        self, user_id: UUID, entry_date: dt.date, weight: float | int
    ) -> None:
        existing: list[WeightEntry] = [
            entry
            for entry in self._data
            if entry.entry_date == entry_date and entry.user_id == user_id
        ]
        if not existing:
            logger.warning(
                "Update on non-existing weight entry attempted."
                f"Date: {entry_date}. User: {user_id}"
            )
            raise ValueError(
                "Weight entry doesn't exist for this date. ' \
            'Use create method to create it."
            )

        row_to_update: WeightEntry = existing[0]
        row_to_update.weight = float(weight)

    def save(self) -> None:
        json_data = TypeAdapter(list[WeightEntry]).dump_json(self._data)

        FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH.parent.mkdir(
            parents=True, exist_ok=True
        )
        FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH.write_bytes(json_data)

    def export_to_csv(self, user_id: UUID) -> None:
        try:
            filepath = self.DAILY_ENTRIES_CSV_DIR / str(user_id) / self.CSV_FILE_NAME
            filepath.parent.mkdir(parents=True, exist_ok=True)

            entries = [entry.model_dump() for entry in self._data]
            pd.DataFrame(entries).set_index(  # pyright: ignore[reportUnknownMemberType]
                "entry_date"
            ).to_csv(filepath)
        except Exception:
            logger.warning(
                f"Failed to export weight entries to csvFilepath: {filepath}",
                exc_info=True,
            )

    @classmethod
    def _load_weights_from_file(cls) -> list[WeightEntry]:
        try:
            json_string = cls.DAILY_ENTRIES_MAIN_FILE_PATH.read_bytes()
            weight_entries = TypeAdapter(list[WeightEntry]).validate_json(json_string)
            return weight_entries
        except FileNotFoundError:
            logger.warning("Data file missing. Creating empty file")
            cls.DAILY_ENTRIES_MAIN_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            cls.DAILY_ENTRIES_MAIN_FILE_PATH.write_text(json.dumps([]))

            return []

        except (json.JSONDecodeError, Exception):
            raise

    def store_google_credentials(self, user_id: UUID, creds: Credentials) -> None:
        filepath = self.CREDS_FILE_DIR / str(user_id) / self.CREDS_FILE_NAME
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(creds.to_json())  # type: ignore

    def load_google_credentials(self, user_id: UUID) -> Credentials | None:
        filepath = self.CREDS_FILE_DIR / str(user_id) / self.CREDS_FILE_NAME

        try:
            with open(filepath) as token_file:
                creds = cast(
                    Credentials,
                    Credentials.from_authorized_user_info(  # type: ignore
                        json.load(token_file)
                    ),
                )
                return creds
        except FileNotFoundError:
            logger.warning("Google credentials file not found")
            return None
        except Exception:
            return None

    def close_connection(self) -> None:
        pass
