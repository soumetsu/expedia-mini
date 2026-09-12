"""Load and validate the supplied Part 1 CSV data."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "expedia-lite-data"
HOTEL_COLUMNS = (
    "hotel_id",
    "hotel_name",
    "city",
    "state",
    "nightly_rate_usd",
)
TRIP_COLUMNS = ("trip_id", "hotel_id", "trip_name", "check_in", "check_out")


class CatalogDataError(RuntimeError):
    """Raised when the supplied travel data is missing or invalid."""


@dataclass(frozen=True, slots=True)
class HotelRecord:
    """One validated row from hotels.csv."""

    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: Decimal


@dataclass(frozen=True, slots=True)
class TripRecord:
    """One validated row from trips.csv."""

    trip_id: str
    hotel_id: str
    trip_name: str
    check_in: date
    check_out: date


@dataclass(frozen=True, slots=True)
class TravelCatalog:
    """Validated hotel and trip records in source-file order."""

    hotels: tuple[HotelRecord, ...]
    trips: tuple[TripRecord, ...]


def _read_rows(path: Path, expected_columns: tuple[str, ...]) -> list[dict[str, str]]:
    """Read a UTF-8-with-BOM CSV and enforce its expected header."""

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            actual_columns = tuple(reader.fieldnames or ())
            if actual_columns != expected_columns:
                raise CatalogDataError(
                    f"{path.name} columns {actual_columns!r} do not match "
                    f"{expected_columns!r}."
                )
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise CatalogDataError(f"Unable to read {path.name}.") from exc

    if not rows:
        raise CatalogDataError(f"{path.name} contains no records.")
    return rows


def _required_text(row: dict[str, str], field: str, source: str) -> str:
    value = (row.get(field) or "").strip()
    if not value:
        raise CatalogDataError(f"{source} contains a blank {field} value.")
    return value


def _load_hotels(path: Path) -> tuple[HotelRecord, ...]:
    rows = _read_rows(path, HOTEL_COLUMNS)
    hotels: list[HotelRecord] = []

    for row in rows:
        hotel_id = _required_text(row, "hotel_id", path.name)
        raw_rate = _required_text(row, "nightly_rate_usd", path.name)
        try:
            nightly_rate = Decimal(raw_rate)
        except InvalidOperation as exc:
            raise CatalogDataError(
                f"{path.name} has an invalid rate for {hotel_id}."
            ) from exc
        if nightly_rate < 0:
            raise CatalogDataError(f"{path.name} has a negative rate for {hotel_id}.")

        hotels.append(
            HotelRecord(
                hotel_id=hotel_id,
                hotel_name=_required_text(row, "hotel_name", path.name),
                city=_required_text(row, "city", path.name),
                state=_required_text(row, "state", path.name),
                nightly_rate_usd=nightly_rate,
            )
        )

    hotel_ids = [hotel.hotel_id for hotel in hotels]
    if len(hotel_ids) != len(set(hotel_ids)):
        raise CatalogDataError(f"{path.name} contains duplicate hotel_id values.")
    return tuple(hotels)


def _load_trips(path: Path) -> tuple[TripRecord, ...]:
    rows = _read_rows(path, TRIP_COLUMNS)
    trips: list[TripRecord] = []

    for row in rows:
        trip_id = _required_text(row, "trip_id", path.name)
        try:
            check_in = date.fromisoformat(_required_text(row, "check_in", path.name))
            check_out = date.fromisoformat(_required_text(row, "check_out", path.name))
        except ValueError as exc:
            raise CatalogDataError(
                f"{path.name} has an invalid date for {trip_id}."
            ) from exc
        if check_out <= check_in:
            raise CatalogDataError(
                f"{path.name} has a non-positive stay length for {trip_id}."
            )

        trips.append(
            TripRecord(
                trip_id=trip_id,
                hotel_id=_required_text(row, "hotel_id", path.name),
                trip_name=_required_text(row, "trip_name", path.name),
                check_in=check_in,
                check_out=check_out,
            )
        )

    trip_ids = [trip.trip_id for trip in trips]
    if len(trip_ids) != len(set(trip_ids)):
        raise CatalogDataError(f"{path.name} contains duplicate trip_id values.")
    return tuple(trips)


def load_catalog(data_directory: Path = DATA_DIRECTORY) -> TravelCatalog:
    """Load both CSVs and validate their hotel-to-trip relationship."""

    hotels = _load_hotels(data_directory / "hotels.csv")
    trips = _load_trips(data_directory / "trips.csv")
    hotel_ids = {hotel.hotel_id for hotel in hotels}
    missing_hotel_ids = sorted(
        {trip.hotel_id for trip in trips if trip.hotel_id not in hotel_ids}
    )
    if missing_hotel_ids:
        missing = ", ".join(missing_hotel_ids)
        raise CatalogDataError(f"trips.csv references unknown hotels: {missing}.")

    return TravelCatalog(hotels=hotels, trips=trips)
