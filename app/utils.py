import datetime as dt

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
        daily_entries = [entry for entry in daily_entries if entry["date"].strftime("%Y-%m-%d") >= date_from]
    if date_to:
        daily_entries = [entry for entry in daily_entries if entry["date"].strftime("%Y-%m-%d") <= date_to]
    return daily_entries


def get_latest_entry_date(daily_entries) -> dt.date:
    return sorted(daily_entries, key=lambda x: x["date"])[-1].get(
        "date", None
    )

def message_category_to_class_name(category):
    return {
        'info': 'flash__message--info',
        'error': 'flash__message--error',
        'success': 'flash__message--success',
    }.get(category, 'info')
