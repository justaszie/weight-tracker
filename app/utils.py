import datetime as dt
import traceback
from typing import Tuple
from collections.abc import Iterable
from project_types import (
    DailyWeightEntry,
    DataSourceName,
    FitnessGoal,
    ToastMessageCategory,
)

DATA_SOURCES_SUPPORTED: list[DataSourceName] = ["gfit", "mfp"]
GOALS_SUPPORTED: list[FitnessGoal] = ["lose", "gain", "maintain"]

REFERENCE_WEEK_DATA: dict[str, float | int | None]  = {
    "weight_change": 0.0,
    "weight_change_prc": 0.0,
    "net_calories": 0,
    "result": None,
}

DEFAULT_GOAL = "lose"
DEFAULT_WEEKS_LIMIT = 4  # used in app.py
DEFAULT_DATA_SOURCE = "gfit"


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
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> list[DailyWeightEntry]:
    if date_from:
        daily_entries = [entry for entry in daily_entries if entry["date"] >= date_from]
    if date_to:
        daily_entries = [entry for entry in daily_entries if entry["date"] <= date_to]
    return list(daily_entries)


def get_latest_entry_date(
    daily_entries: Iterable[DailyWeightEntry],
) -> dt.date | None:
    if not daily_entries:
        return None

    try:
        return sorted(daily_entries, key=lambda x: x["date"])[-1].get("date", None)
    except Exception:
        traceback.print_exc()
        return None


def get_latest_daily_entry(
    daily_entries: Iterable[DailyWeightEntry],
) -> DailyWeightEntry | None:
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


def parse_iso_date(date_str: str | None) -> None | dt.date:
    if not date_str:
        return None

    try:
        return dt.date.fromisoformat(date_str.strip())
    except:
        raise ValueError("Invalid Date")


def validate_date_range(date_from: dt.date | None, date_to: dt.date | None) -> None:
    if date_from and date_to and date_from > date_to:
        raise DateRangeError('"Date To" must be after "Date From"')


def parse_date_filters(date_from: str | None, date_to: str | None) -> Tuple[dt.date | None, dt.date | None]:
    try:
        date_from_parsed: dt.date | None = parse_iso_date(date_from)
    except ValueError:
        raise InvalidDateError('"Date From" must be a valid date')
    try:
        date_to_parsed: dt.date | None = parse_iso_date(date_to)
    except ValueError:
        raise InvalidDateError('"Date To" must be a valid date"')

    try:
        validate_date_range(date_from_parsed, date_to_parsed)
        return (date_from_parsed, date_to_parsed)
    except:
        raise