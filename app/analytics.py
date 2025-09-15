from collections.abc import Hashable, Sequence
from typing import Any

import pandas as pd

from project_types import (
    WeightEntry,
    FitnessGoal,
    ProgressSummaryMetrics,
    Result,
    WeeklyAggregateEntry,
)

MAINTAIN_ACCEPTABLE_CHANGE = 0.2


def get_weekly_aggregates(
    daily_entries: Sequence[WeightEntry], goal: FitnessGoal
) -> list[WeeklyAggregateEntry]:
    # Return value - Weekly entries in descending order (most recent to oldest

    def weight_change_to_result(weight_change: float) -> Result:
        return calculate_result(weight_change, goal)

    if len(daily_entries) == 0:
        return []

    # 1. Convert daily_entries JSON to data frame
    df: pd.DataFrame = (
        pd.DataFrame([entry.model_dump() for entry in daily_entries])  # pyright: ignore[reportUnknownMemberType]
    )

    # Set date index to aggregate by week
    df["week_start"] = pd.to_datetime(df["date"])
    df.set_index("week_start", inplace=True)  # pyright: ignore[reportUnknownMemberType]

    # Calculate weekly averages (mean and median) using resample method
    # averages = round(df['weight'].resample('W').agg(['mean','median']).dropna(), 2)
    weekly_averages: pd.Series[float] = (
        df["weight"].resample("W").mean().dropna().round(2)
    )

    # After resampling, the date of the week is end of week
    # We set the index date to beginning the week
    # (resample results in end of week so we subtract 6 days from it)
    weekly_averages.index -= pd.DateOffset(n=6)

    # Calculate the weight change between weeks
    weekly_entries: pd.DataFrame = weekly_averages.to_frame(name="avg_weight")
    weekly_entries["weight_change"] = (
        weekly_entries.diff()  # pyright: ignore[reportUnknownMemberType]
        .round(2)
        .fillna(0)
    )

    # Calculate % of weight change compared to previous week
    weekly_entries["weight_change_prc"] = (
        (weekly_entries["weight_change"] / weekly_entries["avg_weight"].shift(1) * 100)
        .round(2)
        .fillna(0)  # pyright: ignore[reportUnknownMemberType]
    )

    # Calculate estimated calorie deficit based on weight change
    weekly_entries["net_calories"] = (
        (
            weekly_entries["weight_change"] * 500 / 0.45
        )  # pyright: ignore[reportUnknownMemberType]
        .round(0)
        .fillna(0)
        .astype(int)
    )

    # Add positive / negative result based on goal
    weekly_entries["result"] = weekly_entries[
        "weight_change"
    ].apply(  # pyright: ignore[reportUnknownMemberType]
        weight_change_to_result
    )

    # Reset index to keep date as a column
    # and convert it to simple datetime type
    weekly_entries.reset_index(inplace=True)
    weekly_entries["week_start"] = weekly_entries["week_start"].dt.date

    records: list[dict[Hashable, Any]] = (
        weekly_entries.to_dict(  # pyright: ignore[reportUnknownMemberType]
            orient="records"
        )
    )

    return [
        WeeklyAggregateEntry(**record)
        # {
        #     "week_start": record["week_start"],
        #     "avg_weight": record["avg_weight"],
        #     "weight_change": record["weight_change"],
        #     "weight_change_prc": record["weight_change_prc"],
        #     "net_calories": record["net_calories"],
        #     "result": record["result"],
        # }
        for record in records
    ]


def get_summary(
    weekly_entries: list[WeeklyAggregateEntry],
) -> ProgressSummaryMetrics | None:
    if len(weekly_entries) == 0:
        return None

    weekly_entries.sort( # pyright: ignore
        key=lambda week: week.week_start, reverse=True
    )

    weekly_entries_df: pd.DataFrame = (
        pd.DataFrame.from_records(  # pyright: ignore[reportUnknownMemberType]
            [entry.model_dump() for entry in weekly_entries]
        )
    )

    multiple_entries: bool = len(weekly_entries_df.index) > 1

    summary = ProgressSummaryMetrics(
        total_change = (
            round(float(weekly_entries_df["weight_change"].iloc[:-1].sum()), 2)
            if multiple_entries
            else 0.0
        ),
        avg_change = (
            round(float(weekly_entries_df["weight_change"].iloc[:-1].mean()), 2)
            if multiple_entries
            else 0.0
        ),
        avg_change_prc = (
            round(float(weekly_entries_df["weight_change_prc"].iloc[:-1].mean()), 2)
            if multiple_entries
            else 0.0
        ),
        avg_net_calories = (
            int(weekly_entries_df["net_calories"].iloc[:-1].mean())
            if multiple_entries
            else 0
        ),
    )

    return summary


def calculate_result(weight_change: float, goal: FitnessGoal) -> Result | None:
    match goal:
        case "lose":
            return "positive" if weight_change < 0 else "negative"
        case "gain":
            return "positive" if weight_change > 0 else "negative"
        case "maintain":
            return (
                "positive"
                if abs(weight_change) <= MAINTAIN_ACCEPTABLE_CHANGE
                else "negative"
            )


# TODO - Here we will implement the logic
# to build text that evaluates the overall results
def get_evaluation(weekly_data: Sequence[WeeklyAggregateEntry]) -> str | None:
    return None
