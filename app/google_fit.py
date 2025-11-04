import datetime as dt
import json
import logging
import os
from pathlib import Path
from typing import Any, cast

import pandas as pd
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow  # type: ignore
from googleapiclient.discovery import build  # pyright: ignore
from googleapiclient.errors import HttpError

from .project_types import WeightEntry

logger = logging.getLogger(__name__)

### CONFIGS ###
SCOPES = [
    "https://www.googleapis.com/auth/fitness.body.read",
    "https://www.googleapis.com/auth/fitness.activity.read",
]
REDIRECT_URI = "http://localhost:8000/auth/google-auth"

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


# FOR DEVELOPMENT ONLY: allow google to send authorization to HTTP (insecure)
# endpoint of this app. For testing.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

router = APIRouter()

###############

### ROUTES USED IN OAUTH FLOW ###


# This route initiates the google auth flow
@router.get("/google-signin", include_in_schema=False)
def google_signin(request: Request) -> RedirectResponse:
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps
    flow: Flow = Flow.from_client_secrets_file(  # pyright: ignore[reportUnknownMemberType]
        CLIENT_SECRETS_FILE_PATH, scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI

    authorization_url, state = (  # pyright: ignore
        flow.authorization_url(  # pyright: ignore[reportUnknownMemberType]
            access_type="offline", include_granted_scopes="true", prompt="consent"
        )
    )

    # Store the state in the session so you can verify the callback request
    request.session["state"] = state

    authorization_url = cast(str, authorization_url)
    logger.info("Redirecting user to Google API consent URL")

    return RedirectResponse(authorization_url)


# This is endpoint that Google calls with the authorization.
# After successfully getting token, we transfer the user back to frontend
@router.get("/google-auth", include_in_schema=False)
def handle_google_auth_callback(request: Request) -> RedirectResponse:
    state = request.session["state"]

    flow: Flow = Flow.from_client_secrets_file(  # pyright: ignore[reportUnknownMemberType]
        CLIENT_SECRETS_FILE_PATH, scopes=SCOPES, state=state
    )

    flow.redirect_uri = REDIRECT_URI

    # Use the authorization server's response to fetch the OAuth 2.0 tokens
    authorization_response = str(request.url)
    flow.fetch_token(  # pyright: ignore[reportUnknownMemberType]
        authorization_response=authorization_response
    )

    creds: Credentials = flow.credentials  # pyright: ignore
    logger.info("Google Fit access token received")
    # Save access token for future API usage without auth flow
    GoogleFitAuth().save_auth_token_to_file(creds)  # pyright: ignore

    initiator_query_str = "initiator=data_source_auth_success&source=gfit"

    frontend_url = os.environ.get("FRONTEND_REDIRECT_URL")
    if not frontend_url:
        error_message = (
            "Auth success but frontend URL config for redirection is missing"
        )
        logger.error(error_message)
        raise HTTPException(status_code=500, detail=error_message)

    redirect_url = f"{frontend_url}?{initiator_query_str}"
    logger.info("Redirecting user back to frontend after gfit auth")

    return RedirectResponse(redirect_url)


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
                creds.refresh(GoogleRequest())  # type: ignore
                # Save the credentials for future runs
                logger.info("Gfit access token refreshed successfully")
                self.save_auth_token_to_file(creds)
                return creds
            except Exception:
                logger.warning(
                    "Failed to refresh expired credentials. Re-auth is required"
                )

        return None

    def save_auth_token_to_file(self, creds: Credentials) -> None:
        TOKEN_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE_PATH.write_text(creds.to_json())  # type: ignore


class GoogleFitClient:
    def __init__(self, creds: Credentials | None = None) -> None:
        self.creds = creds
        self._source = "google_fit"

    def get_raw_data(
        self, date_from: str | None = None, date_to: str | None = None
    ) -> Any:
        if not self.creds:
            logger.error(
                "Cannot get data from Google Fit API without valid credentials"
            )
            raise NoCredentialsError

        try:
            fitness_service = build("fitness", "v1", credentials=self.creds)
        except Exception:
            logger.exception("Error while building Google Fit API service")
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
            logger.info("Fetched raw data from gfit API successfully")
        except HttpError as e:
            logger.exception(
                f"Google Fit API request failed. Dataset Requested: {DATA_SET} \n"
                f"Status: {e.resp.status}, Error: {e.error_details}"
            )
            raise
        except Exception:
            logger.exception(
                f"Google Fit API request failed. Dataset Requested: {DATA_SET} \n"
            )
            raise
        finally:
            fitness_service.close()

        return dataset  # pyright: ignore[reportUnknownVariableType]

    def store_raw_data(self, raw_dataset: Any) -> None:
        RAW_DATA_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        json_data = json.dumps(raw_dataset)
        RAW_DATA_FILE_PATH.write_text(json_data)

    def convert_to_daily_entries(self, raw_dataset: Any) -> list[WeightEntry]:
        def nanos_ts_to_datetime(nanos: int) -> dt.datetime:
            return dt.datetime.fromtimestamp(int(nanos) / 1e9)

        # Extracting weight value from nested field 'fpVal' inside 'value'
        def extract_weight_value(raw_data: list[dict[str, Any]]) -> float:
            return round(float(raw_data[-1]["fpVal"]), 2)

        data = self._extract_datapoints(raw_dataset)
        if not data:
            logger.info("Skipping raw data conversion - raw dataset empty")
            return []

        logger.info(f"Converting {len(data)} raw datapoints to daily entries")

        df: pd.DataFrame = pd.DataFrame.from_records(data)  # pyright: ignore

        # Transform timestamp in nanoseconds to the date when weight was captured
        df["entry_date"] = (
            df["endTimeNanos"].apply(nanos_ts_to_datetime).dt.date  # pyright: ignore
        )

        # For multiple weight entries on the same day, keep just the last entry
        df = df.sort_values(by="endTimeNanos").drop_duplicates(  # pyright: ignore
            subset="entry_date", keep="last"
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
        filtered_df = df[(df["weight"] > 50) & (df["weight"] < 100)]

        records = filtered_df.to_dict(orient="records")  # pyright: ignore
        daily_entries = [WeightEntry.model_validate(record) for record in records]
        logger.info(
            f"Converted {len(data)} datapoints to {len(daily_entries)} daily entries"
        )
        return daily_entries

    def _extract_datapoints(self, raw_dataset: Any) -> list[Any]:
        if "point" not in raw_dataset:
            logger.warning("Google Fit response missing 'point' data")
            return []

        return cast(list[dict[str, Any]], raw_dataset["point"])


class NoCredentialsError(Exception):
    pass
