import datetime as dt

from sqlmodel import (
    Field,
    Session,
    SQLModel,
    create_engine,
    select,
)

from .project_types import WeightEntry


class DBWeightEntry(SQLModel, table=True):
    __tablename__ = "weight_entries"

    date: dt.date = Field(primary_key=True, default=None)
    weight: float = Field(nullable=False, default=None)


class DatabaseStorage:
    def __init__(self):
        db_name = "weight_tracker"
        connection_string = f"postgresql+psycopg2://justas@localhost:5432/{db_name}"
        self._engine = create_engine(connection_string)

        # Set up the database when initializing storage
        self._setup_database()

    def _setup_database(self):
        SQLModel.metadata.create_all(self._engine)

    def get_weight_entries(self):
        with Session(self._engine) as session:
            statement = select(DBWeightEntry)
            results = session.exec(statement)
            return [
                WeightEntry.model_validate(row, from_attributes=True)
                for row in results.all()
            ]

    """
    def get_weight_entries(self) -> list[WeightEntry]: ...

    def get_weight_entry(self, date: dt.date) -> WeightEntry | None: ...

    def create_weight_entry(self, date: dt.date, weight: float | int) -> None: ...

    def delete_weight_entry(self, date: dt.date) -> None: ...

    def update_weight_entry(self, date: dt.date, weight: float | int) -> None: ...

    def export_to_csv(self) -> None: ...

    def data_refresh_needed(self) -> bool: ...
    """
