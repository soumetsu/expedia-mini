"""FastAPI application entry point for Expedia-Mini."""

from fastapi import FastAPI

from .routes import router


app = FastAPI(
    title="Expedia-Mini API",
    description="Backend API for the Expedia-Mini classroom application.",
    version="0.1.0",
)
app.include_router(router)
