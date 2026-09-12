"""FastAPI routes for Expedia-Mini Part 1."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from .csv_data import CatalogDataError, load_catalog
from .models import HealthResponse, HotelSearchResponse
from .search import search_hotel_stays


router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    """Confirm that the backend is running."""

    return HealthResponse(status="ok")


@router.get(
    "/hotels/search",
    response_model=HotelSearchResponse,
    tags=["hotels"],
)
async def hotel_search(
    name: Annotated[str, Query(min_length=1, description="Full or partial hotel name")],
) -> HotelSearchResponse:
    """Search hotel names and return every joined stay for each match."""

    try:
        return search_hotel_stays(load_catalog(), name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except CatalogDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc
