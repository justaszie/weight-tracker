import datetime as dt
import json
import logging
import os
from collections.abc import Iterable
from pathlib import Path
from uuid import UUID

import pandas as pd
from google.oauth2.credentials import Credentials
from sqlalchemy.exc import IntegrityError
from sqlmodel import (
    Field,
    Session,
    SQLModel,
    create_engine,
    select,
)

from .project_types import DuplicateEntryError, EntryNotFoundError, WeightEntry

logger = logging.getLogger(__name__)


class DBWeightEntry(SQLModel, table=True):
    __tablename__ = "weight_entries"

    user_id: UUID = Field(primary_key=True, default=None)
    entry_date: dt.date = Field(primary_key=True, default=None)
    # No FK relationship here as users are managed in external server (Supabase)
    weight: float = Field(nullable=False, default=None)


# Model for storing Google OAuth2 access tokens for users
class DBGoogleCredentials(SQLModel, table=True):
    __tablename__ = "google_credentials"

    user_id: UUID = Field(primary_key=True)
    token: str = Field(nullable=False)
    refresh_token: str = Field(nullable=False, default=None)
    scopes: str = Field(
        nullable=False,
        default=json.dumps(
            [
                "https://www.googleapis.com/auth/fitness.body.read",
                "https://www.googleapis.com/auth/fitness.activity.read",
            ]
        ),
    )
    token_uri: str = Field(nullable=False, default=None)
    expiry: dt.datetime = Field(nullable=True, default=None)

    def to_credentials_object(self) -> Credentials:
        try:
            creds: Credentials = Credentials(  # type: ignore
                token=self.token,
                refresh_token=self.refresh_token,
                scopes=json.loads(self.scopes),
                client_id=os.environ["GOOGLE_CLIENT_ID"],
                client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
                token_uri=self.token_uri,
                expiry=self.expiry,
            )
            return creds
        except KeyError:
            logger.error("Google credentials init failed - missing config values")
            raise
        except Exception as e:
            logger.error("Failed to convert credentials db entry to valid credentials")
            raise ValueError(
                "Failed to convert credentials db entry to valid credentials"
            ) from e

    @classmethod
    def from_credentials_object(
        cls, user_id: UUID, creds: Credentials
    ) -> "DBGoogleCredentials":
        return cls(
            user_id=user_id,
            token=creds.token,
            refresh_token=creds.refresh_token,
            scopes=json.dumps(creds.scopes),
            token_uri=creds.token_uri,
            expiry=creds.expiry,
        )


class DatabaseStorage:
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR = "data"

    CSV_FILE_NAME = "daily_history.csv"
    DAILY_ENTRIES_CSV_DIR: Path = Path.joinpath(BASE_DIR, DATA_DIR, "csv")

    def __init__(self) -> None:
        connection_string = os.environ.get("DB_CONNECTION_STRING")
        if not connection_string:
            logger.error("Missing database connection string in environment")
            raise Exception("Missing database connection string in environment")
        self._engine = create_engine(connection_string)

        # Set up the database when initializing storage
        self._setup_database()

    def _setup_database(self) -> None:
        SQLModel.metadata.create_all(self._engine)

    def get_weight_entries(self, user_id: UUID) -> list[WeightEntry]:
        with Session(self._engine) as session:
            statement = select(DBWeightEntry).where(DBWeightEntry.user_id == user_id)
            results = session.exec(statement)
            return [
                WeightEntry.model_validate(row, from_attributes=True)
                for row in results.all()
            ]

    def create_weight_entry(
        self, user_id: UUID, entry_date: dt.date, weight: float | int
    ) -> None:
        with Session(self._engine) as session:
            try:
                new_entry = DBWeightEntry(
                    user_id=user_id, entry_date=entry_date, weight=weight
                )
                session.add(new_entry)
                session.commit()
            except IntegrityError as e:
                logger.warning(
                    f"Duplicate weight entry creation attempted "
                    f"| User: {user_id}"
                    f"| Date: {entry_date}"
                )
                raise DuplicateEntryError(
                    f"Weight entry already exists for date"
                    f" {entry_date.strftime('%Y-%m-%d')}."
                    f"Use update method to replace it."
                ) from e

    def create_weight_entries(self, entries: Iterable[WeightEntry]) -> None:
        entries_db = [
            DBWeightEntry(
                user_id=entry.user_id,
                entry_date=entry.entry_date,
                weight=entry.weight,
            )
            for entry in entries
        ]
        with Session(self._engine) as session:
            session.add_all(entries_db)
            session.commit()

    def get_weight_entry(
        self, user_id: UUID, entry_date: dt.date
    ) -> WeightEntry | None:
        with Session(self._engine) as session:
            result = session.get(DBWeightEntry, (user_id, entry_date))
            if not result:
                return None

            return WeightEntry.model_validate(result, from_attributes=True)

    def update_weight_entry(
        self, user_id: UUID, entry_date: dt.date, weight: float | int
    ) -> None:
        with Session(self._engine) as session:
            entry = session.get(DBWeightEntry, (user_id, entry_date))
            if not entry:
                logger.warning(
                    f"Update on non-existing weight entry attempted. date: {entry_date}"
                )
                raise EntryNotFoundError(
                    "Weight entry doesn't exist for this date. "
                    "Use create method to create it."
                )

            entry.weight = weight
            session.add(entry)
            session.commit()
            session.refresh(entry)

    def delete_weight_entry(self, user_id: UUID, entry_date: dt.date) -> None:
        with Session(self._engine) as session:
            entry = session.get(DBWeightEntry, (user_id, entry_date))
            if not entry:
                logger.warning(
                    f"Delete on non-existing weight entry attempted. date: {entry_date}"
                )
                raise EntryNotFoundError("Weight entry doesn't exist for this date.")

            session.delete(entry)
            session.commit()

    def export_to_csv(self, user_id: UUID) -> None:
        filepath = self.DAILY_ENTRIES_CSV_DIR / str(user_id) / self.CSV_FILE_NAME
        filepath.parent.mkdir(parents=True, exist_ok=True)
        try:
            entries = [entry.model_dump() for entry in self.get_weight_entries(user_id)]
            pd.DataFrame(entries).set_index(  # pyright: ignore[reportUnknownMemberType]
                ["user_id", "entry_date"]
            ).to_csv(filepath)
        except Exception:
            logger.warning(
                f"Failed to export weight entries to csv. Filepath: {filepath}",
                exc_info=True,
            )

    def store_google_credentials(self, user_id: UUID, creds: Credentials) -> None:
        with Session(self._engine) as session:
            try:
                creds_entry = session.get(DBGoogleCredentials, user_id)
                if creds_entry:
                    # Update existing access token
                    creds_entry.sqlmodel_update(
                        DBGoogleCredentials.from_credentials_object(user_id, creds)
                    )
                else:
                    # Insert access token
                    creds_entry = DBGoogleCredentials.from_credentials_object(
                        user_id, creds
                    )

                session.add(creds_entry)
                session.commit()

            except Exception:
                logger.error(
                    "Google Credentials storage failed",
                    exc_info=True,
                )
                raise

    def load_google_credentials(self, user_id: UUID) -> Credentials | None:
        with Session(self._engine) as session:
            try:
                creds_entry = session.get(DBGoogleCredentials, user_id)
                if not creds_entry:
                    return None

                return creds_entry.to_credentials_object()
            except Exception:
                logger.error("Loading credentials from DB failed")
                return None

    def close_connection(self) -> None:
        if self._engine:
            self._engine.dispose()
