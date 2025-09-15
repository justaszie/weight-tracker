import datetime as dt
import traceback
from collections.abc import Iterable

from .project_types import (
    DataSourceName,
    FitnessGoal,
    WeightEntry,
)

DATA_SOURCES_SUPPORTED: list[DataSourceName] = ["gfit", "mfp"]
GOALS_SUPPORTED: list[FitnessGoal] = ["lose", "gain", "maintain"]
DEFAULT_GOAL: FitnessGoal = "lose"


def filter_daily_entries(
    daily_entries: Iterable[WeightEntry],
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> list[WeightEntry]:
    if date_from:
        daily_entries = [entry for entry in daily_entries if entry.date >= date_from]
    if date_to:
        daily_entries = [entry for entry in daily_entries if entry.date <= date_to]
    return list(daily_entries)


def get_latest_entry_date(
    daily_entries: Iterable[WeightEntry],
) -> dt.date | None:
    if not daily_entries:
        return None

    try:
        return sorted(daily_entries, key=lambda x: x.date)[-1].date
    except Exception:
        traceback.print_exc()
        return None


def get_latest_daily_entry(
    daily_entries: Iterable[WeightEntry],
) -> WeightEntry | None:
    if not daily_entries:
        return None

    try:
        return sorted(daily_entries, key=lambda x: x.date)[-1]
    except Exception:
        traceback.print_exc()
        return None
