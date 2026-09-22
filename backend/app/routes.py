"""Thin FastAPI HTTP adapters for Expedia-Mini controllers."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from .controllers.catalog import recommend_hotel_stays, search_hotel_stays
from .controllers.database import (
    BookingConflictError,
    BookingNotFoundError,
    DataAccessError,
    cancel_booking as cancel_booking_record,
    create_booking as create_booking_record,
    delete_booking as delete_booking_record,
    list_bookings as list_booking_records,
    list_users as list_user_records,
)
from .controllers.seed import SeedDataError
from .models import (
    BookingCreateRequest,
    BookingResponse,
    HealthResponse,
    HotelSearchResponse,
    UserResponse,
)


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
    name: Annotated[
        str,
        Query(min_length=1, description="City, state, or full/partial hotel name"),
    ],
    check_in: date | None = None,
    check_out: date | None = None,
) -> HotelSearchResponse:
    """Search destinations or hotel names and return every matching stay."""

    try:
        return search_hotel_stays(name, check_in, check_out)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc


def _booking_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, BookingNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/users", response_model=list[UserResponse], tags=["bookings"])
async def demo_users() -> list[UserResponse]:
    """List demo travelers available to the simulated booking interface."""

    try:
        return list_user_records()
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc


@router.get("/bookings", response_model=list[BookingResponse], tags=["bookings"])
async def booking_history(
    user_id: Annotated[str, Query(min_length=1)],
) -> list[BookingResponse]:
    """Read booking history for one demo traveler."""

    try:
        return list_booking_records(user_id)
    except BookingNotFoundError as exc:
        raise _booking_http_error(exc) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc


@router.post(
    "/bookings",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["bookings"],
)
async def create_booking(payload: BookingCreateRequest) -> BookingResponse:
    """Create and persist a simulated booking."""

    try:
        return create_booking_record(payload.user_id, payload.trip_id)
    except (BookingNotFoundError, BookingConflictError) as exc:
        raise _booking_http_error(exc) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc


@router.patch(
    "/bookings/{booking_id}/cancel",
    response_model=BookingResponse,
    tags=["bookings"],
)
async def cancel_booking(booking_id: str) -> BookingResponse:
    """Cancel a booking while retaining it in history."""

    try:
        return cancel_booking_record(booking_id)
    except BookingNotFoundError as exc:
        raise _booking_http_error(exc) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc


@router.delete(
    "/bookings/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["bookings"],
)
async def delete_booking(booking_id: str) -> Response:
    """Delete a user-created test booking."""

    try:
        delete_booking_record(booking_id)
    except (BookingNotFoundError, BookingConflictError) as exc:
        raise _booking_http_error(exc) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/hotels/recommended",
    response_model=HotelSearchResponse,
    tags=["hotels"],
)
async def recommended_hotels(
    limit: Annotated[int, Query(ge=1, le=6)] = 3,
) -> HotelSearchResponse:
    """Return deterministic best-value stays from distinct hotels."""

    try:
        return recommend_hotel_stays(limit)
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc
