
import datetime as dt

from fastapi import FastAPI
from pydantic import BaseModel

from api import router as api_router
# from google_fit import router as gfit_auth_router


class WeightEntry(BaseModel):
    date: dt.datetime
    weight: float

entries: list[WeightEntry] = []

app = FastAPI()

app.include_router(api_router, prefix="/api", tags=["weights"])
# app.include_router(gfit_auth_router, prefix="/auth", tags=["auth"])

# @app.get("/test-date")
# def testing(dt: dt.date):
#     return f"Date is: {dt.isoformat()}"
