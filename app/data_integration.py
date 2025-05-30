from googleapiclient.discovery import (
    build,
)  # Build fitness service used to make requests
from googleapiclient.errors import HttpError
import datetime as dt
import json
import pandas as pd
from pathlib import Path
import traceback

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = 'data'
RAW_DATA_FILE_NAME = 'raw_weight_data.json'
RAW_DATA_FILE_PATH = Path.joinpath(BASE_DIR, DATA_DIR, RAW_DATA_FILE_NAME)

def get_raw_gfit_data(creds):
    dataset = None
    # TODO: set back to 'fitness' after testing
    fitness_service = build("fitness", "v1", credentials=creds)

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
    except Exception:
        traceback.print_exc()
    finally:
        return dataset


def store_raw_data(raw_data, file_path=RAW_DATA_FILE_PATH):
    with open(file_path, "w") as file:
        json.dump(raw_data, file)


def get_daily_weight_entries(raw_data):
    df = pd.json_normalize(raw_data, "point")

    # Transform timestamp in nanoseconds to the date when weight was captured
    df["date"] = (
        df["endTimeNanos"]
        .apply(lambda x: dt.datetime.fromtimestamp(int(x) / 1e9))
        .dt.date
    )

    # For multiple weight entries on the same day, keep just the last entry
    df = df.sort_values(by="endTimeNanos").drop_duplicates(subset="date", keep="last")

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
