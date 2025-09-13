import datetime as dt
from typing import Literal, Protocol, TypedDict
from pydantic import BaseModel

type FitnessGoal = Literal["gain", "lose", "maintain"]
type Result = Literal["positive", "negative"] | None
type DataSourceName = Literal["gfit", "mfp"]
type ToastMessageCategory = Literal["info", "success", "error"]


# class WeightEntry(TypedDict):
#     date: dt.date
#     weight: float


class WeightEntry(BaseModel):
    date: dt.date
    weight: float


class APIDailyWeightEntry(TypedDict):
    date: str
    weight: float


class WeeklyAggregateEntry(BaseModel):
    week_start: dt.date
    avg_weight: float
    weight_change: float
    weight_change_prc: float
    net_calories: int
    result: Result


class ProgressSummaryMetrics(BaseModel):
    total_change: float
    avg_change: float
    avg_change_prc: float
    avg_net_calories: int


class ProgressSummary(BaseModel):
    metrics: ProgressSummaryMetrics | None = None


class APIWeeklyAggregateEntry(TypedDict):
    week_start: str
    avg_weight: float
    weight_change: float
    weight_change_prc: float
    net_calories: int
    result: Result


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
    ) -> dict[dt.date, float]: ...

    def store_raw_data(self, raw_data: dict[dt.date, float]) -> None: ...

    def convert_to_daily_entries(
        self, raw_data: dict[dt.date, float]
    ) -> list[WeightEntry]: ...
