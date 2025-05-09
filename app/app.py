from flask import (
    Flask,
    g,
    render_template,
    redirect,
    abort,
    session,
    url_for,
    request,
    flash
)

import secrets
import json
import utils
import datetime as dt
import os
import gfit_auth
import data_integration
import data_storage

# from google.oauth2.credentials import Credentials # Handls the authorized credentials including token
# from google_auth_oauthlib.flow import Flow # handles the sign in flow and gets token
# from google.auth.transport.requests import Request # Used in refreshing a token without login flow

SYNC_DATA_SOURCE = 'gfit'

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Register routes used in google fit auth flow
app.register_blueprint(gfit_auth.gfit_auth_bp)

@app.route('/sync-data')
def sync_data():
    # TODO: add a message that data is up to date
    if not data_storage.data_refresh_needed():
        return redirect(url_for('home'))

    raw_data = None

    if SYNC_DATA_SOURCE == 'gfit':
        # Getting authorization to Google Fit API
        creds = gfit_auth.load_google_credentials()
        if not creds:
            return redirect(url_for('gfit_auth_bp.google_signin'))

    # Getting Google Fit data
    if SYNC_DATA_SOURCE == 'gfit':
        raw_data = data_integration.get_raw_gfit_data(creds)

    # TODO: handle the cases where we couldn't get any raw data
    # or when the raw processing, or storage fail
    if raw_data:
        data_integration.store_raw_data(raw_data)

        daily_entries = data_integration.get_daily_weight_entries(raw_data)

        # Store a copy of daily data as csv for any analytics needs
        data_storage.store_daily_entries_csv(daily_entries)

        # Store data in clean storage
        data_storage.store_daily_entries(daily_entries)

    return redirect(url_for('home'))

@app.route('/')
def home():
    return redirect('/tracker')

@app.route('/tracker', methods=['GET','POST'])
def tracker():
    DEFAULT_WEEKS_LIMIT = 4

    weekly_data = None
    # TODO - handle case when there's no data - either no file or it's empty or it has no entires
    # Load daily entries

    goal = request.args.get('goal', 'lose')
    filter = request.args.get('filter', 'weeks')
    date_from = request.args.get('date_from', None)
    date_to = request.args.get('date_to', None)
    weeks_limit = None

    daily_entries = data_storage.load_daily_data_file()

    if daily_entries:
        # TODO: Validate date_to / date_from inputs.
        if (date_from is not None or date_to is not None):
            daily_entries = utils.filter_daily_entries(daily_entries, date_from, date_to)
            if daily_entries:
                weekly_data = utils.get_weekly_aggregates(daily_entries, goal)
        else:
            weeks_limit = int(request.args.get('weeks_num', DEFAULT_WEEKS_LIMIT))
            weekly_data = utils.get_weekly_aggregates(daily_entries, goal, weeks_limit=weeks_limit)

        if weekly_data:
            weekly_data['summary']['evaluation'] = utils.get_evaluation(weekly_data)

            for row in weekly_data['entries']:
                row['week_start'] = dt.date.fromisoformat(row['week_start'])

            # TODO: Calculate it, don't get it from file
            # weekly_data['summary']['latest_date'] = dt.date.fromisoformat(
            #     daily_data['latest_date']
            # )
            weekly_data['summary']['latest_date'] = utils.get_latest_entry_date(daily_entries)
            # weekly_data['summary']['earliest_date'] = dt.date.fromisoformat(
            #     daily_data['earliest_date']
            # )

    return render_template('tracker.html', data=weekly_data, goal=goal, filter=filter, weeks_num=weeks_limit, date_to=date_to, date_from=date_from)


app.jinja_env.filters['signed_amt_str'] = utils.to_signed_amt_str

if __name__ == '__main__':
    app.run(debug=True, port=5040)
