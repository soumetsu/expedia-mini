"""FastAPI application entry point for Expedia-Mini."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .controllers.database import initialize_database
from .routes import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize and seed SQLite before accepting application requests."""

    initialize_database()
    yield


app = FastAPI(
    title="Expedia-Mini API",
    description="Backend API for the Expedia-Mini travel application.",
    version="0.2.0",
    lifespan=lifespan,
)
app.include_router(router)
