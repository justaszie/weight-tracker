import datetime as dt
import traceback
from collections.abc import Sequence
from typing import Any, Literal, cast
from typing_extensions import Self
from fastapi import (
    APIRouter,
    HTTPException,
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


MFP_SOURCE_NAME = "mfp"
GFIT_SOURCE_NAME = "gfit"

REFERENCE_WEEK_DATA: dict[str, int | float | None] = {
    "weight_change": 0.0,
    "weight_change_prc": 0.0,
    "net_calories": 0,
    "result": None,
}

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
    weeks_limit_param: str | None,
) -> list[WeeklyAggregateEntry]:
    """

    Raises:
        utils.InvalidWeeksLimit: if the weeks limit filter parameter is invalid
    """
    weekly_entries = analytics.get_weekly_aggregates(daily_entries, goal)
    if not weekly_entries:
        return []

    # Sort the weeks starting from the  most recent:
    weekly_entries.sort(key=lambda week: week["week_start"], reverse=True)

    if weeks_limit_param:
        if not utils.is_valid_weeks_filter(weeks_limit_param):
            raise utils.InvalidWeeksLimit

        weeks_limit = int(weeks_limit_param)
        # Keeping N + 1 weeks because the last week
        # is used as reference point to compare against, as starting point
        weekly_entries = weekly_entries[0 : weeks_limit + 1]

    last_week = weekly_entries[-1]
    last_week.update(cast(WeeklyAggregateEntry, REFERENCE_WEEK_DATA))

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
        body: list[WeightEntry] = get_filtered_daily_entries(date_from=date_from, date_to=date_to)
        # body: list[WeightEntry] = [
        #     {
        #         "date": entry["date"],
        #         "weight": entry["weight"],
        #     }
        #     for entry in daily_entries
        # ]
        return body
    except:
        traceback.print_exc()
        raise HTTPException(status_code=500)
    # except (utils.InvalidDateError, utils.DateRangeError) as e:
    #     return jsonify({"error_message": str(e)}), 400
    # except Exception:
    #     traceback.print_exc()
    #     return jsonify({"error_message": "Error while getting weight data"}), 500
