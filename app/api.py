from flask import Blueprint, jsonify, request
from file_storage import FileStorage
import analytics
import datetime as dt
import utils
import traceback

api_bp = Blueprint("api_bp", __name__)

def get_filtered_daily_entries(date_from, date_to):
    """

    Raises:
        utils.InvalidDateError: If the selected date filters are invalid dates
        utils.DateRangeError: If the selected date filters represent an invalid range
    """
    (parsed_date_from, parsed_date_to) = utils.parse_date_filters(date_from, date_to)

    data_storage = FileStorage()
    daily_entries = data_storage.get_weight_entries()

    if date_from is not None or date_to is not None:
        daily_entries = utils.filter_daily_entries(
            daily_entries, parsed_date_from, parsed_date_to
        )

    return daily_entries


@api_bp.route("/api/daily-entries", methods=["GET"])
def get_daily_entries():
    date_from_param = request.args.get("date_from", None)
    date_to_param = request.args.get("date_to", None)

    try:
        daily_entries = get_filtered_daily_entries(date_from_param, date_to_param)
        response = [
            {
                "date": entry["date"].strftime("%Y-%m-%d"),
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
    try:
        (date_from, date_to) = utils.parse_date_filters(
            request.args.get("date_from", None),
            request.args.get("date_to", None),
        )
    except (utils.InvalidDateError, utils.DateRangeError) as e:
        return jsonify({"error_message": str(e)}), 400

    try:
        data_storage = FileStorage()
        daily_entries = data_storage.get_weight_entries()

        if date_from is not None or date_to is not None:
            daily_entries = utils.filter_daily_entries(
                daily_entries, date_from, date_to
            )

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

        weekly_entries = analytics.get_weekly_aggregates(daily_entries, goal)

        weeks_limit = request.args.get("weeks_limit", None)
        if weeks_limit:
            if not utils.is_valid_weeks_filter(weeks_limit):
                return (
                    jsonify({"error_message": "Weeks limit must be positive"}),
                    400,
                )
            weeks_limit = int(weeks_limit)
            # Keeping N + 1 weeks because the last week
            # is used as reference point to compare against, as starting point
            weekly_entries = weekly_entries[0 : weeks_limit + 1]

        weekly_entries[-1].update(utils.REFERENCE_WEEK_DATA)

        for entry in weekly_entries:
            entry["week_start"] = entry["week_start"].strftime("%Y-%m-%d")

        response = {}
        response["weekly_data"] = weekly_entries
        response["goal"] = goal
        if warning_message:
            response["warning_message"] = warning_message

        return jsonify(response)

    except:
        traceback.print_exc()
        return jsonify({"error_message": "Error while getting analytics data"}), 500


@api_bp.route("/api/summary", methods=["GET"])
def get_summary():
    try:
        (date_from, date_to) = utils.parse_date_filters(
            request.args.get("date_from", None),
            request.args.get("date_to", None),
        )
    except (utils.InvalidDateError, utils.DateRangeError) as e:
        return jsonify({"error_message": str(e)}), 400

    try:
        data_storage = FileStorage()
        daily_entries = data_storage.get_weight_entries()

        if date_from is not None or date_to is not None:
            daily_entries = utils.filter_daily_entries(
                daily_entries, date_from, date_to
            )

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

        weekly_entries = analytics.get_weekly_aggregates(daily_entries, goal)

        weeks_limit = request.args.get("weeks_limit", None)
        if weeks_limit:
            if not utils.is_valid_weeks_filter(weeks_limit):
                return (
                    jsonify({"error_message": "Weeks limit must be positive"}),
                    400,
                )
            weeks_limit = int(weeks_limit)
            # Keeping N + 1 weeks because the last week
            # is used as reference point to compare against, as starting point
            weekly_entries = weekly_entries[0 : weeks_limit + 1]

        weekly_entries[-1].update(utils.REFERENCE_WEEK_DATA)

        response = {}
        response["summary"] = analytics.get_summary(weekly_entries)
        response["goal_progress"] = analytics.get_evaluation(response["summary"])

        if warning_message:
            response["warning_message"] = warning_message

        return jsonify(response)

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
