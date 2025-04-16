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

from google.oauth2.credentials import Credentials # Handls the authorized credentials including token
from google_auth_oauthlib.flow import Flow # handles the sign in flow and gets token
from google.auth.transport.requests import Request # Used in refreshing a token without login flow

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

CLIENT_SECRETS_FILE = "auth/credentials.json"
SCOPES = [
    'https://www.googleapis.com/auth/fitness.body.read',
    'https://www.googleapis.com/auth/fitness.activity.read',
]
REDIRECT_URI = "http://localhost:5040/google-auth"
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # FOR DEVELOPMENT: allow google to send authorization to HTTP (insecure) endpoint of this app. For testing.

# This is endpoint that Google calls with the authorization.
# From here, we need to continue process of getting the data
@app.route('/google-auth')
def google_auth():
    state = session['state']

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = REDIRECT_URI

    # Use the authorization server's response to fetch the OAuth 2.0 tokens
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    creds = flow.credentials

    with open('auth/token.json', 'w') as token:
                token.write(creds.to_json())

    return redirect(url_for('load_data'))


@app.route('/google-signin', methods=['GET'])
def google_signin():
     # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true', prompt='consent')

    # Store the state in the session so you can verify the callback request
    session['state'] = state

    # TBD: when we call redirect from a non-route, does it work
    return redirect(authorization_url)

def load_google_credentials():
    # Get credentials for API access
    creds = None

    # The file token.json stores the user's access and refresh tokens
    # It is created automatically when the authorization flow completes for the first time
    if os.path.exists('auth/token.json'):
        creds = Credentials.from_authorized_user_info(json.loads(open('auth/token.json').read()))

    if creds:
        if creds.valid:
            return creds
        elif creds and creds.expired and creds.refresh_token:
            # If token has expired but we have a refresh token, refresh the access token
            creds.refresh(Request())
             # Save the credentials for future runs
            with open('auth/token.json', 'w') as token:
                token.write(creds.to_json())

            return creds
    else:
        return None

@app.route('/load-data')
def load_data():
    # TODO - json.load doesn't work if the file exists but doesn't contain valid json
    refresh_needed = True
    if os.path.exists('data/daily_entries.json'):
        with open('data/daily_entries.json', 'r') as file:
            daily_entries = json.load(file)
            if daily_entries['daily_entries'] and len(daily_entries['daily_entries']) > 0:
                if not utils.is_outdated(daily_entries):
                    refresh_needed = False

    if refresh_needed:
        # Getting authorization to Google Fit API
        creds = load_google_credentials()
        if not creds:
            return redirect(url_for('google_signin'))

        # Gettign Google Fit data
        raw_data = utils.get_gfit_data(creds)
        today = dt.date.today().strftime('%Y%m%d.json')
        with open('data/raw_weight_data_' + today, 'w') as file:
            json.dump(raw_data, file)

        daily_entries = utils.get_daily_weight_entries(raw_data)
          # Store data in a file to be loaded when we need to display data in frontend
        with open('data/daily_entries.json', 'w') as file:
            json.dump(daily_entries, file)

    return redirect(url_for('home'))

@app.route('/')
def home():
    return redirect('/tracker')

@app.route('/tracker', methods=['GET','POST'])
def tracker():
    DEFAULT_WEEKS = 4


    # TODO - handle case when there's no data - either no file or it's empty or it has no entires
    # Load daily entries
    with open('data/daily_entries.json', 'r') as file:
        daily_entries = json.load(file)



    goal = request.args.get('goal', 'lose')
    filter = request.args.get('filter', 'weeks')

    weeks_limit = None
    if (filter == 'weeks'):
        weeks_limit = int(request.args.get('weeks_num', DEFAULT_WEEKS))

    # Weekly filter logic:  first aggregate, then filter
    # Dates filter logic: first filter daily entries, then aggregate


    # Send daily_entries to utils.get_weekly_aggregates to get the weekly entries
    weekly_data = utils.get_weekly_aggregates(daily_entries, goal, weeks_limit=weeks_limit)
    weekly_data['summary']['evaluation'] = utils.get_evaluation(weekly_data)

    # Collate weekly entries and summary metrics to one object and send to frontend

    # print(request.args)
    # TODO: Validate filter params. If not within available options, use default values.
    for row in weekly_data['entries']:
        row['week_start'] = dt.date.fromisoformat(row['week_start'])
    return render_template('tracker.html', goal=goal, filter=filter, data=weekly_data)


app.jinja_env.filters['signed_amt_str'] = utils.to_signed_amt_str

if __name__ == '__main__':
    app.run(debug=True, port=5040)
