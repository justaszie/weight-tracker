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
import gfit_service

# from google.oauth2.credentials import Credentials # Handls the authorized credentials including token
# from google_auth_oauthlib.flow import Flow # handles the sign in flow and gets token
# from google.auth.transport.requests import Request # Used in refreshing a token without login flow

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Register routes used in google fit auth flow
app.register_blueprint(gfit_service.gfit_auth_bp)

@app.route('/load-data')
def load_data():
    if (utils.data_refresh_needed()):
        # Getting authorization to Google Fit API
        creds = gfit_service.load_google_credentials()
        if not creds:
            return redirect(url_for('gfit_auth_bp.google_signin'))

        # Gettign Google Fit data
        raw_data = gfit_service.get_gfit_data(creds)
        # today = dt.date.today().strftime('%Y%m%d.json')

        # TODO: Use data service or something for this raw data storage dump
        with open('data/raw_weight_data.json', 'w') as file:
            json.dump(raw_data, file)

        # TODO: To be extracted to a processing function, and potentially module
        daily_entries = utils.get_daily_weight_entries(raw_data)
          # Store data in a file to be loaded when we need to display data in frontend
        with open('data/daily_data.json', 'w') as file:
            json.dump(daily_entries, file)

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

    daily_data = utils.load_daily_data_file()

    if daily_data:
        daily_entries = daily_data['daily_entries']
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

            weekly_data['summary']['latest_date'] = dt.date.fromisoformat(
                daily_data['latest_date']
            )
            weekly_data['summary']['earliest_date'] = dt.date.fromisoformat(
                daily_data['earliest_date']
            )

    return render_template('tracker.html', data=weekly_data, goal=goal, filter=filter, weeks_num=weeks_limit, date_to=date_to, date_from=date_from)


app.jinja_env.filters['signed_amt_str'] = utils.to_signed_amt_str

if __name__ == '__main__':
    app.run(debug=True, port=5040)
