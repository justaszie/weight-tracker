from flask import (
    Flask,
    g,
    render_template,
    redirect,
    abort,
    session,
    url_for,
    request,
    flash,
)

import secrets
import json
import utils
import datetime as dt
import os
import gfit_auth
import data_integration
from data_storage_file import FileStorage
import analytics
import traceback

SYNC_DATA_SOURCE = "gfit"
DEFAULT_GOAL = "lose"
DEFAULT_WEEKS_LIMIT = 4

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Register routes used in google fit auth flow
app.register_blueprint(gfit_auth.gfit_auth_bp)


@app.before_request
def initialize_goal():
    session["goal"] = session.get("goal", DEFAULT_GOAL)


@app.route("/sync-data")
def sync_data():
    try:
        data_storage = FileStorage()
    except Exception:
        traceback.print_exc()
        return redirect(url_for("tracker"))

    if not data_storage.data_refresh_needed():
        flash("Already up to date.", "info")
        return redirect(url_for("tracker"))

    raw_data = None

    if SYNC_DATA_SOURCE == "gfit":
        try:
            # Getting authorization to Google Fit API
            creds = gfit_auth.load_google_credentials()

            if not creds:
                return redirect(url_for("gfit_auth_bp.google_signin"))

            # Getting Google Fit data
            raw_data = data_integration.get_raw_gfit_data(creds)
        except Exception:
            traceback.print_exc()
            flash("We have trouble getting your weight data. We're working on it", 'error')
            return redirect(url_for("tracker"))

    if raw_data:
        data_integration.store_raw_data(raw_data)

        daily_entries = data_integration.get_daily_weight_entries(raw_data)

        # Updating existing records with delta from the external data source
        existing_dates = {entry["date"] for entry in data_storage.get_weight_entries()}
        new_entries = [
            entry for entry in daily_entries if entry["date"] not in existing_dates
        ]

        for entry in new_entries:
            data_storage.create_weight_entry(entry["date"], entry["weight"])
            existing_dates.add(entry["date"])

        # We're using file based storage so we need to update the file after making changes
        data_storage.save(csv_copy=True)

    if new_entries:
        flash("Data updated successfully!", "success")
    else:
        flash("No new data received", "info")

    return redirect(url_for("tracker"))


@app.route("/")
def home():
    return redirect("/tracker")


@app.route("/tracker", methods=["GET", "POST"])
def tracker():
    weekly_data = {}

    session["goal"] = request.args.get("goal", session["goal"])
    session.modified = True

    filter = request.args.get("filter", "weeks")
    date_from = request.args.get("date_from", None)
    date_to = request.args.get("date_to", None)
    weeks_limit = int(request.args.get("weeks_num", DEFAULT_WEEKS_LIMIT))

    daily_entries = []
    latest_entry_date = None

    try:
        data_storage = FileStorage()
        daily_entries = data_storage.get_weight_entries()

    except Exception:
        traceback.print_exc()
        flash("We have trouble getting your weight data. We're working on it", "error")

    if daily_entries:
        latest_entry_date = utils.get_latest_entry_date(daily_entries)

        # TODO: Validate date_to / date_from inputs.
        if date_from is not None or date_to is not None:
            daily_entries = utils.filter_daily_entries(
                daily_entries, date_from, date_to
            )

        """
        # Simple list of weekly data. Format:
         [
            {
             "week_start": "2025-01-10": datetime.date(2025, 04, 14),
             "avg_weight": 70.2,
             "weight_change": -0.52,
             "weight_change_prc": 0.67,
             "net_calories": -224,
             "result": "positive",
            }
         ]
        """
        if daily_entries:
            weekly_entries = analytics.get_weekly_aggregates(
                daily_entries, session["goal"]
            )

        if weekly_entries:
            if filter == "weeks":
                # Keeping N + 1 weeks because the last week
                # is used as reference point to compare against, as starting point
                weekly_entries = weekly_entries[0 : weeks_limit + 1]

            if weekly_entries:
                # Last week is a reference point, not actual progress data
                weekly_entries[-1].update(utils.REFERENCE_WEEK_DATA)
                weekly_data["entries"] = weekly_entries
                weekly_data["summary"] = analytics.get_summary(weekly_entries)
                weekly_data["goal_progress"] = analytics.get_evaluation(
                    weekly_data["summary"]
                )

    return render_template(
        "tracker.html",
        data=weekly_data,
        latest_entry_date=latest_entry_date,
        filter=filter,
        weeks_num=weeks_limit,
        date_to=date_to,
        date_from=date_from,
    )


app.jinja_env.filters["signed_amt_str"] = utils.to_signed_amt_str
app.jinja_env.filters["message_category_to_class"] = (
    utils.message_category_to_class_name
)
#
if __name__ == "__main__":
    app.run(debug=True, port=5040)
