import logging
import os
import secrets
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .api import router_v1 as api_router
from .db_storage import DatabaseStorage
from .demo import DemoStorage
from .file_storage import FileStorage
from .google_fit import router as auth_router
from .project_types import DataStorage

logging.basicConfig(
    format="[{levelname}] - {asctime} - {name}: {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def create_data_storage() -> DataStorage:
    load_dotenv()
    if os.environ.get("DEMO_MODE", "false") == "true":
        return DemoStorage()
    else:
        storage_type = os.environ.get("STORAGE_TYPE", "database")
        match storage_type:
            case "database":
                return DatabaseStorage()
            case "file":
                return FileStorage()
            case _:
                raise ValueError(f"Unsupported storage type {storage_type}")


# Instantiating storage and logging config as part of app startup
@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    data_storage = create_data_storage()
    app.state.data_storage = data_storage
    logger.info(
        f"App started with {data_storage.__class__.__name__} as Storage Backend"
    )

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
        allow_credentials=False,
    )

    app.include_router(api_router)
    app.include_router(auth_router, prefix="/auth")

    return app


app = create_app()
