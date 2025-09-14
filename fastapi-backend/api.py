import datetime as dt
import traceback
from collections.abc import Sequence
from typing import Annotated, Any, Literal, cast
from typing_extensions import Self
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)
from google.oauth2.credentials import Credentials

import analytics
import utils
from data_integration import (
    DataIntegrationService,
    DataSyncError,
    SourceFetchError,
    SourceNoDataError,
)
from file_storage import FileStorage
from google_fit import GoogleFitAuth, GoogleFitClient
from mfp import MyFitnessPalClient
from project_types import (
    APIDailyWeightEntry,
    APIWeeklyAggregateEntry,
    DataSourceClient,
    FitnessGoal,
    ProgressSummary,
    ProgressSummaryMetrics,
    WeeklyAggregateEntry,
    WeightEntry,
)
from pydantic import (
    BaseModel,
    # field_validator,
    model_validator,
)


# class DailyEntriesRequestParams(BaseModel):
#     date_from: dt.date | None = None
#     date_to: dt.date | None = None

#     @model_validator(mode="after")
#     def validate_date_params(self) -> Self:
#         if self.date_from > self.date_to:
#             raise ValueError('"Date To" must be after "Date From"')
#         return self


class WeeklyAggregateResponse(BaseModel):
    weekly_data: list[WeeklyAggregateEntry]
    goal: FitnessGoal


MFP_SOURCE_NAME = "mfp"
GFIT_SOURCE_NAME = "gfit"

# REFERENCE_WEEK_DATA: dict[str, int | float | None] =

router = APIRouter()


def get_filtered_daily_entries(
    date_from: dt.date | None = None, date_to: dt.date | None = None
) -> list[WeightEntry]:
    data_storage = FileStorage()
    filtered_daily_entries = daily_entries = data_storage.get_weight_entries()

    if date_from is not None or date_to is not None:
        filtered_daily_entries = utils.filter_daily_entries(
            daily_entries, date_from, date_to
        )

    return filtered_daily_entries


def get_filtered_weekly_entries(
    daily_entries: Sequence[WeightEntry],
    goal: FitnessGoal,
    weeks_limit: int | None,
) -> list[WeeklyAggregateEntry]:

    weekly_entries = analytics.get_weekly_aggregates(daily_entries, goal)
    if not weekly_entries:
        return []

    # Sort the weeks starting from the  most recent:
    weekly_entries.sort(key=lambda week: week.week_start, reverse=True)

    if weeks_limit:
        # Keeping N + 1 weeks because the last week
        # is used as reference point to compare against, as starting point
        weekly_entries = weekly_entries[0 : weeks_limit + 1]

    last_week = weekly_entries[-1]
    reference_week = last_week.model_copy(
        update={
            "weight_change": 0.0,
            "weight_change_prc": 0.0,
            "net_calories": 0,
            "result": None,
        }
    )
    weekly_entries[-1] = reference_week

    return weekly_entries


@router.get("/daily-entries", response_model=list[WeightEntry])
def get_daily_entries(
    date_from: dt.date | None = None, date_to: dt.date | None = None
) -> list[WeightEntry]:

    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=422, detail="'Date To' must be after 'Date From'"
        )

    try:
        body: list[WeightEntry] = get_filtered_daily_entries(
            date_from=date_from, date_to=date_to
        )
        return body
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error while getting weight data")


@router.get("/weekly-aggregates", response_model=WeeklyAggregateResponse)
def get_weekly_aggregates(
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    weeks_limit: Annotated[int | None, Query(gt=0)] = None,
    goal: FitnessGoal | None = None,
) -> WeeklyAggregateResponse:

    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=422, detail="'Date To' must be after 'Date From'"
        )
    try:
        daily_entries = get_filtered_daily_entries(date_from, date_to)
        if not goal:
            goal = utils.DEFAULT_GOAL

        weekly_entries: list[WeeklyAggregateEntry] = get_filtered_weekly_entries(
            daily_entries, goal, weeks_limit
        )

        body = WeeklyAggregateResponse(weekly_data=weekly_entries, goal=goal)

        return body
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="Error while getting analytics data"
        )


@router.get("/summary", response_model=ProgressSummary)
def get_summary(
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    weeks_limit: Annotated[int | None, Query(gt=0)] = None,
) -> ProgressSummary:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=422, detail="'Date To' must be after 'Date From'"
        )

    try:
        daily_entries = get_filtered_daily_entries(date_from, date_to)

        weekly_entries = get_filtered_weekly_entries(
            daily_entries, utils.DEFAULT_GOAL, weeks_limit
        )
        summary_metrics = analytics.get_summary(weekly_entries)
        body = ProgressSummary(metrics=summary_metrics)

        return body
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="Error while getting analytics data"
        )


@router.get("/latest-entry", response_model=(WeightEntry | None))
def get_latest_entry() -> WeightEntry | None:
    try:
        data_storage = FileStorage()
        daily_entries = data_storage.get_weight_entries()
        latest_daily_entry = utils.get_latest_daily_entry(daily_entries)

        return latest_daily_entry
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error while getting weight data")
