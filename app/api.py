from flask import Blueprint, jsonify, request
from file_storage import FileStorage
import datetime as dt
import utils

api_bp = Blueprint("api_bp", __name__)


# TODO - Exception handling
@api_bp.route("/api/daily-entries", methods=["GET"])
def get_daily_entries():
    try:
        (date_from, date_to) = utils.parse_date_filters(
            request.args.get("date_from", None),
            request.args.get("date_to", None),
        )
    except (utils.InvalidDateError, utils.DateRangeError) as e:
        return jsonify({"message": str(e)}), 400

    storage = FileStorage()
    daily_entries = storage.get_weight_entries()

    if date_from is not None or date_to is not None:
        daily_entries = utils.filter_daily_entries(daily_entries, date_from, date_to)

    daily_entries = [
        {
            "date": entry["date"].strftime("%Y-%m-%d"),
            "weight": entry["weight"],
        }
        for entry in daily_entries
    ]

    return jsonify(daily_entries)


@api_bp.route("/api/weekly-aggregates", methods=["GET"])
def get_weekly_aggregates():
    pass


@api_bp.route("/api/summary", methods=["GET"])
def get_summary():
    pass
