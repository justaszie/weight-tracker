import traceback


class DataIntegrationService:
    def __init__(self, data_storage, data_source):
        self.storage = data_storage
        self.source = data_source

    def refresh_weight_entries(self, store_raw_copy, store_entries_as_csv):
        """
        Load data from source and insert only new weight entries in the storage
        Return value: list of inserted new weight entries
        """
        raw_data = None

        if not self.source.ready_to_fetch():
            raise SourceNotReadyError

        # 2B: Getting data from source
        try:
            raw_data = self.get_raw_data()
        except:
            raise SourceFetchError

        if not raw_data:
            raise SourceNoDataError

        if store_raw_copy:
            try:
                self.source.store_raw_data(raw_data)
            except:
                traceback.print_exc()

        # 4: CONVERTING RAW DATA TO DAILY ENTRIES
        try:
            daily_entries = self.source.get_daily_weight_entries(raw_data)

            # 5: GETTING EXISTING DAILY ENTRIES
            existing_dates = {
                entry["date"] for entry in self.storage.get_weight_entries()
            }

            # 6: UPDATING EXISTING DAILY EENTRIES WITH NEW ENTRIES
            new_entries = [
                entry for entry in daily_entries if entry["date"] not in existing_dates
            ]

            for entry in new_entries:
                self.storage.create_weight_entry(entry["date"], entry["weight"])
                existing_dates.add(entry["date"])

            # 7. UPDATE EXISTING STORAGE (only needed for file storage)
            self.storage.save(csv_copy=store_entries_as_csv)

        except:
            raise DataSyncError

        return new_entries

    # TODO: depending on data source we may need params here
    # E.g. date range limit may be needed if it takes a long time to fetch
    def get_raw_data(self):
        return self.source.get_raw_data()


class SourceNotReadyError(Exception):
    pass


class SourceFetchError(Exception):
    pass


class SourceNoDataError(Exception):
    pass


class DataSyncError(Exception):
    pass
