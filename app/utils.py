import datetime as dt
import traceback
from typing import Optional, Tuple
from collections.abc import Iterable
from project_types import (
    DailyWeightEntry,
    WeeklyAggregateEntry,
    DataSource,
    FitnessGoal,
    ToastMessageCategory,
)

DATA_SOURCES_SUPPORTED: list[DataSource] = ["gfit", "mfp"]
GOALS_SUPPORTED: list[FitnessGoal] = ["lose", "gain", "maintain"]

REFERENCE_WEEK_DATA: WeeklyAggregateEntry = {
    "weight_change": 0.0,
    "weight_change_prc": 0.0,
    "net_calories": 0,
    "result": None,
}

DEFAULT_GOAL: FitnessGoal = "lose"
DEFAULT_WEEKS_LIMIT: int = 4  # used in app.py
DEFAULT_DATA_SOURCE: DataSource = "gfit"


class InvalidDateError(Exception):
    pass


class DateRangeError(Exception):
    pass


class InvalidWeeksLimit(Exception):
    pass


# TODO - to be removed - used by templates
def to_signed_amt_str(amount: float | int, decimals: bool = True) -> str:
    return ("+" if amount >= 0 else "-") + (
        f"{abs(amount):.2f}" if decimals else str(abs(amount))
    )


def filter_daily_entries(
    daily_entries: Iterable[DailyWeightEntry],
    date_from: Optional[dt.date] = None,
    date_to: Optional[dt.date] = None,
) -> list[DailyWeightEntry]:
    if date_from:
        daily_entries = [entry for entry in daily_entries if entry["date"] >= date_from]
    if date_to:
        daily_entries = [entry for entry in daily_entries if entry["date"] <= date_to]
    return list(daily_entries)


def get_latest_entry_date(
    daily_entries: Iterable[DailyWeightEntry],
) -> Optional[dt.date]:
    if not daily_entries:
        return None

    try:
        return sorted(daily_entries, key=lambda x: x["date"])[-1].get("date", None)
    except Exception:
        traceback.print_exc()
        return None


def get_latest_daily_entry(
    daily_entries: Iterable[DailyWeightEntry],
) -> Optional[DailyWeightEntry]:
    if not daily_entries:
        return None

    try:
        return sorted(daily_entries, key=lambda x: x["date"])[-1]
    except Exception:
        traceback.print_exc()
        return None


def message_category_to_class_name(category: ToastMessageCategory) -> str:
    return {
        "info": "flash__message--info",
        "error": "flash__message--error",
        "success": "flash__message--success",
    }.get(category, "flash__message--info")


def is_valid_weeks_filter(value: int | str) -> bool:
    try:
        return int(value) > 0
    except:
        return False


def is_valid_goal_selection(goal: str) -> bool:
    return goal.lower() in GOALS_SUPPORTED


def is_valid_data_source(source: str) -> bool:
    return source.lower() in DATA_SOURCES_SUPPORTED


def parse_iso_date(date_str: Optional[str]) -> None | dt.date:
    if not date_str:
        return None

    try:
        return dt.date.fromisoformat(date_str.strip())
    except:
        raise ValueError("Invalid Date")


def validate_date_range(date_from: Optional[dt.date], date_to: Optional[dt.date]) -> None:
    if date_from and date_to and date_from > date_to:
        raise DateRangeError('"Date To" must be after "Date From"')


def parse_date_filters(
    date_from: Optional[str], date_to: Optional[str]
) -> Tuple[Optional[dt.date], Optional[dt.date]]:
    try:
        date_from_parsed: dt.date | None = parse_iso_date(date_from)
    except ValueError:
        raise InvalidDateError('"Date From" must be a valid date')
    try:
        date_to_parsed: dt.date | None = parse_iso_date(date_to)
    except ValueError:
        raise InvalidDateError('"Date To" must be a valid date')

    try:
        validate_date_range(date_from_parsed, date_to_parsed)
    except:
        raise

    return (date_from_parsed, date_to_parsed)
