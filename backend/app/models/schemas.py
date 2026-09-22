"""Pydantic request and response contracts for the HTTP boundary."""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


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
