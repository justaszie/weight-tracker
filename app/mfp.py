import datetime as dt
import json
from http.cookiejar import CookieJar
from pathlib import Path

import browser_cookie3  # type: ignore
import myfitnesspal  # type: ignore

from .project_types import WeightEntry

BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR = "data"
RAW_DATA_FILE_NAME = "raw_weight_data.json"
RAW_DATA_FILE_PATH: Path = Path.joinpath(
    BASE_DIR, DATA_DIR, "raw", "mfp", RAW_DATA_FILE_NAME
)

# By Default fetching MFP data starting from 1 year ago
DEFAULT_LOOKBACK_YEARS = 1
DEFAULT_DATE_FROM = (
    dt.datetime.now() - dt.timedelta(days=365 * DEFAULT_LOOKBACK_YEARS)
).date()


class MyFitnessPalClient:
    def __init__(self) -> None:
        self._source = "myfitnesspal"

    def get_raw_data(
        self, date_from: str | None = None, date_to: str | None = None
    ) -> dict[dt.date, float]:
        cookiejar: CookieJar = browser_cookie3.chrome()  # pyright: ignore
        client = myfitnesspal.Client(cookiejar=cookiejar)

        parsed_date_from = (
            dt.date.fromisoformat(date_from) if date_from else DEFAULT_DATE_FROM
        )

        weight_entries: dict[dt.date, float] = client.get_measurements(
            "Weight", lower_bound=parsed_date_from
        )

        return weight_entries

    def store_raw_data(self, raw_dataset: dict[dt.date, float]) -> None:
        RAW_DATA_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        json_data = json.dumps(
            {date.isoformat(): weight for date, weight in raw_dataset.items()}
        )
        RAW_DATA_FILE_PATH.write_text(json_data)

    def convert_to_daily_entries(
        self, raw_dataset: dict[dt.date, float]
    ) -> list[WeightEntry]:
        return [
            WeightEntry(entry_date=entry[0], weight=round(float(entry[1]), 2))
            for entry in raw_dataset.items()
        ]
