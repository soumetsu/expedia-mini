"""API response models for Expedia-Mini."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str


class HotelStayResponse(BaseModel):
    """A hotel joined to one offered stay."""

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
    """Stable response envelope for hotel-name search results."""

    query: str
    count: int = Field(ge=0)
    results: list[HotelStayResponse]
