import datetime as dt
from collections.abc import Iterable
from typing import Any, Literal, Protocol
from uuid import UUID

from google.oauth2.credentials import Credentials
from pydantic import BaseModel

type FitnessGoal = Literal["gain", "lose", "maintain"]
type Result = Literal["positive", "negative"] | None
type DataSourceName = Literal["gfit", "mfp"]


class WeightEntry(BaseModel):
    user_id: UUID
    entry_date: dt.date
    weight: float


class WeeklyAggregateEntry(BaseModel):
    week_start: dt.date
    avg_weight: float
    weight_change: float
    weight_change_prc: float
    net_calories: int
    result: Result


class ProgressMetrics(BaseModel):
    total_change: float
    avg_change: float
    avg_change_prc: float
    avg_net_calories: int


class ProgressSummary(BaseModel):
    metrics: ProgressMetrics | None = None
    latest_week: WeeklyAggregateEntry | None = None


class DataStorage(Protocol):
    def get_weight_entries(self, user_id: UUID) -> list[WeightEntry]: ...

    def get_weight_entry(
        self, user_id: UUID, entry_date: dt.date
    ) -> WeightEntry | None: ...

    def create_weight_entries(self, entries: Iterable[WeightEntry]) -> None: ...

    def create_weight_entry(
        self, user_id: UUID, entry_date: dt.date, weight: float | int
    ) -> None: ...

    def delete_weight_entry(self, user_id: UUID, entry_date: dt.date) -> None: ...

    def update_weight_entry(
        self, user_id: UUID, entry_date: dt.date, weight: float | int
    ) -> None: ...

    def export_to_csv(self, user_id: UUID) -> None: ...

    def store_google_credentials(self, user_id: UUID, creds: Credentials) -> None: ...

    def load_google_credentials(self, user_id: UUID) -> Credentials | None: ...

    def close_connection(self) -> None: ...


class DataSourceClient(Protocol):
    def get_raw_data(
        self, date_from: str | None = None, date_to: str | None = None
    ) -> Any: ...

    def store_raw_data(self, raw_dataset: Any) -> None: ...

    def convert_to_daily_entries(self, raw_dataset: Any) -> list[WeightEntry]: ...


class DuplicateEntryError(ValueError):
    pass


class EntryNotFoundError(ValueError):
    pass
