# type: ignore

import datetime as dt
import json
from pathlib import Path
from uuid import UUID

import pytest
from google.oauth2.credentials import Credentials
from pydantic import TypeAdapter, ValidationError

from app.file_storage import FileStorage
from app.project_types import WeightEntry


TEST_USER_ID = UUID("3760183f-61fa-4ee1-badf-2668fbec152d")
RANDOM_UUID = UUID("5ebcce4b-e597-406e-9d93-8de7072bbc34")


@pytest.fixture
def test_creds_file_data():
    return """
        {
            "token": "abca12",
            "refresh_token": "1//tjj5",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "aaa.apps.googleusercontent.com",
            "client_secret": "add444",
            "scopes": [
                "https://www.googleapis.com/auth/fitness.body.read",
                "https://www.googleapis.com/auth/fitness.activity.read"
            ],
            "universe_domain": "googleapis.com",
            "account": "",
            "expiry": "2025-09-08T07:06:53.565408Z"
        }"""


class TestWeightStorageUsingFile:
    def test_load_weights_from_nonexistent_file(self, mocker):
        mock_file_path = Path(__file__).resolve().parent / "non_existing.json"
        mocker.patch(
            "app.file_storage.FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH",
            new=mock_file_path,
        )
        entries = FileStorage._load_weights_from_file()
        assert entries == []
        if not Path(mock_file_path).is_file():
            print("Expected the storage file to be created but it was not")
            assert False

        if mock_file_path.exists():
            mock_file_path.unlink(missing_ok=True)

    def test_load_weights_from_wrong_format_file(self, mocker, tmp_path):
        test_file_data = ""
        tmp_path = tmp_path / "test_data.json"
        mocker.patch(
            "app.file_storage.FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH", new=tmp_path
        )
        tmp_path.write_text(test_file_data)

        with pytest.raises(ValidationError):
            FileStorage._load_weights_from_file()

    def test_load_weights_from_file(self, mocker, tmp_path):
        # 1. Mock the filepath to the tmp_path value
        tmp_path = tmp_path / "test_data.json"
        mocker.patch(
            "app.file_storage.FileStorage.DAILY_ENTRIES_MAIN_FILE_PATH", new=tmp_path
        )
        # 2. dump test data to the temp test file
        test_file_data = json.dumps(
            [
                {
                    "entry_date": "2025-08-28",
                    "weight": 73.6,
                    "user_id": str(TEST_USER_ID),
                },
                {
                    "entry_date": "2025-08-29",
                    "weight": 73.6,
                    "user_id": str(TEST_USER_ID),
                },
                {
                    "entry_date": "2025-08-30",
                    "weight": 73.5,
                    "user_id": str(TEST_USER_ID),
                },
                {
                    "entry_date": "2025-09-01",
                    "weight": 73.0,
                    "user_id": str(RANDOM_UUID),
                },
            ]
        )
        tmp_path.write_text(test_file_data)

        actual_entries = FileStorage._load_weights_from_file()

        expected_entries = TypeAdapter(list[WeightEntry]).validate_python(
            [
                {
                    "entry_date": dt.date(2025, 8, 28),
                    "weight": 73.6,
                    "user_id": TEST_USER_ID,
                },
                {
                    "entry_date": dt.date(2025, 8, 29),
                    "weight": 73.6,
                    "user_id": TEST_USER_ID,
                },
                {
                    "entry_date": dt.date(2025, 8, 30),
                    "weight": 73.5,
                    "user_id": TEST_USER_ID,
                },
                {
                    "entry_date": dt.date(2025, 9, 1),
                    "weight": 73.0,
                    "user_id": RANDOM_UUID,
                },
            ]
        )
        assert actual_entries == expected_entries


class TestWeightStorageProtocol:
    @pytest.fixture
    def sample_weight_entries(self):
        data = [
            {
                "entry_date": dt.date(2025, 8, 28),
                "weight": 73.6,
                "user_id": TEST_USER_ID,
            },
            {
                "entry_date": dt.date(2025, 8, 29),
                "weight": 73.6,
                "user_id": TEST_USER_ID,
            },
            {
                "entry_date": dt.date(2025, 8, 30),
                "weight": 73.5,
                "user_id": TEST_USER_ID,
            },
            {
                "entry_date": dt.date(2025, 9, 1),
                "weight": 73.0,
                "user_id": TEST_USER_ID,
            },
            {
                "entry_date": dt.date(2025, 8, 28),
                "weight": 73.6,
                "user_id": RANDOM_UUID,
            },
            {
                "entry_date": dt.date(2025, 8, 29),
                "weight": 73.6,
                "user_id": RANDOM_UUID,
            },
            {
                "entry_date": dt.date(2025, 8, 30),
                "weight": 82.5,
                "user_id": RANDOM_UUID,
            },
            {
                "entry_date": dt.date(2025, 8, 31),
                "weight": 92.5,
                "user_id": RANDOM_UUID,
            },
            {"entry_date": dt.date(2025, 9, 1), "weight": 73.0, "user_id": RANDOM_UUID},
        ]
        return TypeAdapter(list[WeightEntry]).validate_python(data)

    @pytest.fixture
    def mock_load_data_function(self, mocker):
        return mocker.patch("app.file_storage.FileStorage._load_weights_from_file")

    @pytest.fixture
    def sample_storage(self, mocker, mock_load_data_function, sample_weight_entries):
        mock_load_data_function.return_value = sample_weight_entries
        return FileStorage()

    @pytest.fixture
    def empty_storage(self, mocker, mock_load_data_function):
        mock_load_data_function.return_value = []
        return FileStorage()

    def test_get_weight_entries(self, sample_storage, sample_weight_entries):
        expected_entries = [
            entry for entry in sample_weight_entries if entry.user_id == TEST_USER_ID
        ]
        assert sample_storage.get_weight_entries(TEST_USER_ID) == expected_entries

    def test_get_existing_weight_entry(self, sample_storage):
        expected = {
            "entry_date": dt.date(2025, 8, 28),
            "weight": 73.6,
            "user_id": TEST_USER_ID,
        }
        expected = WeightEntry.model_validate(expected)
        assert (
            sample_storage.get_weight_entry(
                TEST_USER_ID, entry_date=dt.date(2025, 8, 28)
            )
            == expected
        )

    def test_get_nonexistent_weight_entry(self, sample_storage):
        assert (
            sample_storage.get_weight_entry(
                TEST_USER_ID, entry_date=dt.date(2027, 1, 28)
            )
            == None
        )

    @pytest.mark.parametrize(
        "user_id, date, weight",
        [
            (TEST_USER_ID, dt.date(2025, 9, 2), 76),
            (TEST_USER_ID, dt.date(2025, 9, 3), 74.5),
            (TEST_USER_ID, dt.date(2025, 8, 31), 73.5),
        ],
    )
    def test_create_weight_entry(self, sample_storage, user_id, date, weight) -> None:
        count_before_create = len(sample_storage.get_weight_entries(user_id))
        sample_storage.create_weight_entry(user_id, date, weight)
        assert (
            len(sample_storage.get_weight_entries(user_id)) == count_before_create + 1
        )

        expected_entry_after_creation = WeightEntry.model_validate(
            {
                "entry_date": date,
                "weight": weight,
                "user_id": user_id,
            }
        )
        assert (
            sample_storage.get_weight_entry(user_id=user_id, entry_date=date)
            == expected_entry_after_creation
        )

    def test_create_duplicate_weight_entry(self, sample_storage):
        existing_entries = sample_storage.get_weight_entries(TEST_USER_ID)
        assert len(existing_entries) > 0

        sample_entry = existing_entries[0]
        date = sample_entry.entry_date
        user_id = sample_entry.user_id
        weight = 99.9

        count_before_create = len(sample_storage.get_weight_entries(user_id))
        with pytest.raises(ValueError):
            sample_storage.create_weight_entry(user_id, date, weight)

        assert len(sample_storage.get_weight_entries(user_id)) == count_before_create

    @pytest.mark.parametrize(
        "user_id, date, weight",
        [
            (TEST_USER_ID, dt.date(2025, 8, 28), 72.5),
            (TEST_USER_ID, dt.date(2025, 8, 28), 71),
        ],
    )
    def test_update_valid_weight_entry(self, sample_storage, user_id, date, weight):
        sample_storage.update_weight_entry(TEST_USER_ID, date, weight)
        updated_entry = sample_storage.get_weight_entry(user_id, entry_date=date)

        new_weight = updated_entry.weight
        assert new_weight == weight

    def test_update_nonexistent_weight_entry(self, sample_storage):
        user_id = TEST_USER_ID
        date = dt.date(1990, 1, 1)
        weight = 98.1
        assert sample_storage.get_weight_entry(TEST_USER_ID, date) == None
        with pytest.raises(ValueError):
            sample_storage.update_weight_entry(TEST_USER_ID, date, weight)

    def test_delete_existing_weight_entry(self, sample_storage):
        entries = sample_storage.get_weight_entries(TEST_USER_ID)
        count_before = len(entries)
        assert count_before > 0

        sample_entry = entries[0]
        date = sample_entry.entry_date

        sample_storage.delete_weight_entry(user_id=TEST_USER_ID, entry_date=date)
        assert len(sample_storage.get_weight_entries(TEST_USER_ID)) == count_before - 1
        assert sample_storage.get_weight_entry(TEST_USER_ID, date) == None

    def test_delete_all_weight_entries(self, sample_storage):
        dates = [
            entry.entry_date
            for entry in sample_storage.get_weight_entries(TEST_USER_ID)
        ]
        assert len(sample_storage.get_weight_entries(TEST_USER_ID)) == len(dates)

        for date in dates:
            sample_storage.delete_weight_entry(TEST_USER_ID, date)

        assert len(sample_storage.get_weight_entries(TEST_USER_ID)) == 0

    def test_delete_nonexisting_weight_entry(self, sample_storage):
        date = dt.date(1990, 1, 1)
        count_before = len(sample_storage.get_weight_entries(TEST_USER_ID))
        assert sample_storage.get_weight_entry(TEST_USER_ID, date) == None
        with pytest.raises(ValueError):
            sample_storage.delete_weight_entry(TEST_USER_ID, date)
        assert len(sample_storage.get_weight_entries(TEST_USER_ID)) == count_before

    @pytest.mark.parametrize(
        "dates_in_db, expected_output",
        [
            ([dt.date.today() - dt.timedelta(days=1), dt.date.today()], False),
            (
                [
                    dt.date.today() - dt.timedelta(days=2),
                    dt.date.today() - dt.timedelta(days=1),
                ],
                True,
            ),
            (
                [
                    dt.date.today() - dt.timedelta(days=3),
                    dt.date.today() - dt.timedelta(days=2),
                ],
                True,
            ),
            ([dt.date.today() - dt.timedelta(days=120)], True),
        ],
    )
    def test_data_refresh_needed(self, empty_storage, dates_in_db, expected_output):
        weight = 80.2
        for date in dates_in_db:
            empty_storage.create_weight_entry(
                TEST_USER_ID, entry_date=date, weight=weight
            )
        assert len(empty_storage.get_weight_entries(TEST_USER_ID)) == len(dates_in_db)

        assert empty_storage.data_refresh_needed(TEST_USER_ID) == expected_output

    # Empty Storage Cases
    def test_get_weight_entry_empty_storage(self, empty_storage):
        assert (
            empty_storage.get_weight_entry(
                user_id=TEST_USER_ID, entry_date=dt.date(2027, 1, 28)
            )
            == None
        )

    def test_get_weight_entries_empty_storage(self, empty_storage):
        assert empty_storage.get_weight_entries(TEST_USER_ID) == []

    def test_create_weight_entry_empty_storage(self, empty_storage):
        date = dt.date(2025, 8, 28)
        weight = 74.5
        empty_storage.create_weight_entry(TEST_USER_ID, date, weight)
        assert len(empty_storage.get_weight_entries(TEST_USER_ID)) == 1
        expected_entry = WeightEntry.model_validate(
            {
                "entry_date": date,
                "weight": weight,
                "user_id": TEST_USER_ID,
            }
        )
        assert (
            empty_storage.get_weight_entry(user_id=TEST_USER_ID, entry_date=date)
            == expected_entry
        )

    def test_update_weight_entry_empty_storage(self, empty_storage):
        date = dt.date(1990, 1, 1)
        weight = 98.1
        assert empty_storage.get_weight_entry(TEST_USER_ID, date) == None
        with pytest.raises(ValueError):
            empty_storage.update_weight_entry(TEST_USER_ID, date, weight)

    def test_delete_weight_entry_empty_storage(self, empty_storage):
        date = dt.date(1990, 1, 1)
        assert empty_storage.get_weight_entry(TEST_USER_ID, date) == None
        with pytest.raises(ValueError):
            empty_storage.delete_weight_entry(TEST_USER_ID, date)
        assert len(empty_storage.get_weight_entries(TEST_USER_ID)) == 0

    def test_data_refresh_needed_empty_storage(self, empty_storage):
        assert len(empty_storage.get_weight_entries(TEST_USER_ID)) == 0
        assert empty_storage.data_refresh_needed(TEST_USER_ID) == True

    def test_load_creds_no_file(self, mocker, empty_storage):
        mocker.patch("app.file_storage.FileStorage.CREDS_FILE_DIR", new=Path("any_dir"))
        mocker.patch(
            "app.file_storage.FileStorage.CREDS_FILE_NAME",
            new="nonexisting_file.json",
        )

        file_open_fn = mocker.patch("app.file_storage.open", mocker.mock_open())
        creds = empty_storage.load_google_credentials(TEST_USER_ID)

        assert creds == None

    def test_load_valid_creds(
        self, mocker, empty_storage, test_creds_file_data, tmp_path
    ):
        expected_creds_dict = json.loads(test_creds_file_data)

        mocker.patch("app.file_storage.FileStorage.CREDS_FILE_DIR", new=tmp_path)
        test_filepath = tmp_path / str(TEST_USER_ID) / empty_storage.CREDS_FILE_NAME
        test_filepath.parent.mkdir(parents=True)
        test_filepath.write_text(test_creds_file_data)

        creds = empty_storage.load_google_credentials(TEST_USER_ID)

        assert (
            creds is not None
            and creds.token == expected_creds_dict["token"]
            and creds.refresh_token == expected_creds_dict["refresh_token"]
        )

    def test_store_valid_creds(self, mocker, empty_storage, tmp_path):
        mocker.patch("app.file_storage.FileStorage.CREDS_FILE_DIR", Path(tmp_path))
        mocker.patch(
            "app.file_storage.FileStorage.CREDS_FILE_NAME",
            new="test_creds.json",
        )

        test_token = "abc123"
        test_refresh_token = "dae/"
        test_creds = Credentials(token=test_token, refresh_token=test_refresh_token)

        empty_storage.store_google_credentials(TEST_USER_ID, test_creds)

        test_filepath = tmp_path / str(TEST_USER_ID) / "test_creds.json"
        result = json.loads(test_filepath.read_text())
        assert (
            result["token"] == test_token
            and result["refresh_token"] == test_refresh_token
        )
