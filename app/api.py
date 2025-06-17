from flask import Blueprint, jsonify, request
from file_storage import FileStorage
import datetime as dt
import utils

api_bp = Blueprint("api_bp", __name__)


# TODO - Exception handling
@api_bp.route("/daily-entries", methods=["GET"])
def get_daily_entries():
    date_from = request.args.get("date_from", None)
    date_to = request.args.get("date_to", None)

    if date_from:
        date_from = dt.date.fromisoformat(date_from)
    if date_to:
        date_to = dt.date.fromisoformat(date_to)

    storage = FileStorage()
    daily_entries = storage.get_weight_entries()
    daily_entries = utils.filter_daily_entries(daily_entries, date_from, date_to)
    daily_entries = [
        {
            "date": entry["date"].strftime("%Y-%m-%d"),
            "weight": entry["weight"],
        }
        for entry in daily_entries
    ]

    return jsonify(daily_entries)


@api_bp.route("/weekly-aggregates", methods=["GET"])
def get_weekly_aggregates():
    pass


@api_bp.route("/summary", methods=["GET"])
def get_summary():
    pass
