import secrets

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .api import router as api_router
from .demo import DemoStorage
from .file_storage import FileStorage
from .google_fit import router as auth_router

app = FastAPI(
    title="Weight Tracker API",
    description="API for fetching weight from various sources and generating analytics data."
)

app.state.data_storage = FileStorage()

app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_hex(32),
    max_age=60 * 60,
    https_only=False,  # In Dev, we need insecure transport via http
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=False,
)

app.include_router(api_router, prefix="/api", tags=["weights"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
