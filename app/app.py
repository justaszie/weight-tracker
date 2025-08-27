from flask import (
    Flask,
    render_template,
    redirect,
    session,
    url_for,
    request,
    flash,
)

import secrets
import traceback
import utils
import google_fit
from data_integration import (
    DataIntegrationService,
    SourceFetchError,
    SourceNoDataError,
    DataSyncError,
)
from file_storage import FileStorage
from google_fit import GoogleFitClient, GoogleFitAuth
from mfp import MyFitnessPalClient
import analytics
import api
from flask_cors import CORS



MFP_SOURCE_NAME = 'mfp'
GFIT_SOURCE_NAME = 'gfit'


app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# Register routes used in google fit auth flow
app.register_blueprint(google_fit.gfit_auth_bp)
app.register_blueprint(api.api_bp)


@app.before_request
def initialize_goal():
    session["goal"] = session.get("goal", utils.DEFAULT_GOAL)


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

    data_source = request.args.get('source', utils.DEFAULT_DATA_SOURCE)
    if not utils.is_valid_data_source(data_source):
        flash("Data source not supported. Choose one of the listed sources", "error")
        return redirect(url_for("tracker"))

    if data_source == GFIT_SOURCE_NAME:
        oauth_credentials = GoogleFitAuth().load_auth_token()
        if not oauth_credentials:
            return redirect(url_for("gfit_auth_bp.google_signin"))

        data_source_client = GoogleFitClient(oauth_credentials)

    if data_source == MFP_SOURCE_NAME:
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
            error_message = "We couldn't get your data from Google Fit. Please try again later."
        else:
            error_message = "We couldn't get your data. Please try again later."

        flash(
            error_message,
            "error",
        )
        return redirect(url_for("tracker"))
    except SourceNoDataError:
        flash("No data received", "info")
        return redirect(url_for("tracker"))
    except DataSyncError:
        traceback.print_exc()
        flash(
            "We're having trouble syncing your data. We're working on it.",
            "error",
        )
        return redirect(url_for("tracker"))

    if new_entries:
        flash("Data updated successfully!", "success")
    else:
        flash("Your data is already up to date", "info")

    return redirect(url_for("tracker"))


@app.route("/tracker", methods=["GET"])
def tracker():
    weekly_data = {}

    goal = request.args.get("goal", session["goal"])
    if not utils.is_valid_goal_selection(goal):
        flash("Invalid goal selection", "error")
        goal = utils.DEFAULT_GOAL

    session["goal"] = goal
    session.modified = True

    filter = request.args.get("filter", "weeks")
    date_from = request.args.get("date_from", None)
    date_to = request.args.get("date_to", None)
    weeks_limit = request.args.get("weeks_limit", utils.DEFAULT_WEEKS_LIMIT)

    filter_values = {
        "filter": filter,
        "date_from": date_from,
        "date_to": date_to,
        "weeks_limit": weeks_limit,
    }

    daily_entries = []
    latest_daily_entry = None

    try:
        data_storage = FileStorage()
        daily_entries = data_storage.get_weight_entries()

    except Exception:
        traceback.print_exc()
        flash(
            "We're having trouble loading your weight data. We're working on it",
            "error",
        )
        return render_template("tracker.html", **filter_values)

    latest_daily_entry = utils.get_latest_daily_entry(daily_entries)

    if filter == "dates":
        try:
            (date_from, date_to) = utils.parse_date_filters(date_from, date_to)
        except (utils.InvalidDateError, utils.DateRangeError) as e:
            flash(str(e), "error")
            return render_template("tracker.html", **filter_values)

        if date_from is not None or date_to is not None:
            daily_entries = utils.filter_daily_entries(daily_entries, date_from, date_to)


    if not daily_entries:
        return render_template("tracker.html", **filter_values)


    try:
        weekly_entries = analytics.get_weekly_aggregates(daily_entries, session["goal"])

        if filter == "weeks":
            if not utils.is_valid_weeks_filter(weeks_limit):
                flash("Weeks filter must be a positive number", "error")
                return render_template("tracker.html", **filter_values)

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
        flash("We're having trouble analyzing your data. We're working on it.", "error")
        return render_template("tracker.html", **filter_values)

    return render_template(
        "tracker.html",
        data=weekly_data,
        latest_daily_entry=latest_daily_entry,
        **filter_values,
    )

@app.route("/")
def home():
    return redirect("/tracker")


app.jinja_env.filters["signed_amt_str"] = utils.to_signed_amt_str
app.jinja_env.filters["message_category_to_class"] = (
    utils.message_category_to_class_name
)

if __name__ == "__main__":
    app.run(debug=True, port=5040)
