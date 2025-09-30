import os
import secrets
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .api import router as api_router
from .db_storage import DatabaseStorage
from .demo import DemoStorage
from .file_storage import FileStorage
from .google_fit import router as auth_router
from .project_types import DataStorage


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


# Instantiating storage as part of app startup
@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    app.state.data_storage = create_data_storage()

    yield

    if app.state.data_storage:
        app.state.data_storage.close_connection()


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

    app.include_router(api_router, prefix="/api", tags=["weights"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"])

    return app


app = create_app()
