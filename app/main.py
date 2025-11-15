import logging
import os
import secrets
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from supabase import Client, create_client

from .api import router_v1 as api_router
from .db_storage import DatabaseStorage
from .file_storage import FileStorage
from .google_fit import router as auth_router
from .project_types import DataStorage


def configure_logging() -> None:
    logging.basicConfig(
        format="[{levelname}] - {asctime} - {name}: {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )

    logging.getLogger("googleapiclient").setLevel(logging.ERROR)


def log_dotenv_configuration() -> None:
    logger.info("=== Application Configuration ===")
    logger.info(f"DEMO_MODE: {os.environ.get('DEMO_MODE')}")
    logger.info(f"STORAGE_TYPE: {os.environ.get('STORAGE_TYPE')}")
    logger.info(f"FRONTEND_URL: {os.environ.get('FRONTEND_URL')}")
    logger.info("=================================")


def create_data_storage() -> DataStorage:
    storage_type = os.environ.get("STORAGE_TYPE", "database")
    match storage_type:
        case "database":
            return DatabaseStorage()
        case "file":
            return FileStorage()
        case _:
            raise ValueError(f"Unsupported storage type {storage_type}")


# Instantiating auth service, storage and logging config as part of app startup
@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    data_storage = create_data_storage()
    app.state.data_storage = data_storage
    logger.info(
        f"App started with {data_storage.__class__.__name__} as Storage Backend"
    )

    # TODO: exception handling if config vars are missing or supabase init fails
    url: str | None = os.environ.get("SUPABASE_URL")
    key: str | None = os.environ.get("SUPABASE_KEY")
    if url and key:
        supabase: Client = create_client(url, key)
        app.state.supabase = supabase
        logger.info("Supabase client initialized for auth")
    else:
        logger.error("Missing config to initialize Supabase client")

    yield

    if app.state.data_storage:
        app.state.data_storage.close_connection()
        logger.info(f"{data_storage.__class__.__name__} closed")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Weight Tracker API",
        description="""API for fetching weight from
    various sources and generating analytics data.""",
        lifespan=lifespan,
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=secrets.token_hex(32),
        max_age=60 * 60,
        https_only=False,  # In Dev we need insecure transport via http
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    app.include_router(api_router)
    app.include_router(auth_router, prefix="/auth")

    return app


load_dotenv()

configure_logging()
logger = logging.getLogger(__name__)

log_dotenv_configuration()

app = create_app()
