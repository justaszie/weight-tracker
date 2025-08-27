import pandas as pd
from collections.abc import Sequence, Callable
from project_types import (
    FitnessGoal,
    Result,
    DailyWeightEntry,
    WeeklyAggregateEntry,
    ProgressSummary,
)

MAINTAIN_ACCEPTABLE_CHANGE = 0.2


def get_weekly_aggregates(
    daily_entries: Sequence[DailyWeightEntry], goal: FitnessGoal
) -> list[WeeklyAggregateEntry]:
    # Return value - Weekly entries in descending order (most recent to oldest

    # 1. Convert daily_entries JSON to data frame
    df: pd.DataFrame = pd.DataFrame.from_records(daily_entries)  # type: ignore

    # Set date index to aggregate by week
    df["week_start"] = pd.to_datetime(df["date"])
    df.set_index("week_start", inplace=True)  # type: ignore

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
    weekly_entries["weight_change"] = weekly_entries.diff().round(2).fillna(0)  # type: ignore

    # Calculate % of weight change compared to previous week
    weekly_entries["weight_change_prc"] = (
        (weekly_entries["weight_change"] / weekly_entries["avg_weight"] * 100)
        .round(2)
        .fillna(0)  # type: ignore
    )

    # Calculate estimated calorie deficit based on weight change
    weekly_entries["net_calories"] = (
        (weekly_entries["weight_change"] * 500 / 0.45).round(0).fillna(0).astype(int)  # type: ignore
    )

    weight_change_to_result: Callable[[float], Result] = lambda x: calculate_result(
        x, goal
    )
    # Add positive / negative result based on goal
    weekly_entries["result"] = weekly_entries["weight_change"].apply(  # type: ignore
        weight_change_to_result
    )

    # Reset index to keep date as a column
    # and convert it to simple datetime type
    weekly_entries.reset_index(inplace=True)
    weekly_entries["week_start"] = weekly_entries["week_start"].dt.date

    # Display in the order from the most recent
    weekly_entries = weekly_entries[::-1]

    result: list[WeeklyAggregateEntry] = weekly_entries.to_dict(orient="records")  # pyright: ignore

    return result


def get_summary(weekly_entries: Sequence[WeeklyAggregateEntry]) -> ProgressSummary:
    weekly_entries_df: pd.DataFrame = pd.DataFrame.from_records(weekly_entries)  # type: ignore

    multiple_entries: bool = len(weekly_entries_df.index) > 1

    summary: ProgressSummary = {
        "total_change": (
            round(float(weekly_entries_df["weight_change"].iloc[:-1].sum()), 2)
            if multiple_entries
            else 0.0
        ),
        "avg_change": (
            round(float(weekly_entries_df["weight_change"].iloc[:-1].mean()), 2)
            if multiple_entries
            else 0.0
        ),
        "avg_change_prc": (
            round(float(weekly_entries_df["weight_change_prc"].iloc[:-1].mean()), 2)
            if multiple_entries
            else 0.0
        ),
        "avg_net_calories": (
            int(weekly_entries_df["net_calories"].iloc[:-1].mean())
            if multiple_entries
            else 0
        ),
    }

    return summary


def calculate_result(weight_change: float, goal: FitnessGoal) -> Result:
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


# TODO - Here we will implement the logic to build text that evaluates the overall results
def get_evaluation(weekly_data: Sequence[WeeklyAggregateEntry]) -> str | None:
    return None
