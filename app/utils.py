import datetime as dt
import logging
from collections.abc import Sequence

from .project_types import (
    FitnessGoal,
    WeightEntry,
)

logger = logging.getLogger(__name__)

DEFAULT_GOAL: FitnessGoal = "lose"


def filter_daily_entries(
    daily_entries: Sequence[WeightEntry],
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> list[WeightEntry]:
    if date_from:
        daily_entries = [
            entry for entry in daily_entries if entry.entry_date >= date_from
        ]
    if date_to:
        daily_entries = [
            entry for entry in daily_entries if entry.entry_date <= date_to
        ]
    return list(daily_entries)


def get_latest_entry_date(
    daily_entries: Sequence[WeightEntry],
) -> dt.date | None:
    if not daily_entries:
        return None

    try:
        return sorted(daily_entries, key=lambda x: x.entry_date)[-1].entry_date
    except Exception:
        logger.warning(
            "Failed to get the date of the latest weight entry",
            exc_info=True,
            extra={
                "entries_count": len(daily_entries),
            },
        )
        return None


def get_latest_daily_entry(
    daily_entries: Sequence[WeightEntry],
) -> WeightEntry | None:
    if not daily_entries:
        return None

    try:
        return sorted(daily_entries, key=lambda x: x.entry_date)[-1]
    except Exception:
        logger.warning(
            "Failed to get the latest weight entry",
            exc_info=True,
            extra={
                "entries_count": len(daily_entries),
            },
        )
        return None
