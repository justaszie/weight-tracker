from pathlib import Path
import json
import myfitnesspal
import browser_cookie3
import datetime as dt

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = "data"
RAW_DATA_FILE_NAME = "raw_weight_data.json"
RAW_DATA_FILE_PATH = Path.joinpath(BASE_DIR, DATA_DIR, "raw", "mfp", RAW_DATA_FILE_NAME)

DEFAULT_DATE_FROM = (dt.datetime.now() - dt.timedelta(days=365 * 1)).date()


class MyFitnessPalClient:
    def __init__(self):
        self._source = "myfitnesspal"

    def ready_to_fetch(self):
        return True

    def get_raw_data(self, date_from=None, date_to=None):
        cookiejar = browser_cookie3.chrome()
        client = myfitnesspal.Client(cookiejar=cookiejar)

        date_from = dt.date.fromisoformat(date_from) if date_from else DEFAULT_DATE_FROM

        weight = client.get_measurements("Weight", lower_bound=date_from)

        return weight

    def store_raw_data(self, raw_data):
        Path(RAW_DATA_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(RAW_DATA_FILE_PATH, "w") as file:
            json.dump(
                [{entry[0].isoformat(): entry[1]} for entry in raw_data.items()], file
            )

    def convert_to_daily_entries(self, raw_data):
        return [{"date": entry[0], "weight": entry[1]} for entry in reversed(raw_data.items())]
