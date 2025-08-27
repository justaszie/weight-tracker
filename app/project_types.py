
from datetime import date
from typing import Literal, TypedDict

type FitnessGoal = Literal["gain", "lose", "maintain"]
type Result = Literal["positive", "negative", None]
type DataSource = Literal['gfit', 'mfp']
type ToastMessageCategory = Literal['info', 'success', 'error']


class DailyWeightEntry(TypedDict):
    date: date
    weight: float


class WeeklyAggregateEntry(TypedDict, total=False):
    week_start: date
    avg_weight: float
    weight_change: float
    weight_change_prc: float
    net_calories: int
    result: Result


class ProgressSummary(TypedDict):
    total_change: float
    avg_change: float
    avg_change_prc: float
    avg_net_calories: int
