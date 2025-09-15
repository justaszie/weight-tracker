import datetime as dt
from typing import Any, Literal, Protocol
from pydantic import BaseModel

type FitnessGoal = Literal["gain", "lose", "maintain"]
type Result = Literal["positive", "negative"] | None
type DataSourceName = Literal["gfit", "mfp"]


class WeightEntry(BaseModel):
    date: dt.date
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


class DataStorage(Protocol):
    def get_weight_entries(self) -> list[WeightEntry]: ...

    def get_weight_entry(self, date: dt.date) -> WeightEntry | None: ...

    def create_weight_entry(self, date: dt.date, weight: float | int) -> None: ...

    def delete_weight_entry(self, date: dt.date) -> None: ...

    def update_weight_entry(self, date: dt.date, weight: float | int) -> None: ...

    def export_to_csv(self) -> None: ...

    def data_refresh_needed(self) -> bool: ...


class DataSourceClient(Protocol):
    def get_raw_data(
        self, date_from: str | None = None, date_to: str | None = None
    ) -> Any: ...

    def store_raw_data(self, raw_dataset: Any) -> None: ...

    def convert_to_daily_entries(
        self, raw_dataset: Any
    ) -> list[WeightEntry]: ...
