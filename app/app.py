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
        flash("Your data is already up to date", "info")
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
            flash(
                "We couldn't get your data from Google Fit. Try again later.", "error"
            )
            return redirect(url_for("tracker"))

    if not raw_data:
        flash("No data received", "info")
        return redirect(url_for("tracker"))

    try:
        data_integration.store_raw_data(raw_data)
    except:
        traceback.print_exc()

    try:
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
            flash("Your data is already up to date", "info")
        return redirect(url_for("tracker"))

    except Exception:
        traceback.print_exc()
        flash("We're having trouble syncing your data. We're working on it.", "error")
        return redirect(url_for("tracker"))


@app.route("/")
def home():
    return redirect("/tracker")


@app.route("/tracker", methods=["GET"])
def tracker():
    weekly_data = {}

    session["goal"] = request.args.get("goal", session["goal"])
    session.modified = True

    filter = request.args.get("filter", "weeks")
    date_from = request.args.get("date_from", None)
    date_to = request.args.get("date_to", None)
    weeks_limit = request.args.get("weeks_num", DEFAULT_WEEKS_LIMIT)

    if filter == "weeks" and not utils.is_valid_weeks_filter(weeks_limit):
        flash("Weeks filter must be a positive number", "error")

        return render_template(
            "tracker.html",
            filter=filter,
            weeks_num=weeks_limit,
        )

    if filter == "dates":
        date_error = utils.date_filter_error(date_from, date_to)
        if date_error:
            flash(date_error, "error")
            return render_template(
                "tracker.html",
                filter=filter,
                date_from=date_from,
                date_to=date_to,
            )

    daily_entries = []
    latest_entry_date = None

    try:
        data_storage = FileStorage()
        daily_entries = data_storage.get_weight_entries()

    except Exception:
        traceback.print_exc()
        flash("We have trouble loading your weight data. We're working on it", "error")
        return render_template(
            "tracker.html",
            filter=filter,
            weeks_num=weeks_limit,
            date_from=date_from,
            date_to=date_to,
        )

    latest_entry_date = utils.get_latest_entry_date(daily_entries)

    if date_from is not None or date_to is not None:
        daily_entries = utils.filter_daily_entries(daily_entries, date_from, date_to)

    if not daily_entries:
        return render_template(
            "tracker.html",
            filter=filter,
            weeks_num=weeks_limit,
            date_from=date_from,
            date_to=date_to,
        )

    try:
        weekly_entries = analytics.get_weekly_aggregates(daily_entries, session["goal"])

        if filter == "weeks":
            weeks_limit = int(weeks_limit)
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
    except:
        traceback.print_exc()
        flash("We have trouble analyzing your data. We're working on it.", "error")
        return render_template(
            "tracker.html",
            filter=filter,
            weeks_num=weeks_limit,
            date_from=date_from,
            date_to=date_to,
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

if __name__ == "__main__":
    app.run(debug=True, port=5040)
