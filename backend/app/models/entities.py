"""Domain entities and relationships represented by the supplied records."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal


BookingStatus = Literal["confirmed", "cancelled"]


@dataclass(frozen=True)
class Hotel:
    """A hotel referenced by one or more offered trips."""

    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: Decimal


@dataclass(frozen=True)
class Trip:
    """A fixed-date hotel stay that references one hotel."""

    trip_id: str
    hotel_id: str
    trip_name: str
    check_in: date
    check_out: date


@dataclass(frozen=True)
class User:
    """A demo traveler that may own multiple bookings."""

    user_id: str
    display_name: str
    username: str | None = None
    email: str | None = None


@dataclass(frozen=True)
class Booking:
    """A simulated reservation that references one user and one trip."""

    booking_id: str
    user_id: str
    trip_id: str
    booked_on: date
    status: BookingStatus


@dataclass(frozen=True)
class SeedData:
    """Validated initial records imported into an empty SQLite database."""

    hotels: tuple[Hotel, ...]
    trips: tuple[Trip, ...]
    users: tuple[User, ...]
    bookings: tuple[Booking, ...]
