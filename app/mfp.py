import datetime as dt
import json
from http.cookiejar import CookieJar
from pathlib import Path

import browser_cookie3  # type: ignore
import myfitnesspal  # type: ignore

from project_types import DailyWeightEntry

BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR = "data"
RAW_DATA_FILE_NAME = "raw_weight_data.json"
RAW_DATA_FILE_PATH: Path = Path.joinpath(
    BASE_DIR, DATA_DIR, "raw", "mfp", RAW_DATA_FILE_NAME
)

# Default fetching data back 1 year
DEFAULT_LOOKBACK_YEARS = 1
DEFAULT_DATE_FROM: dt.date = (
    dt.datetime.now() - dt.timedelta(days=365 * DEFAULT_LOOKBACK_YEARS)
).date()


class MyFitnessPalClient:
    def __init__(self) -> None:
        self._source = "myfitnesspal"

    def ready_to_fetch(self) -> bool:
        return True

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

    def store_raw_data(self, raw_data: dict[dt.date, float]) -> None:
        Path(RAW_DATA_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(RAW_DATA_FILE_PATH, "w") as file:
            json.dump(
                [{entry[0].isoformat(): entry[1]} for entry in raw_data.items()], file
            )

    def convert_to_daily_entries(
        self, raw_data: dict[dt.date, float]
    ) -> list[DailyWeightEntry]:
        return [
            {"date": entry[0], "weight": float(entry[1])}
            for entry in reversed(raw_data.items())
        ]
