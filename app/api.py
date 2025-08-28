from flask import Blueprint, jsonify, request, url_for
from project_types import WeeklyAggregateEntry
from google_fit import GoogleFitAuth, GoogleFitClient
from data_integration import (
    DataIntegrationService,
    DataSyncError,
    SourceFetchError,
    SourceNoDataError,
)
from project_types import (
    DailyWeightEntry,
)
# from collections.abc import Optional
from typing import Optional
from file_storage import FileStorage
from mfp import MyFitnessPalClient
import analytics
import datetime as dt
import utils
import traceback

api_bp = Blueprint("api_bp", __name__)

MFP_SOURCE_NAME = "mfp"
GFIT_SOURCE_NAME = "gfit"


def get_filtered_daily_entries(date_from: Optional[str], date_to: Optional[str]) -> list[DailyWeightEntry]:
    """
    Raises:
        utils.InvalidDateError: If the selected date filters are invalid dates
        utils.DateRangeError: If the selected date filters represent an invalid range
    """
    (parsed_date_from, parsed_date_to) = utils.parse_date_filters(date_from, date_to)

    data_storage = FileStorage()
    filtered_daily_entries = daily_entries = data_storage.get_weight_entries()

    if date_from is not None or date_to is not None:
        filtered_daily_entries = utils.filter_daily_entries(
            daily_entries, parsed_date_from, parsed_date_to
        )

    return filtered_daily_entries


def get_filtered_weekly_entries(daily_entries, goal, weeks_limit):
    """

    Raises:
        utils.InvalidWeeksLimit: if the weeks limit filter parameter is invalid
    """
    weekly_entries: list[WeeklyAggregateEntry] = analytics.get_weekly_aggregates(
        daily_entries, goal
    )

    if weeks_limit:
        if not utils.is_valid_weeks_filter(weeks_limit):
            raise utils.InvalidWeeksLimit

        weeks_limit = int(weeks_limit)
        # Keeping N + 1 weeks because the last week
        # is used as reference point to compare against, as starting point
        weekly_entries = weekly_entries[0 : weeks_limit + 1]

    weekly_entries[-1].update(utils.REFERENCE_WEEK_DATA)

    return weekly_entries


@api_bp.route("/api/daily-entries", methods=["GET"])
def get_daily_entries():
    date_from_param = request.args.get("date_from", None)
    date_to_param = request.args.get("date_to", None)

    try:
        daily_entries = get_filtered_daily_entries(date_from_param, date_to_param)
        response = [
            {
                "date": entry["date"].isoformat(),
                "weight": entry["weight"],
            }
            for entry in daily_entries
        ]
        return jsonify(response)

    except (utils.InvalidDateError, utils.DateRangeError) as e:
        return jsonify({"error_message": str(e)}), 400
    except:
        traceback.print_exc()
        return jsonify({"error_message": "Error while getting weight data"}), 500


@api_bp.route("/api/weekly-aggregates", methods=["GET"])
def get_weekly_aggregates():
    date_from_param = request.args.get("date_from", None)
    date_to_param = request.args.get("date_to", None)

    try:
        daily_entries = get_filtered_daily_entries(date_from_param, date_to_param)
    except (utils.InvalidDateError, utils.DateRangeError) as e:
        return jsonify({"error_message": str(e)}), 400
    except:
        traceback.print_exc()
        return jsonify({"error_message": "Error while getting weight data"}), 500

    try:
        warning_message = None
        goal = request.args.get("goal", utils.DEFAULT_GOAL)
        if not utils.is_valid_goal_selection(goal):
            warning_message = (
                f"Invalid Goal parameter. Setting to default goal: {utils.DEFAULT_GOAL}"
            )
            goal = utils.DEFAULT_GOAL

        weeks_limit_param = request.args.get("weeks_limit", None)

        weekly_entries = get_filtered_weekly_entries(
            daily_entries, goal, weeks_limit_param
        )

        for entry in weekly_entries:
            entry["week_start"] = entry["week_start"].strftime("%Y-%m-%d")

        response = {}
        response["weekly_data"] = weekly_entries
        response["goal"] = goal
        if warning_message:
            response["warning_message"] = warning_message

        return jsonify(response)

    except utils.InvalidWeeksLimit:
        return (
            jsonify({"error_message": "Weeks limit must be positive"}),
            400,
        )
    except:
        traceback.print_exc()
        return jsonify({"error_message": "Error while getting analytics data"}), 500


@api_bp.route("/api/summary", methods=["GET"])
def get_summary():
    date_from_param = request.args.get("date_from", None)
    date_to_param = request.args.get("date_to", None)

    try:
        daily_entries = get_filtered_daily_entries(date_from_param, date_to_param)
    except (utils.InvalidDateError, utils.DateRangeError) as e:
        return jsonify({"error_message": str(e)}), 400
    except:
        traceback.print_exc()
        return jsonify({"error_message": "Error while getting weight data"}), 500

    try:
        weeks_limit_param = request.args.get("weeks_limit", None)

        weekly_entries = get_filtered_weekly_entries(
            daily_entries, utils.DEFAULT_GOAL, weeks_limit_param
        )

        response = {}
        response["summary"] = analytics.get_summary(weekly_entries)
        # TODO - Upcoming feature, to be implemented later
        # response["goal_progress"] = analytics.get_evaluation(response["summary"])

        return jsonify(response)
    except utils.InvalidWeeksLimit:
        return (
            jsonify({"error_message": "Weeks limit must be positive"}),
            400,
        )

    except:
        traceback.print_exc()
        return jsonify({"error_message": "Error while getting analytics data"}), 500


@api_bp.route("/api/latest-entry", methods=["GET"])
def get_latest_entry():
    try:
        data_storage = FileStorage()
        daily_entries = data_storage.get_weight_entries()
        latest_daily_entry = utils.get_latest_daily_entry(daily_entries)

        latest_daily_entry["date"] = latest_daily_entry["date"].isoformat()
        return jsonify(latest_daily_entry)
    except Exception:
        traceback.print_exc()
        return jsonify({"error_message": "Error while getting weight data"}), 500


@api_bp.route("/api/sync-data", methods=["POST"])
def sync_data():
    try:
        data_storage = FileStorage()
    except Exception:
        traceback.print_exc()
        return (
            jsonify({"status": "error", "message": "Error while getting weight data"}),
            500,
        )

    if not data_storage.data_refresh_needed():
        return (
            jsonify(
                {
                    "status": "data_up_to_date",
                    "message": "Your data is already up to date",
                }
            ),
            200,
        )

    request_body = request.get_json()
    data_source = request_body.get("data_source", utils.DEFAULT_DATA_SOURCE)

    if not utils.is_valid_data_source(data_source):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Data source not supported. Choose one of the listed sources",
                }
            ),
            422,
        )

    if data_source == GFIT_SOURCE_NAME:
        oauth_credentials = GoogleFitAuth().load_auth_token()
        if not oauth_credentials:
            # Response that includes redirect to google auth flow
            return (
                jsonify(
                    {
                        "status": "auth_needed",
                        "message": "Google Fit authentication needed",
                        "auth_url": url_for("gfit_auth_bp.google_signin"),
                    }
                ),
                401,
            )

        data_source_client = GoogleFitClient(oauth_credentials)

    elif data_source == MFP_SOURCE_NAME:
        data_source_client = MyFitnessPalClient()

    data_integration = DataIntegrationService(data_storage, data_source_client)

    try:
        new_entries = data_integration.refresh_weight_entries(
            store_raw_copy=True, store_csv_copy=True
        )
    except SourceFetchError:
        traceback.print_exc()
        if data_source == MFP_SOURCE_NAME:
            error_message = "We couldn't connect to MyFitnessPal. Please check if you're logged in and try again."
        elif data_source == GFIT_SOURCE_NAME:
            error_message = (
                "We couldn't get your data from Google Fit. Please try again later."
            )
        else:
            error_message = "We couldn't get your data. Please try again later."

        return jsonify({"status": "error", "message": error_message}), 500
    except SourceNoDataError:
        return (
            jsonify({"status": "no_data_received", "message": "No data received"}),
            204,
        )
    except DataSyncError:
        traceback.print_exc()
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "We're having trouble syncing your data. We're working on it.",
                }
            ),
            500,
        )

    if new_entries:
        return (
            jsonify(
                {
                    "status": "sync_success",
                    "message": "Data updated successfully",
                    "new_entries_count": len(new_entries),
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "status": "data_up_to_date",
                    "message": "Your data is already up to date",
                }
            ),
            204,
        )
