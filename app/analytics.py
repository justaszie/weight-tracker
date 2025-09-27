from collections.abc import Sequence

import pandas as pd

from .project_types import (
    FitnessGoal,
    ProgressMetrics,
    Result,
    WeeklyAggregateEntry,
    WeightEntry,
)

MAINTAIN_ACCEPTABLE_CHANGE = 0.2


def get_weekly_aggregates(
    daily_entries: Sequence[WeightEntry], goal: FitnessGoal
) -> list[WeeklyAggregateEntry]:
    def weight_change_to_result(weight_change: float) -> Result:
        return calculate_result(weight_change, goal)

    if len(daily_entries) == 0:
        return []

    # 1. Convert daily_entries DTO list to data frame
    df = pd.DataFrame([entry.model_dump() for entry in daily_entries])

    # Set date index to aggregate by week
    df["week_start"] = pd.to_datetime(df["entry_date"])
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
        (weekly_entries["weight_change"] * 500 / 0.45)  # pyright: ignore[reportUnknownMemberType]
        .round(0)
        .fillna(0)
        .astype(int)
    )

    # Add positive / negative result based on goal
    weekly_entries["result"] = weekly_entries["weight_change"].apply(  # pyright: ignore[reportUnknownMemberType]
        weight_change_to_result
    )

    # Reset index to keep date as a column
    # and convert it to simple datetime type
    weekly_entries.reset_index(inplace=True)
    weekly_entries["week_start"] = weekly_entries["week_start"].dt.date

    records = weekly_entries.to_dict(  # pyright: ignore[reportUnknownMemberType]
        orient="records"
    )

    return [WeeklyAggregateEntry.model_validate(record) for record in records]


def get_summary(
    weekly_entries: list[WeeklyAggregateEntry],
) -> ProgressMetrics | None:
    if len(weekly_entries) == 0:
        return None

    # Sorting the weekly entries in descending order so the reference week is excluded
    sorted_weekly_entries = sorted(
        weekly_entries, key=lambda entry: entry.week_start, reverse=True
    )

    weekly_entries_df = pd.DataFrame(
        [entry.model_dump() for entry in sorted_weekly_entries]
    )

    multiple_entries: bool = len(weekly_entries_df.index) > 1

    summary = ProgressMetrics(
        total_change=(
            round(float(weekly_entries_df["weight_change"].iloc[:-1].sum()), 2)
            if multiple_entries
            else 0.0
        ),
        avg_change=(
            round(float(weekly_entries_df["weight_change"].iloc[:-1].mean()), 2)
            if multiple_entries
            else 0.0
        ),
        avg_change_prc=(
            round(float(weekly_entries_df["weight_change_prc"].iloc[:-1].mean()), 2)
            if multiple_entries
            else 0.0
        ),
        avg_net_calories=(
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
