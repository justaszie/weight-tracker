import traceback
from functools import wraps
from typing import Callable, TypeVar, ParamSpec, Any
from project_types import DailyWeightEntry
from file_storage import FileStorage
from mfp import MyFitnessPalClient
from google_fit import GoogleFitClient

P = ParamSpec("P")
R = TypeVar("R")

type DataSourceClient = GoogleFitClient | MyFitnessPalClient
type DataStorage = FileStorage

def raises_sync_error(method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except Exception:
            raise DataSyncError

    return wrapper

class DataIntegrationService:
    def __init__(self, data_storage: DataStorage, data_source: DataSourceClient) -> None:
        self.storage = data_storage
        self.source = data_source

    def refresh_weight_entries(self, store_raw_copy: bool = False, store_csv_copy: bool =False) -> list[DailyWeightEntry]:
        """
        Load data from source and insert only new weight entries in the storage
        Return value: list of inserted new weight entries
        """
        raw_data = None

        raw_data = self.get_raw_data()
        if not raw_data:
            raise SourceNoDataError

        if store_raw_copy:
            self.store_raw_data(raw_data) # pyright: ignore

        daily_entries: list[DailyWeightEntry] = self.convert_to_daily_entries(raw_data)
        new_entries: list[DailyWeightEntry] = self.filter_new_weight_entries(daily_entries)

        self.store_new_weight_entries(new_entries)

        if store_csv_copy:
            self.storage.export_to_csv()

        return new_entries

    # TODO: depending on data source we may need params here
    # E.g. date range limit may be needed if it takes a long time to fetch
    def get_raw_data(self) -> Any:
        try:
            return self.source.get_raw_data()
        except:
            raise SourceFetchError

    def store_raw_data(self, raw_data: Any) -> None:
        try:
            self.source.store_raw_data(raw_data)
        except:
            traceback.print_exc()

    @raises_sync_error
    def convert_to_daily_entries(self, raw_data: Any) -> list[DailyWeightEntry]:
        return self.source.convert_to_daily_entries(raw_data)

    @raises_sync_error
    def get_existing_weight_entries(self):
        return self.storage.get_weight_entries()

    @raises_sync_error
    def filter_new_weight_entries(self, source_entries: list[DailyWeightEntry]) -> list[DailyWeightEntry]:
        existing_dates = {entry["date"] for entry in self.get_existing_weight_entries()}
        return [
            entry for entry in source_entries if entry["date"] not in existing_dates
        ]

    @raises_sync_error
    def store_new_weight_entries(self, new_entries: list[DailyWeightEntry]) -> None:
        for entry in new_entries:
            self.storage.create_weight_entry(entry["date"], entry["weight"])

        # Only needed because we're using file storage
        self.storage.save()

class SourceFetchError(Exception):
    pass


class SourceNoDataError(Exception):
    pass


class DataSyncError(Exception):
    pass
