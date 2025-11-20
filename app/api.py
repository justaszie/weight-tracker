import datetime as dt
import logging
import os
from collections.abc import Sequence
from typing import (
    Annotated,
    cast,
)
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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
from .demo import DemoDataSourceClient
from .google_fit import GoogleFitAuth, GoogleFitClient
from .project_types import (
    DataSourceClient,
    DataSourceName,
    DataStorage,
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


class DataSyncSuccessResponse(BaseModel):
    status: str
    message: str
    new_entries_count: int | None = None


class DataSyncAuthNeededResponse(BaseModel):
    message: str
    auth_url: str | None = None


class NoCredentialsError(Exception):
    pass


MFP_SOURCE_NAME = "mfp"
GFIT_SOURCE_NAME = "gfit"

router_v1 = APIRouter(prefix="/api/v1", tags=["v1"])

logger = logging.getLogger(__name__)

jwt_authentication = HTTPBearer(auto_error=False)


def get_data_storage(request: Request) -> DataStorage:
    return cast(DataStorage, request.app.state.data_storage)


def get_data_source_client(
    request: Request, source_name: DataSourceName, user_id: UUID
) -> DataSourceClient:
    if is_demo_user(user_id):
        return DemoDataSourceClient(user_id)

    if source_name == GFIT_SOURCE_NAME:
        data_storage = get_data_storage(request)
        oauth_credentials: Credentials | None = GoogleFitAuth().load_credentials(
            data_storage, user_id
        )
        if not oauth_credentials:
            raise NoCredentialsError("Google API credentials required")

        return GoogleFitClient(user_id, oauth_credentials)

    # elif source_name == MFP_SOURCE_NAME:
    #     return MyFitnessPalClient(user_id)

    else:
        raise ValueError("Data Source not supported")


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_authentication)],
) -> UUID:
    jwt_token = credentials.credentials
    supabase_client = request.app.state.supabase

    try:
        result = supabase_client.auth.get_user(jwt_token)
        user = result.user
        if not user:
            logger.error("No valid user matching access token")
            raise HTTPException(401, "Authentication failed")
        logger.info(f"Authenticated Request from user: {user.id}")
        return UUID(user.id)
    except Exception as e:
        logger.exception("User Authentication Failed")
        raise HTTPException(401, "Authentication failed") from e


def is_demo_user(user_id: UUID) -> bool:
    demo_user_id = os.environ.get("DEMO_USER_ID")
    if demo_user_id is None:
        logger.warning("Failed to verify demo user id - missing config")
        return False

    return UUID(demo_user_id) == user_id


DataStorageDependency = Annotated[DataStorage, Depends(get_data_storage)]
UserDependency = Annotated[UUID, Depends(get_current_user)]


def get_filtered_daily_entries(
    data_storage: DataStorage,
    user_id: UUID,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> list[WeightEntry]:
    filtered_daily_entries = daily_entries = data_storage.get_weight_entries(user_id)

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


@router_v1.get("/daily-entries", response_model=list[WeightEntry])
def get_daily_entries(
    user_id: UserDependency,
    data_storage: DataStorageDependency,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
) -> list[WeightEntry]:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=422, detail="'Date To' must be after 'Date From'"
        )

    try:
        body = get_filtered_daily_entries(data_storage, user_id, date_from, date_to)
        logger.info(f"Fetched {len(body)} daily weight entries")
        return body
    except Exception as e:
        logger.exception("Error while getting daily weight data")
        raise HTTPException(
            status_code=500, detail="Error while getting daily weight data"
        ) from e


@router_v1.get("/weekly-aggregates", response_model=WeeklyAggregateResponse)
def get_weekly_aggregates(
    data_storage: DataStorageDependency,
    user_id: UserDependency,
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
        daily_entries = get_filtered_daily_entries(
            data_storage, user_id, date_from, date_to
        )
        if not goal:
            goal = utils.DEFAULT_GOAL

        weekly_entries: list[WeeklyAggregateEntry] = get_filtered_weekly_entries(
            daily_entries, goal, weeks_limit
        )
        logger.info(
            f"Calculated weekly weight aggregates for {len(weekly_entries)} + 1 weeks"
        )

        body = WeeklyAggregateResponse(weekly_data=weekly_entries, goal=goal)
        return body
    except Exception as e:
        logger.exception("Calculating weekly aggregates failed")
        raise HTTPException(
            status_code=500, detail="Error while getting analytics data"
        ) from e


@router_v1.get("/summary", response_model=ProgressSummary)
def get_summary(
    user_id: UserDependency,
    data_storage: DataStorageDependency,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    weeks_limit: Annotated[int | None, Query(gt=0)] = None,
) -> ProgressSummary:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=422, detail="'Date To' must be after 'Date From'"
        )

    try:
        daily_entries = get_filtered_daily_entries(
            data_storage, user_id, date_from, date_to
        )

        weekly_entries = get_filtered_weekly_entries(
            daily_entries, utils.DEFAULT_GOAL, weeks_limit
        )
        progress_metrics = analytics.get_summary(weekly_entries)
        logger.info(
            f"Weight progress metrics calculated for {len(weekly_entries)} + 1 weeks"
        )

        body = ProgressSummary(metrics=progress_metrics)
        return body
    except Exception as e:
        logger.exception("Fetching weight progress summary failed")
        raise HTTPException(
            status_code=500, detail="Error while getting analytics data"
        ) from e


@router_v1.get("/latest-entry", response_model=(WeightEntry | None))
def get_latest_entry(
    user_id: UserDependency,
    data_storage: DataStorageDependency,
) -> WeightEntry | None:
    try:
        daily_entries = data_storage.get_weight_entries(user_id)
        latest_daily_entry = utils.get_latest_daily_entry(daily_entries)
        if latest_daily_entry:
            logger.info(
                f"Latest weight entry fetched: {latest_daily_entry.model_dump()}"
            )
        else:
            logger.warning("No latest weight entry found")
        return latest_daily_entry
    except Exception as e:
        logger.exception("Fetching latest daily weight entry failed")
        raise HTTPException(
            status_code=500, detail="Error while getting weight data"
        ) from e


@router_v1.post(
    "/sync-data",
    response_model=DataSyncSuccessResponse,
    response_model_exclude_unset=True,
    responses={
        401: {
            "model": DataSyncAuthNeededResponse,
            "description": "Data Source requires authentication",
        }
    },
)
def sync_data(
    user_id: UserDependency,
    sync_request: DataSyncRequest,
    http_request: Request,
    data_storage: DataStorageDependency,
) -> DataSyncSuccessResponse | JSONResponse:
    if not data_storage.data_refresh_needed(user_id):
        logger.info("Data sync skipped - already up to date")
        return DataSyncSuccessResponse(
            status="data_up_to_date", message="Your data is already up to date"
        )

    logger.info(f"Starting weights data sync for source: {sync_request.data_source}")
    data_source = sync_request.data_source

    try:
        data_source_client = get_data_source_client(http_request, data_source, user_id)
        logger.info(
            "Data Source client for syncing initialized:"
            f" {data_source_client.__class__.__name__}"
        )
    except NoCredentialsError:
        logger.warning("Google Fit credentials missing or expired")
        return JSONResponse(
            status_code=401,
            content={
                "message": "Google Fit authentication needed",
                "auth_url": (
                    f"{http_request.app.url_path_for('google_signin')}?user_id={user_id}"
                ),
            },
        )

    data_integration = DataIntegrationService(data_storage, data_source_client)

    try:
        new_entries = data_integration.refresh_weight_entries(
            user_id, store_raw_copy=False
        )
        if new_entries:
            logger.info(f"Weight data synced with {len(new_entries)} new entry(ies)")
            return DataSyncSuccessResponse(
                status="sync_success",
                message="Data updated successfully",
                new_entries_count=len(new_entries),
            )
        else:
            logger.info("No new data found when syncing weight entries")
            return DataSyncSuccessResponse(
                status="no_new_data", message="No new data was found"
            )
    except SourceNoDataError:
        logger.info("No weights data was received from source")
        return DataSyncSuccessResponse(
            status="no_data_received", message="No data received"
        )
    except SourceFetchError as e:
        logger.exception("Fetching weight data from source failed")
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
        logger.exception("Syncing weight data failed")
        raise HTTPException(
            status_code=500,
            detail="We're having trouble syncing your data. \
We're working on it",
        ) from e


@router_v1.get("/healthz")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
