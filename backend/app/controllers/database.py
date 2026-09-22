"""SQLite database controller for schema, seeding, reads, and booking CRUD."""

from __future__ import annotations

import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

from ..models import BookingResponse, HotelStayResponse, UserResponse
from .seed import DATA_DIRECTORY, SeedDataError, load_seed_data


DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "expedia_mini.db"
SEED_VERSION = "1"


class DataAccessError(RuntimeError):
    """Raised when SQLite cannot initialize or serve application data."""


class BookingNotFoundError(LookupError):
    """Raised when a referenced booking, user, or trip does not exist."""


class BookingConflictError(ValueError):
    """Raised when a booking operation conflicts with stored state."""


SCHEMA = """
CREATE TABLE IF NOT EXISTS app_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hotels (
    hotel_id TEXT PRIMARY KEY,
    hotel_name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    nightly_rate_usd NUMERIC NOT NULL CHECK (nightly_rate_usd >= 0)
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id TEXT PRIMARY KEY,
    hotel_id TEXT NOT NULL REFERENCES hotels(hotel_id),
    trip_name TEXT NOT NULL,
    check_in TEXT NOT NULL,
    check_out TEXT NOT NULL,
    CHECK (check_out > check_in)
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    trip_id TEXT NOT NULL REFERENCES trips(trip_id),
    booked_on TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('confirmed', 'cancelled')),
    is_seeded INTEGER NOT NULL DEFAULT 0 CHECK (is_seeded IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_trips_hotel_id ON trips(hotel_id);
CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_trip_id ON bookings(trip_id);
"""


def _connect(database_path: Path) -> sqlite3.Connection:
    try:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
    except (OSError, sqlite3.Error) as exc:
        raise DataAccessError("The application database could not be opened.") from exc


def initialize_database(
    database_path: Path = DATABASE_PATH,
    data_directory: Path = DATA_DIRECTORY,
) -> Path:
    """Create the schema and import validated CSV models exactly once."""

    connection = _connect(database_path)
    try:
        with connection:
            connection.executescript(SCHEMA)
            seed = connection.execute(
                "SELECT value FROM app_metadata WHERE key = 'seed_version'"
            ).fetchone()
            if seed is not None:
                return database_path

            seed_data = load_seed_data(data_directory)
            connection.executemany(
                """
                INSERT INTO hotels (
                    hotel_id, hotel_name, city, state, nightly_rate_usd
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        hotel.hotel_id,
                        hotel.hotel_name,
                        hotel.city,
                        hotel.state,
                        str(hotel.nightly_rate_usd),
                    )
                    for hotel in seed_data.hotels
                ],
            )
            connection.executemany(
                """
                INSERT INTO trips (
                    trip_id, hotel_id, trip_name, check_in, check_out
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        trip.trip_id,
                        trip.hotel_id,
                        trip.trip_name,
                        trip.check_in.isoformat(),
                        trip.check_out.isoformat(),
                    )
                    for trip in seed_data.trips
                ],
            )
            connection.executemany(
                "INSERT INTO users (user_id, display_name) VALUES (?, ?)",
                [(user.user_id, user.display_name) for user in seed_data.users],
            )
            connection.executemany(
                """
                INSERT INTO bookings (
                    booking_id, user_id, trip_id, booked_on, status, is_seeded
                ) VALUES (?, ?, ?, ?, ?, 1)
                """,
                [
                    (
                        booking.booking_id,
                        booking.user_id,
                        booking.trip_id,
                        booking.booked_on.isoformat(),
                        booking.status,
                    )
                    for booking in seed_data.bookings
                ],
            )
            connection.execute(
                "INSERT INTO app_metadata (key, value) VALUES ('seed_version', ?)",
                (SEED_VERSION,),
            )
    except SeedDataError:
        raise
    except sqlite3.Error as exc:
        raise DataAccessError("The application database could not be initialized.") from exc
    finally:
        connection.close()
    return database_path


STAY_SELECT = """
SELECT
    h.hotel_id,
    h.hotel_name,
    h.city,
    h.state,
    h.nightly_rate_usd,
    t.trip_id,
    t.trip_name,
    t.check_in,
    t.check_out
FROM trips AS t
JOIN hotels AS h ON h.hotel_id = t.hotel_id
ORDER BY t.trip_id
"""


BOOKING_SELECT = """
SELECT
    b.booking_id,
    b.user_id,
    u.display_name,
    b.trip_id,
    t.trip_name,
    h.hotel_id,
    h.hotel_name,
    h.city,
    h.state,
    h.nightly_rate_usd,
    t.check_in,
    t.check_out,
    b.booked_on,
    b.status,
    b.is_seeded
FROM bookings AS b
JOIN users AS u ON u.user_id = b.user_id
JOIN trips AS t ON t.trip_id = b.trip_id
JOIN hotels AS h ON h.hotel_id = t.hotel_id
"""


def _stay_from_row(row: sqlite3.Row) -> HotelStayResponse:
    check_in = date.fromisoformat(row["check_in"])
    check_out = date.fromisoformat(row["check_out"])
    nights = (check_out - check_in).days
    nightly_rate = Decimal(str(row["nightly_rate_usd"]))
    return HotelStayResponse(
        hotel_id=row["hotel_id"],
        hotel_name=row["hotel_name"],
        city=row["city"],
        state=row["state"],
        nightly_rate_usd=nightly_rate,
        trip_id=row["trip_id"],
        trip_name=row["trip_name"],
        check_in=check_in,
        check_out=check_out,
        nights=nights,
        estimated_stay_price_usd=nightly_rate * nights,
    )


def _booking_from_row(row: sqlite3.Row) -> BookingResponse:
    stay = _stay_from_row(row)
    return BookingResponse(
        booking_id=row["booking_id"],
        user_id=row["user_id"],
        display_name=row["display_name"],
        trip_id=stay.trip_id,
        trip_name=stay.trip_name,
        hotel_name=stay.hotel_name,
        city=stay.city,
        state=stay.state,
        check_in=stay.check_in,
        check_out=stay.check_out,
        nights=stay.nights,
        nightly_rate_usd=stay.nightly_rate_usd,
        estimated_stay_price_usd=stay.estimated_stay_price_usd,
        booked_on=date.fromisoformat(row["booked_on"]),
        status=row["status"],
        can_delete=not bool(row["is_seeded"]),
    )


def fetch_hotel_stays(
    database_path: Path = DATABASE_PATH,
) -> list[HotelStayResponse]:
    """Return all hotel/trip joins from SQLite for catalog business rules."""

    initialize_database(database_path)
    connection = _connect(database_path)
    try:
        return [_stay_from_row(row) for row in connection.execute(STAY_SELECT)]
    except sqlite3.Error as exc:
        raise DataAccessError("Hotel stays could not be read.") from exc
    finally:
        connection.close()


def _fetch_booking(
    connection: sqlite3.Connection, booking_id: str
) -> BookingResponse | None:
    row = connection.execute(
        f"{BOOKING_SELECT} WHERE b.booking_id = ?", (booking_id,)
    ).fetchone()
    return _booking_from_row(row) if row else None


def list_users(database_path: Path = DATABASE_PATH) -> list[UserResponse]:
    initialize_database(database_path)
    connection = _connect(database_path)
    try:
        rows = connection.execute(
            "SELECT user_id, display_name FROM users ORDER BY user_id"
        ).fetchall()
        return [UserResponse(**dict(row)) for row in rows]
    except sqlite3.Error as exc:
        raise DataAccessError("Demo travelers could not be read.") from exc
    finally:
        connection.close()


def list_bookings(
    user_id: str, database_path: Path = DATABASE_PATH
) -> list[BookingResponse]:
    initialize_database(database_path)
    connection = _connect(database_path)
    try:
        user = connection.execute(
            "SELECT 1 FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if user is None:
            raise BookingNotFoundError("Demo traveler was not found.")
        rows = connection.execute(
            f"{BOOKING_SELECT} WHERE b.user_id = ? "
            "ORDER BY b.booked_on DESC, b.booking_id DESC",
            (user_id,),
        ).fetchall()
        return [_booking_from_row(row) for row in rows]
    except sqlite3.Error as exc:
        raise DataAccessError("Booking history could not be read.") from exc
    finally:
        connection.close()


def create_booking(
    user_id: str,
    trip_id: str,
    database_path: Path = DATABASE_PATH,
    booked_on: date | None = None,
) -> BookingResponse:
    initialize_database(database_path)
    connection = _connect(database_path)
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            user = connection.execute(
                "SELECT 1 FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            trip = connection.execute(
                "SELECT 1 FROM trips WHERE trip_id = ?", (trip_id,)
            ).fetchone()
            if user is None or trip is None:
                raise BookingNotFoundError("Demo traveler or stay was not found.")
            duplicate = connection.execute(
                """
                SELECT 1 FROM bookings
                WHERE user_id = ? AND trip_id = ? AND status = 'confirmed'
                """,
                (user_id, trip_id),
            ).fetchone()
            if duplicate is not None:
                raise BookingConflictError(
                    "This traveler already has a confirmed booking for that stay."
                )

            existing_ids = [
                row["booking_id"]
                for row in connection.execute("SELECT booking_id FROM bookings")
            ]
            numeric_ids = [
                int(value[1:])
                for value in existing_ids
                if value.startswith("B") and value[1:].isdigit()
            ]
            booking_id = f"B{max(numeric_ids, default=0) + 1:03d}"
            connection.execute(
                """
                INSERT INTO bookings (
                    booking_id, user_id, trip_id, booked_on, status, is_seeded
                ) VALUES (?, ?, ?, ?, 'confirmed', 0)
                """,
                (booking_id, user_id, trip_id, (booked_on or date.today()).isoformat()),
            )
            booking = _fetch_booking(connection, booking_id)
            assert booking is not None
            return booking
    except sqlite3.Error as exc:
        raise DataAccessError("The booking could not be created.") from exc
    finally:
        connection.close()


def cancel_booking(
    booking_id: str, database_path: Path = DATABASE_PATH
) -> BookingResponse:
    initialize_database(database_path)
    connection = _connect(database_path)
    try:
        with connection:
            booking = _fetch_booking(connection, booking_id)
            if booking is None:
                raise BookingNotFoundError("Booking was not found.")
            connection.execute(
                "UPDATE bookings SET status = 'cancelled' WHERE booking_id = ?",
                (booking_id,),
            )
            updated = _fetch_booking(connection, booking_id)
            assert updated is not None
            return updated
    except sqlite3.Error as exc:
        raise DataAccessError("The booking could not be cancelled.") from exc
    finally:
        connection.close()


def delete_booking(booking_id: str, database_path: Path = DATABASE_PATH) -> None:
    initialize_database(database_path)
    connection = _connect(database_path)
    try:
        with connection:
            row = connection.execute(
                "SELECT is_seeded FROM bookings WHERE booking_id = ?", (booking_id,)
            ).fetchone()
            if row is None:
                raise BookingNotFoundError("Booking was not found.")
            if row["is_seeded"]:
                raise BookingConflictError(
                    "Seed bookings are retained; create a test booking to delete."
                )
            connection.execute("DELETE FROM bookings WHERE booking_id = ?", (booking_id,))
    except sqlite3.Error as exc:
        raise DataAccessError("The booking could not be deleted.") from exc
    finally:
        connection.close()
