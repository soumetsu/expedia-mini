"""Model contracts shared by controllers and FastAPI routes."""

from .entities import Booking, Hotel, SeedData, Trip, User
from .schemas import (
    BookingCreateRequest,
    BookingResponse,
    HealthResponse,
    HotelSearchResponse,
    HotelStayResponse,
    UserResponse,
)

__all__ = [
    "Booking",
    "BookingCreateRequest",
    "BookingResponse",
    "HealthResponse",
    "Hotel",
    "HotelSearchResponse",
    "HotelStayResponse",
    "SeedData",
    "Trip",
    "User",
    "UserResponse",
]
