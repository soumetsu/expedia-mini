"""Model contracts shared by controllers and FastAPI routes."""

from .entities import Booking, Hotel, SeedData, Trip, User
from .schemas import (
    BookingCreateRequest,
    BookingResponse,
    AuthResponse,
    AuthUserResponse,
    HealthResponse,
    HotelSearchResponse,
    HotelStayResponse,
    LoginRequest,
    RegisterRequest,
    SearchHistoryResponse,
    UserResponse,
)

__all__ = [
    "Booking",
    "BookingCreateRequest",
    "BookingResponse",
    "AuthResponse",
    "AuthUserResponse",
    "HealthResponse",
    "Hotel",
    "HotelSearchResponse",
    "HotelStayResponse",
    "LoginRequest",
    "RegisterRequest",
    "SearchHistoryResponse",
    "SeedData",
    "Trip",
    "User",
    "UserResponse",
]
