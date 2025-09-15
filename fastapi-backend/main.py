
import datetime as dt

import secrets
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from api import router as api_router
from google_fit import router as auth_router
# from google_fit import router as gfit_auth_router


class WeightEntry(BaseModel):
    date: dt.datetime
    weight: float

entries: list[WeightEntry] = []

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_hex(32),
    max_age=60 * 60,
    same_site="lax",
    https_only=False,             # In Dev, we need insecure transport
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=['*'],
    allow_credentials=False,
)

app.include_router(api_router, prefix="/api", tags=["weights"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
# app.include_router(gfit_auth_router, prefix="/auth", tags=["auth"])

# @app.get("/test-date")
# def testing(dt: dt.date):
#     return f"Date is: {dt.isoformat()}"
