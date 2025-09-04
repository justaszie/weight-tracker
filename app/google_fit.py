import datetime as dt
import json
import os
import traceback
from collections.abc import Hashable
from pathlib import Path
from typing import Any, cast

import pandas as pd
from flask import Blueprint, redirect, request, session
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow  # type: ignore
from googleapiclient.discovery import build  # pyright: ignore
from googleapiclient.errors import HttpError
from werkzeug import Response

from project_types import DailyWeightEntry

### CONFIGS ###
SCOPES = [
    "https://www.googleapis.com/auth/fitness.body.read",
    "https://www.googleapis.com/auth/fitness.activity.read",
]
REDIRECT_URI = "http://localhost:5040/google-auth"

BASE_DIR: Path = Path(__file__).resolve().parent
AUTH_DIR = "auth"

TOKEN_FILE_NAME = "token.json"
TOKEN_FILE_PATH: Path = Path.joinpath(BASE_DIR, AUTH_DIR, TOKEN_FILE_NAME)

CLIENT_SECRETS_FILE_NAME = "credentials.json"
CLIENT_SECRETS_FILE_PATH: Path = Path.joinpath(
    BASE_DIR, AUTH_DIR, CLIENT_SECRETS_FILE_NAME
)

DATA_DIR = "data"
RAW_DATA_FILE_NAME = "raw_weight_data.json"
RAW_DATA_FILE_PATH: Path = Path.joinpath(
    BASE_DIR, DATA_DIR, "raw", "gfit", RAW_DATA_FILE_NAME
)

FRONTEND_REDIRECT_URL = "http://localhost:5173/"

# FOR DEVELOPMENT ONLY: allow google to send authorization to HTTP (insecure)
# endpoint of this app. For testing.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

gfit_auth_bp = Blueprint("gfit_auth_bp", __name__)
###############

### ROUTES USED IN OAUTH FLOW ###


# This route initiates the google auth flow
@gfit_auth_bp.route("/google-signin", methods=["GET"])
def google_signin() -> Response:
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps
    flow: Flow = (
        Flow.from_client_secrets_file(  # pyright: ignore[reportUnknownMemberType]
            CLIENT_SECRETS_FILE_PATH, scopes=SCOPES
        )
    )
    flow.redirect_uri = REDIRECT_URI

    authorization_url, state = (  # pyright: ignore
        flow.authorization_url(  # pyright: ignore[reportUnknownMemberType]
            access_type="offline", include_granted_scopes="true", prompt="consent"
        )
    )

    # Store the state in the session so you can verify the callback request
    session["state"] = state

    authorization_url = cast(str, authorization_url)
    return redirect(authorization_url)


# This is endpoint that Google calls with the authorization.
# From here, we need to continue process of getting the data
@gfit_auth_bp.route("/google-auth")
def handle_google_auth_callback() -> Response:
    state = session["state"]

    flow: Flow = (
        Flow.from_client_secrets_file(  # pyright: ignore[reportUnknownMemberType]
            CLIENT_SECRETS_FILE_PATH, scopes=SCOPES, state=state
        )
    )

    flow.redirect_uri = REDIRECT_URI

    # Use the authorization server's response to fetch the OAuth 2.0 tokens
    authorization_response: str = request.url
    flow.fetch_token(  # pyright: ignore[reportUnknownMemberType]
        authorization_response=authorization_response
    )

    creds: Credentials = flow.credentials  # pyright: ignore
    # Save access token for future API usage without auth flow
    GoogleFitAuth().save_auth_token_to_file(creds)  # pyright: ignore

    initiator_query_str = "initiator=data_source_auth_success&source=gfit"

    return redirect(FRONTEND_REDIRECT_URL + "?" + initiator_query_str)


#################################


class GoogleFitAuth:
    def load_auth_token(self) -> Credentials | None:
        # Get credentials for API access
        creds: Credentials | None = None

        # The file token.json stores the user's access and refresh tokens
        # It is created automatically when the authorization flow
        # completes for the first time
        if not os.path.exists(TOKEN_FILE_PATH):
            return None

        try:
            with open(TOKEN_FILE_PATH) as token_file:
                creds = cast(
                    Credentials,
                    Credentials.from_authorized_user_info(  # type: ignore
                        json.load(token_file)
                    ),
                )
        except Exception:
            return None

        if creds.valid:  # pyright: ignore[reportUnknownMemberType]
            return creds
        elif (
            creds
            and creds.expired  # pyright: ignore[reportUnknownMemberType]
            and creds.refresh_token  # pyright: ignore[reportUnknownMemberType]
        ):
            # If token has expired but we have a refresh token, refresh the access token
            try:
                creds.refresh(Request())  # type: ignore
                # Save the credentials for future runs
                self.save_auth_token_to_file(creds)
                return creds
            except Exception:
                traceback.print_exc()

        return None

    def save_auth_token_to_file(self, creds: Credentials) -> None:
        Path(TOKEN_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE_PATH, "w") as token:
            token.write(cast(str, creds.to_json()))  # type: ignore


class GoogleFitClient:
    def __init__(self, creds: Credentials | None = None) -> None:
        self.creds = creds
        self._source = "google_fit"

    def get_raw_data(
        self, date_from: str | None = None, date_to: str | None = None
    ) -> Any:
        if not self.creds:
            print("Cannot get data from Google Fit API without valid credentials")
            raise NoCredentialsError

        try:
            fitness_service = build("fitness", "v1", credentials=self.creds)
        except Exception:
            traceback.print_exc()
            raise

        # Get all available data
        date_from_ns_timestamp = 0
        tomorrow: dt.datetime = dt.datetime.now() + dt.timedelta(days=1)
        date_to_ns_timestamp = int(tomorrow.timestamp() * 1e9)

        DATA_SOURCE = "derived:com.google.weight:com.google.android.gms:merge_weight"
        DATA_SET: str = f"{date_from_ns_timestamp}-{date_to_ns_timestamp}"

        # Using google api library to build the HTTP request object
        # to call Fit API with relevant parameters
        request = (  # pyright: ignore
            fitness_service.users()  # pyright: ignore
            .dataSources()
            .datasets()
            .get(userId="me", dataSourceId=DATA_SOURCE, datasetId=DATA_SET)
        )

        dataset = None
        try:
            dataset = request.execute()  # pyright: ignore
        except HttpError as e:
            print(
                f"Error response status code : \
                    {e.resp.status}, reason : {e.error_details}"
            )
            traceback.print_exc()
            raise
        except Exception:
            traceback.print_exc()
            raise
        finally:
            fitness_service.close()

        return dataset if not self._is_empty_dataset(dataset) else []  # pyright: ignore

    def store_raw_data(self, raw_data: Any) -> None:
        Path(RAW_DATA_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(RAW_DATA_FILE_PATH, "w") as file:
            json.dump(raw_data, file)

    def convert_to_daily_entries(self, raw_data: Any) -> list[DailyWeightEntry]:
        def nanos_ts_to_datetime(nanos: int) -> dt.datetime:
            return dt.datetime.fromtimestamp(int(nanos) / 1e9)

        # Extracting weight value from nested field 'fpVal' inside 'value'
        def extract_weight_value(raw_data: list[dict[str, Any]]) -> float:
            return round(raw_data[-1]["fpVal"], 2)

        df: pd.DataFrame = pd.json_normalize(raw_data, "point")  # pyright: ignore

        # Transform timestamp in nanoseconds to the date when weight was captured
        df["date"] = (
            df["endTimeNanos"].apply(nanos_ts_to_datetime).dt.date  # pyright: ignore
        )

        # For multiple weight entries on the same day, keep just the last entry
        df = df.sort_values(by="endTimeNanos").drop_duplicates(  # pyright: ignore
            subset="date", keep="last"
        )

        df["weight"] = df["value"].apply(extract_weight_value)  # pyright: ignore

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

        records: list[dict[Hashable, Any]] = df.to_dict(  # pyright: ignore
            orient="records"
        )
        return [
            {
                "date": record["date"],
                "weight": float(record["weight"]),
            }
            for record in records
        ]

    def _is_empty_dataset(self, dataset: Any) -> bool:
        return not ("point" in dataset and len(dataset["point"]) > 0)


class NoCredentialsError(Exception):
    pass
