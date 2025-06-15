import datetime as dt
import traceback

DATA_SOURCES_SUPPORTED = ['gfit', 'mfp']
GOALS_SUPPORTED = ['lose', 'gain', 'maintain']

REFERENCE_WEEK_DATA = {
    "weight_change": 0,
    "weight_change_prc": 0,
    "net_calories": 0,
    "result": None,
}

def to_signed_amt_str(amount, decimals=True) -> str:
    return ("+" if amount >= 0 else "-") + (
        f"{abs(amount):.2f}" if decimals else str(abs(amount))
    )


def filter_daily_entries(daily_entries, date_from=None, date_to=None):
    if date_from:
        daily_entries = [
            entry
            for entry in daily_entries
            if entry["date"].strftime("%Y-%m-%d") >= date_from
        ]
    if date_to:
        daily_entries = [
            entry
            for entry in daily_entries
            if entry["date"].strftime("%Y-%m-%d") <= date_to
        ]
    return daily_entries


def get_latest_entry_date(daily_entries) -> dt.date:
    if not daily_entries:
        return None

    try:
        return sorted(daily_entries, key=lambda x: x["date"])[-1].get("date", None)
    except Exception:
        traceback.print_exc()
        return None

def  get_latest_daily_entry(daily_entries) -> dt.date:
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

def date_filter_error(date_from_str, date_to_str):
    if date_from_str:
        try:
            date_from = dt.date.fromisoformat(date_from_str)
        except:
            return '"Date From" must be a valid date'

    if date_to_str:
        try:
            date_to = dt.date.fromisoformat(date_to_str)
        except:
            return '"Date To" must be a valid date'

    if date_from_str:
        if date_to_str and date_to < date_from:
            return '"Date To" must be after "Date From"'
        elif date_from > dt.date.today():
            return '"Date From" cannot be in the future'

    return None
