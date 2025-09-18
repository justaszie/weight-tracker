import datetime as dt
import traceback
from collections.abc import Sequence
from typing import Annotated

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
)
from google.oauth2.credentials import Credentials
from pydantic import (
    BaseModel,
)

from . import analytics, utils
from .data_integration import (
    DataIntegrationService,
    DataSyncError,
    SourceFetchError,
    SourceNoDataError,
)
from .file_storage import FileStorage
from .google_fit import GoogleFitAuth, GoogleFitClient
from .mfp import MyFitnessPalClient
from .project_types import (
    DataSourceClient,
    DataSourceName,
    FitnessGoal,
    ProgressSummary,
    WeeklyAggregateEntry,
    WeightEntry,
)


class WeeklyAggregateResponse(BaseModel):
    weekly_data: list[WeeklyAggregateEntry]
    goal: FitnessGoal


class DataSyncRequest(BaseModel):
    data_source: DataSourceName


class DataSyncResponse(BaseModel):
    status: str
    message: str
    new_entries_count: int | None = None
    auth_url: str | None = None


MFP_SOURCE_NAME = "mfp"
GFIT_SOURCE_NAME = "gfit"

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

    # Sort the weeks starting from the  most recent
    # so we can limit the return to N most recent:
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
        body = get_filtered_daily_entries(date_from, date_to)
        return body
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="Error while getting weight data"
        ) from e


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
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="Error while getting analytics data"
        ) from e


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
        progress_metrics = analytics.get_summary(weekly_entries)
        body = ProgressSummary(metrics=progress_metrics)

        return body
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="Error while getting analytics data"
        ) from e


@router.get("/latest-entry", response_model=(WeightEntry | None))
def get_latest_entry() -> WeightEntry | None:
    try:
        data_storage = FileStorage()
        daily_entries = data_storage.get_weight_entries()
        latest_daily_entry = utils.get_latest_daily_entry(daily_entries)

        return latest_daily_entry
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="Error while getting weight data"
        ) from e


@router.post(
    "/sync-data", response_model=DataSyncResponse, response_model_exclude_unset=True
)
def sync_data(sync_request: DataSyncRequest, http_request: Request) -> DataSyncResponse:
    try:
        data_storage = FileStorage()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error while getting weight data"
        ) from e

    if not data_storage.data_refresh_needed():
        return DataSyncResponse(
            status="data_up_to_date", message="Your data is already up to date"
        )

    data_source = sync_request.data_source

    data_source_client: DataSourceClient
    if data_source == GFIT_SOURCE_NAME:
        oauth_credentials: Credentials | None = GoogleFitAuth().load_auth_token()
        if not oauth_credentials:
            return DataSyncResponse(
                status="auth_needed",
                message="Google Fit authentication needed",
                auth_url=http_request.app.url_path_for("google_signin"),
            )

        data_source_client = GoogleFitClient(oauth_credentials)

    elif data_source == MFP_SOURCE_NAME:
        data_source_client = MyFitnessPalClient()

    else:
        raise HTTPException(status_code=422, detail="Unsupported Data Source Type")

    data_integration = DataIntegrationService(data_storage, data_source_client)

    try:
        new_entries = data_integration.refresh_weight_entries(
            store_raw_copy=True, store_csv_copy=True
        )
        if new_entries:
            return DataSyncResponse(
                status="sync_success",
                message="Data updated successfully",
                new_entries_count=len(new_entries),
            )
        else:
            return DataSyncResponse(
                status="no_new_data", message="No new data was found"
            )
    except SourceNoDataError:
        return DataSyncResponse(status="no_data_received", message="No data received")
    except SourceFetchError as e:
        traceback.print_exc()
        if data_source == MFP_SOURCE_NAME:
            error_message = "We couldn't connect to MyFitnessPal. Please check \
if you're logged in and try again."
        elif data_source == GFIT_SOURCE_NAME:
            error_message = (
                "We couldn't get your data from Google Fit. Please try again later."
            )
        else:
            error_message = "We couldn't get your data. Please try again later."

        raise HTTPException(status_code=500, detail=error_message) from e
    except DataSyncError as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="We're having trouble syncing your data. \
We're working on it",
        ) from e
