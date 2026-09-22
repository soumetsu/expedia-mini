"""Read and validate the four CSV files used only for initial SQLite seeding."""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..models import Booking, Hotel, SeedData, Trip, User


DATA_DIRECTORY = Path(__file__).resolve().parents[3] / "expedia-lite-data"


class SeedDataError(RuntimeError):
    """Raised when the supplied initial records cannot be safely imported."""


def _read_rows(data_directory: Path, filename: str) -> list[dict[str, str]]:
    path = data_directory / filename
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            return list(csv.DictReader(source))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise SeedDataError(f"Unable to read {filename}.") from exc


def _require_unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise SeedDataError(f"{label} values must be unique.")


def load_seed_data(data_directory: Path = DATA_DIRECTORY) -> SeedData:
    """Load typed seed models and validate IDs, dates, and foreign references."""

    try:
        hotels = tuple(
            Hotel(
                hotel_id=row["hotel_id"],
                hotel_name=row["hotel_name"],
                city=row["city"],
                state=row["state"],
                nightly_rate_usd=Decimal(row["nightly_rate_usd"]),
            )
            for row in _read_rows(data_directory, "hotels.csv")
        )
        trips = tuple(
            Trip(
                trip_id=row["trip_id"],
                hotel_id=row["hotel_id"],
                trip_name=row["trip_name"],
                check_in=date.fromisoformat(row["check_in"]),
                check_out=date.fromisoformat(row["check_out"]),
            )
            for row in _read_rows(data_directory, "trips.csv")
        )
        users = tuple(
            User(user_id=row["user_id"], display_name=row["display_name"])
            for row in _read_rows(data_directory, "users.csv")
        )
        bookings = tuple(
            Booking(
                booking_id=row["booking_id"],
                user_id=row["user_id"],
                trip_id=row["trip_id"],
                booked_on=date.fromisoformat(row["booked_on"]),
                status=row["status"],
            )
            for row in _read_rows(data_directory, "bookings.csv")
        )
    except (KeyError, ValueError, InvalidOperation) as exc:
        raise SeedDataError("The supplied seed data has an invalid field value.") from exc

    _require_unique([hotel.hotel_id for hotel in hotels], "hotel_id")
    _require_unique([trip.trip_id for trip in trips], "trip_id")
    _require_unique([user.user_id for user in users], "user_id")
    _require_unique([booking.booking_id for booking in bookings], "booking_id")

    hotel_ids = {hotel.hotel_id for hotel in hotels}
    trip_ids = {trip.trip_id for trip in trips}
    user_ids = {user.user_id for user in users}

    if any(hotel.nightly_rate_usd < 0 for hotel in hotels):
        raise SeedDataError("Hotel nightly rates must not be negative.")
    if any(trip.hotel_id not in hotel_ids for trip in trips):
        raise SeedDataError("Every trip must reference an existing hotel.")
    if any(trip.check_out <= trip.check_in for trip in trips):
        raise SeedDataError("Every trip check-out must be after check-in.")
    if any(booking.user_id not in user_ids for booking in bookings):
        raise SeedDataError("Every booking must reference an existing user.")
    if any(booking.trip_id not in trip_ids for booking in bookings):
        raise SeedDataError("Every booking must reference an existing trip.")
    if any(booking.status not in {"confirmed", "cancelled"} for booking in bookings):
        raise SeedDataError("Booking status must be confirmed or cancelled.")

    return SeedData(hotels=hotels, trips=trips, users=users, bookings=bookings)
