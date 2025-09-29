import datetime as dt
import os
import traceback
from pathlib import Path

import pandas as pd
from sqlalchemy.exc import IntegrityError
from sqlmodel import (
    Field,
    Session,
    SQLModel,
    create_engine,
    select,
)

from . import utils
from .project_types import WeightEntry


class DBWeightEntry(SQLModel, table=True):
    __tablename__ = "weight_entries"

    entry_date: dt.date = Field(primary_key=True, default=None)
    weight: float = Field(nullable=False, default=None)


class DatabaseStorage:
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR = "data"
    CSV_FILE_NAME = "daily_history.csv"
    DAILY_ENTRIES_CSV_FILE_PATH: Path = Path.joinpath(BASE_DIR, DATA_DIR, CSV_FILE_NAME)

    def __init__(self) -> None:
        connection_string = os.environ.get("DB_CONNECTION_STRING")
        if not connection_string:
            raise Exception("Missing database connection string in environment")
        self._engine = create_engine(connection_string)

        # Set up the database when initializing storage
        self._setup_database()

    def _setup_database(self) -> None:
        SQLModel.metadata.create_all(self._engine)

    def get_weight_entries(self) -> list[WeightEntry]:
        with Session(self._engine) as session:
            statement = select(DBWeightEntry)
            results = session.exec(statement)
            return [
                WeightEntry.model_validate(row, from_attributes=True)
                for row in results.all()
            ]

    def create_weight_entry(self, entry_date: dt.date, weight: float | int) -> None:
        with Session(self._engine) as session:
            try:
                new_entry = DBWeightEntry(entry_date=entry_date, weight=weight)
                session.add(new_entry)
                session.commit()
            except IntegrityError as e:
                raise ValueError(
                    f"Weight entry already exists for date"
                    f" {entry_date.strftime('%Y-%m-%d')}."
                    f"Use update method to replace it."
                ) from e

    def data_refresh_needed(self) -> bool:
        existing_data = self.get_weight_entries()

        latest_entry_date: dt.date | None = utils.get_latest_entry_date(existing_data)
        return latest_entry_date < dt.date.today() if latest_entry_date else True

    def _find_db_weight_entry(self, entry_date: dt.date) -> DBWeightEntry | None:
        with Session(self._engine) as session:
            result = session.get(DBWeightEntry, entry_date)
            return result

    def get_weight_entry(self, entry_date: dt.date) -> WeightEntry | None:
        result = self._find_db_weight_entry(entry_date)
        if not result:
            return None

        return WeightEntry.model_validate(result, from_attributes=True)

    def update_weight_entry(self, entry_date: dt.date, weight: float | int) -> None:
        entry = self._find_db_weight_entry(entry_date)
        if not entry:
            raise ValueError(
                "Weight entry doesn't exist for this date. ' \
                'Use create method to create it."
            )

        with Session(self._engine) as session:
            entry.weight = weight
            session.add(entry)
            session.commit()
            session.refresh(entry)

    def delete_weight_entry(self, entry_date: dt.date) -> None:
        entry = self._find_db_weight_entry(entry_date)
        if not entry:
            raise ValueError("Weight entry doesn't exist for this date.")

        with Session(self._engine) as session:
            session.delete(entry)
            session.commit()

    def export_to_csv(self) -> None:
        try:
            entries = [entry.model_dump() for entry in self.get_weight_entries()]
            pd.DataFrame(entries).set_index(  # pyright: ignore[reportUnknownMemberType]
                "entry_date"
            ).to_csv(DatabaseStorage.DAILY_ENTRIES_CSV_FILE_PATH)
        except Exception:
            traceback.print_exc()
