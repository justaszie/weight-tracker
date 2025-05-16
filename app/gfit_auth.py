import os
import json
from google.oauth2.credentials import Credentials # Handles the authorized credentials including token
from google.auth.transport.requests import Request # Used in refreshing a token without login flow
from google_auth_oauthlib.flow import Flow # handles the sign in flow and gets token
from flask import Blueprint, session, redirect, request, url_for

gfit_auth_bp = Blueprint('gfit_auth_bp', __name__)

CLIENT_SECRETS_FILE = "auth/credentials.json"
SCOPES = [
    'https://www.googleapis.com/auth/fitness.body.read',
    'https://www.googleapis.com/auth/fitness.activity.read',
]
REDIRECT_URI = "http://localhost:5040/google-auth"
TOKEN_FILE_PATH = 'auth/token.json'

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # FOR DEVELOPMENT: allow google to send authorization to HTTP (insecure) endpoint of this app. For testing.

# This route initiates the google auth flow
@gfit_auth_bp.route('/google-signin', methods=['GET'])
def google_signin():
     # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )

    # Store the state in the session so you can verify the callback request
    session['state'] = state

    return redirect(authorization_url)

# This is endpoint that Google calls with the authorization.
# From here, we need to continue process of getting the data
@gfit_auth_bp.route('/google-auth')
def handle_google_auth_callback():
    state = session['state']

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state)

    flow.redirect_uri = REDIRECT_URI

    # Use the authorization server's response to fetch the OAuth 2.0 tokens
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    creds = flow.credentials
    # Save access token for future API usage without auth flow
    save_token_to_file(creds)

    return redirect(url_for('sync_data'))

def save_token_to_file(creds, file_path=TOKEN_FILE_PATH):
    with open(file_path, 'w') as token:
        token.write(creds.to_json())

def load_google_credentials(file_path=TOKEN_FILE_PATH):
    # Get credentials for API access
    creds = None

    # The file token.json stores the user's access and refresh tokens
    # It is created automatically when the authorization flow completes for the first time
    if os.path.exists(file_path):
        creds = Credentials.from_authorized_user_info(json.loads(open(file_path).read()))

    if creds:
        if creds.valid:
            return creds
        elif creds and creds.expired and creds.refresh_token:
            # If token has expired but we have a refresh token, refresh the access token
            try:
                creds.refresh(Request())
                # Save the credentials for future runs
                save_token_to_file(creds)
                return creds
            except Exception as e:
                print(e)
                return None

