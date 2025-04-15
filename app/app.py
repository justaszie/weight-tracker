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
from datetime import date
import os

from google.oauth2.credentials import Credentials # Handls the authorized credentials including token
from google_auth_oauthlib.flow import Flow # handles the sign in flow and gets token
from google.auth.transport.requests import Request # Used in refreshing a token without login flow
from googleapiclient.discovery import build # Build fitness service used to make requests


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

    return redirect(url_for('get_data'))


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

@app.route('/get-data')
def get_data():
     creds = load_google_credentials()
     if (creds):
        return 'AUTHORIZED BY GOOGLE'
     else:
        if not creds:
            return redirect(url_for('google_signin'))

    # # Build the fitness service with the authenticated credentials
    # fitness_service = build('fitness', 'v1', credentials=credentials)

    # # Calculate time range - default to last 7 days
    # end_time = int(datetime.datetime.now().timestamp() * 1000)  # Current time in milliseconds
    # start_time = end_time - (7 * 24 * 60 * 60 * 1000)  # 7 days ago in milliseconds

    # # Get steps data
    # steps_data = get_steps_data(fitness_service, start_time, end_time)

@app.route('/')
def home():
    return redirect('/tracker')

@app.route('/tracker', methods=['GET','POST'])
def tracker():
    print(request.args)
    # TODO: Validate filter params. If not within available options, use default values.
    goal = request.args.get('goal', 'lose')
    filter = request.args.get('filter', 'weeks')
    with open('data/sample_entries.json') as data_file:
        data = json.load(data_file)
        for row in data['entries']:
            row['week_start'] = date.fromisoformat(row['week_start'])
    return render_template('tracker.html', goal=goal, filter=filter, data=data)

app.jinja_env.filters['signed_amt_str'] = utils.to_signed_amt_str

if __name__ == '__main__':
    app.run(debug=True, port=5040)
