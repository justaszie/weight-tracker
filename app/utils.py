import datetime as dt
import traceback
from typing import Optional, Tuple

DATA_SOURCES_SUPPORTED = ["gfit", "mfp"]
GOALS_SUPPORTED = ["lose", "gain", "maintain"]

REFERENCE_WEEK_DATA = {
    "weight_change": 0,
    "weight_change_prc": 0,
    "net_calories": 0,
    "result": None,
}


DEFAULT_GOAL = "lose"
DEFAULT_WEEKS_LIMIT = 4
DEFAULT_DATA_SOURCE = "gfit"


class InvalidDateError(Exception):
    pass


class DateRangeError(Exception):
    pass

class InvalidWeeksLimit(Exception):
    pass


def to_signed_amt_str(amount, decimals=True) -> str:
    return ("+" if amount >= 0 else "-") + (
        f"{abs(amount):.2f}" if decimals else str(abs(amount))
    )


def filter_daily_entries(daily_entries, date_from=None, date_to=None):
    if date_from:
        daily_entries = [entry for entry in daily_entries if entry["date"] >= date_from]
    if date_to:
        daily_entries = [entry for entry in daily_entries if entry["date"] <= date_to]
    return daily_entries


def get_latest_entry_date(daily_entries) -> dt.date:
    if not daily_entries:
        return None

    try:
        return sorted(daily_entries, key=lambda x: x["date"])[-1].get("date", None)
    except Exception:
        traceback.print_exc()
        return None


def get_latest_daily_entry(daily_entries) -> dt.date:
    if not daily_entries:
        return None

    try:
        return sorted(daily_entries, key=lambda x: x["date"])[-1]
    except Exception:
        traceback.print_exc()
        return None


def message_category_to_class_name(category):
    return {
        "info": "flash__message--info",
        "error": "flash__message--error",
        "success": "flash__message--success",
    }.get(category, "flash__message--info")


def is_valid_weeks_filter(value):
    try:
        return int(value) > 0
    except:
        return False


def is_valid_goal_selection(goal):
    return goal.lower() in GOALS_SUPPORTED


def is_valid_data_source(source):
    return source.lower() in DATA_SOURCES_SUPPORTED


def parse_iso_date(date_str):
    if not date_str:
        return None

    try:
        return dt.date.fromisoformat(date_str.strip())
    except:
        raise ValueError("Invalid Date")


def validate_date_range(date_from, date_to):
    if date_from and date_to and date_from > date_to:
        raise DateRangeError('"Date To" must be after "Date From"')


def parse_date_filters(
    date_from: Optional[str], date_to: Optional[str]
) -> Tuple[Optional[dt.date], Optional[dt.date]]:
    try:
        date_from_parsed = parse_iso_date(date_from)
    except ValueError:
        raise InvalidDateError('"Date From" must be a valid date')
    try:
        date_to_parsed = parse_iso_date(date_to)
    except ValueError:
        raise InvalidDateError('"Date To" must be a valid date')

    try:
        validate_date_range(date_from_parsed, date_to_parsed)
    except:
        raise

    return (date_from_parsed, date_to_parsed)