import datetime as dt


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
    latest_date_str = sorted(daily_entries, key=lambda x: x["date"])[-1]["date"]
    return dt.date.fromisoformat(latest_date_str)
