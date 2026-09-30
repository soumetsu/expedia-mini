"""Pydantic request and response contracts for the HTTP boundary."""

from datetime import date
from decimal import Decimal
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


class HealthResponse(BaseModel):
    status: str
    geoapify_api_key_status: Literal["key is configured", "key is not configured"]


class PostcodeCenterResponse(BaseModel):
    """The provider's representative point for a resolved U.S. ZIP code."""

    postcode: str
    country_code: Literal["us"]
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    locality: str | None = None
    state: str | None = None


class NearbyHotelResponse(BaseModel):
    """One live hotel place returned by Geoapify Places."""

    place_id: str
    name: str | None = None
    formatted_address: str | None = None
    city: str | None = None
    state: str | None = None
    postcode: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    distance_meters: int = Field(ge=0)
    distance_miles: float = Field(ge=0)
    inside_searched_postcode: bool | None = None


class NearbyHotelSearchResponse(BaseModel):
    """Live hotels ranked from a resolved ZIP reference point."""

    query: str
    count: int = Field(ge=0)
    search_scope: Literal["postcode boundary", "expanded radius"] = (
        "postcode boundary"
    )
    search_radius_miles: int | None = Field(default=None, ge=1)
    hotel_source: Literal["Geoapify Places API"] = "Geoapify Places API"
    postcode_source: Literal["Geoapify Geocoding API"] = "Geoapify Geocoding API"
    distance_basis: Literal["straight-line distance from ZIP center"] = (
        "straight-line distance from ZIP center"
    )
    center: PostcodeCenterResponse
    results: list[NearbyHotelResponse]


class HotelStayResponse(BaseModel):
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: Decimal
    trip_id: str
    trip_name: str
    check_in: date
    check_out: date
    nights: int = Field(ge=1)
    estimated_stay_price_usd: Decimal = Field(ge=0)


class HotelSearchResponse(BaseModel):
    query: str
    count: int = Field(ge=0)
    results: list[HotelStayResponse]


class UserResponse(BaseModel):
    user_id: str
    display_name: str
    username: str | None = None
    email: str | None = None


class AuthUserResponse(BaseModel):
    user_id: str
    username: str
    display_name: str
    email: str | None = None


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)
    email: str | None = Field(default=None, max_length=254)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9_.-]{1,30}[a-z0-9])?", normalized):
            raise ValueError(
                "Username must use 3-32 letters, numbers, dots, underscores, or hyphens."
            )
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Enter a valid email address or leave email blank.")
        return normalized


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    token: str
    user: AuthUserResponse


class SearchHistoryResponse(BaseModel):
    search_id: int
    query: str
    check_in: date | None = None
    check_out: date | None = None
    result_count: int = Field(ge=0)
    searched_at: str


class BookingCreateRequest(BaseModel):
    user_id: str = Field(min_length=1)
    trip_id: str = Field(min_length=1)


class BookingResponse(BaseModel):
    booking_id: str
    user_id: str
    display_name: str
    trip_id: str
    trip_name: str
    hotel_name: str
    city: str
    state: str
    check_in: date
    check_out: date
    nights: int = Field(ge=1)
    nightly_rate_usd: Decimal = Field(ge=0)
    estimated_stay_price_usd: Decimal = Field(ge=0)
    booked_on: date
    status: Literal["confirmed", "cancelled"]
    can_delete: bool
