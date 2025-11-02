import logging
from collections.abc import Callable, Sequence
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from .file_storage import FileStorage
from .google_fit import NoCredentialsError
from .project_types import (
    DataSourceClient,
    DataStorage,
    WeightEntry,
)

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def raises_sync_error[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except (SourceFetchError, SourceNoDataError, DataSyncError):
            raise
        except Exception as e:
            raise DataSyncError from e

    return wrapper


class DataIntegrationService:
    def __init__(
        self, data_storage: DataStorage, data_source: DataSourceClient
    ) -> None:
        self.storage = data_storage
        self.source = data_source

    def refresh_weight_entries(self, store_raw_copy: bool = False) -> list[WeightEntry]:
        """
        Load data from source and insert only new weight entries in the storage
        Return value: list of inserted new weight entries
        """
        raw_data = self.get_raw_data()

        if store_raw_copy:
            self.store_raw_data(raw_data)

        daily_entries: list[WeightEntry] = self.convert_to_daily_entries(raw_data)
        new_entries: list[WeightEntry] = self.filter_new_weight_entries(daily_entries)

        self.store_new_weight_entries(new_entries)

        return new_entries

    # Depending on data source we may need params here
    # E.g. date range limit may be needed if it takes a long time to fetch
    def get_raw_data(self) -> Any:
        try:
            raw_data: Any = self.source.get_raw_data()
        except NoCredentialsError as e:
            raise SourceFetchError from e
        except Exception as e:
            raise SourceFetchError from e

        return raw_data

    def store_raw_data(self, raw_data: Any) -> None:
        try:
            self.source.store_raw_data(raw_data)
        except Exception:
            logger.warning(
                "Failed to store a copy of raw data",
                exc_info=True,
                extra={
                    "data_source": self.source.__class__.__name__,
                },
            )

    @raises_sync_error
    def convert_to_daily_entries(self, raw_data: Any) -> list[WeightEntry]:
        daily_entries = self.source.convert_to_daily_entries(raw_data)
        if not daily_entries:
            raise SourceNoDataError

        return daily_entries

    @raises_sync_error
    def get_existing_weight_entries(self) -> list[WeightEntry]:
        return self.storage.get_weight_entries()

    @raises_sync_error
    def filter_new_weight_entries(
        self, source_entries: Sequence[WeightEntry]
    ) -> list[WeightEntry]:
        existing_dates = {
            entry.entry_date for entry in self.get_existing_weight_entries()
        }
        return [
            entry for entry in source_entries if entry.entry_date not in existing_dates
        ]

    @raises_sync_error
    def store_new_weight_entries(self, new_entries: list[WeightEntry]) -> None:
        for entry in new_entries:
            self.storage.create_weight_entry(entry.entry_date, entry.weight)

        # Only need this step to persist the data if we're using file storage
        if isinstance(self.storage, FileStorage):
            self.storage.save()


class SourceFetchError(Exception):
    pass


class SourceNoDataError(Exception):
    pass


class DataSyncError(Exception):
    pass
