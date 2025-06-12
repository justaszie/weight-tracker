import os
import json
from pathlib import Path
import traceback
import datetime as dt
import pandas as pd
from flask import Blueprint, session, redirect, request, url_for
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


### CONFIGS ###
SCOPES = [
    "https://www.googleapis.com/auth/fitness.body.read",
    "https://www.googleapis.com/auth/fitness.activity.read",
]
REDIRECT_URI = "http://localhost:5040/google-auth"

BASE_DIR = Path(__file__).resolve().parent
AUTH_DIR = "auth"

TOKEN_FILE_NAME = "token.json"
TOKEN_FILE_PATH = Path.joinpath(BASE_DIR, AUTH_DIR, TOKEN_FILE_NAME)

CLIENT_SECRETS_FILE_NAME = "credentials.json"
CLIENT_SECRETS_FILE_PATH = Path.joinpath(BASE_DIR, AUTH_DIR, CLIENT_SECRETS_FILE_NAME)

DATA_DIR = "data"
RAW_DATA_FILE_NAME = "raw_weight_data.json"
RAW_DATA_FILE_PATH = Path.joinpath(
    BASE_DIR, DATA_DIR, "raw", "gfit", RAW_DATA_FILE_NAME
)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = (
    "1"  # FOR DEVELOPMENT: allow google to send authorization to HTTP (insecure) endpoint of this app. For testing.
)

gfit_auth_bp = Blueprint("gfit_auth_bp", __name__)
###############

### ROUTES USED IN OAUTH FLOW ###


# This route initiates the google auth flow
@gfit_auth_bp.route("/google-signin", methods=["GET"])
def google_signin():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE_PATH, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )

    # Store the state in the session so you can verify the callback request
    session["state"] = state

    return redirect(authorization_url)


# This is endpoint that Google calls with the authorization.
# From here, we need to continue process of getting the data
@gfit_auth_bp.route("/google-auth")
def handle_google_auth_callback():
    state = session["state"]

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE_PATH, scopes=SCOPES, state=state
    )

    flow.redirect_uri = REDIRECT_URI

    # Use the authorization server's response to fetch the OAuth 2.0 tokens
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    creds = flow.credentials
    # Save access token for future API usage without auth flow
    GoogleFitAuth().save_auth_token_to_file(creds)

    return redirect(url_for("sync_data"))


#################################


class GoogleFitAuth:
    def load_auth_token(self):
        # Get credentials for API access
        creds = None

        # The file token.json stores the user's access and refresh tokens
        # It is created automatically when the authorization flow completes for the first time
        if os.path.exists(TOKEN_FILE_PATH):
            try:
                creds = Credentials.from_authorized_user_info(
                    json.loads(open(TOKEN_FILE_PATH).read())
                )
            except:
                creds = None

        if creds:
            if creds.valid:
                return creds
            elif creds and creds.expired and creds.refresh_token:
                # If token has expired but we have a refresh token, refresh the access token
                try:
                    creds.refresh(Request())
                    # Save the credentials for future runs
                    GoogleFitClient.save_auth_token_to_file(creds)
                    return creds
                except:
                    traceback.print_exc()
                    return None

    def save_auth_token_to_file(cls, creds):
        Path(TOKEN_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE_PATH, "w") as token:
            token.write(creds.to_json())


class GoogleFitClient:
    def __init__(self, creds):
        self.creds = creds
        self._source = "google_fit"

    def ready_to_fetch(self):
        return True if self.creds else False

    def get_raw_data(self):
        dataset = None
        fitness_service = build("fitness", "v1", credentials=self.creds)

        # Get all available data
        date_from_ns_timestamp = 0
        tomorrow = dt.datetime.now() + dt.timedelta(days=1)
        date_to_ns_timestamp = int(tomorrow.timestamp() * 1e9)

        DATA_SOURCE = "derived:com.google.weight:com.google.android.gms:merge_weight"
        DATA_SET = f"{date_from_ns_timestamp}-{date_to_ns_timestamp}"

        # # Using google api library to build the HTTP request object to call Fit API with relevant parameters
        request = (
            fitness_service.users()
            .dataSources()
            .datasets()
            .get(userId="me", dataSourceId=DATA_SOURCE, datasetId=DATA_SET)
        )

        try:
            dataset = request.execute()
            fitness_service.close()
        except HttpError as e:
            print(
                "Error response status code : {}, reason : {}".format(
                    e.resp.status, e.error_details
                )
            )
            fitness_service.close()
            raise
        except Exception:
            raise
        finally:
            return dataset

    def store_raw_data(self, raw_data):
        Path(RAW_DATA_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(RAW_DATA_FILE_PATH, "w") as file:
            json.dump(raw_data, file)

    def convert_to_daily_entries(self, raw_data):
        df = pd.json_normalize(raw_data, "point")

        # Transform timestamp in nanoseconds to the date when weight was captured
        df["date"] = (
            df["endTimeNanos"]
            .apply(lambda x: dt.datetime.fromtimestamp(int(x) / 1e9))
            .dt.date
        )

        # For multiple weight entries on the same day, keep just the last entry
        df = df.sort_values(by="endTimeNanos").drop_duplicates(
            subset="date", keep="last"
        )

        # Extracting weight value from nested field 'fpVal' inside 'value'
        df["weight"] = df["value"].apply(lambda x: round(x[-1]["fpVal"], 2))

        df.drop(
            columns=[
                "startTimeNanos",
                "endTimeNanos",
                "dataTypeName",
                "value",
                "modifiedTimeMillis",
                "originDataSourceId",
            ],
            inplace=True,
        )

        # Remove outliers that were added by mistake
        df = df[(df["weight"] > 50) & (df["weight"] < 100)]

        return df.to_dict(orient="records")
