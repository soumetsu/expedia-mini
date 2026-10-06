"""SQLite database controller for schema, seeding, reads, and booking CRUD."""

from __future__ import annotations

import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

from ..models import (
    AuthUserResponse,
    BookingResponse,
    DemoHotelNightResponse,
    HotelStayResponse,
    PostcodeCenterResponse,
    SavedHotelCreateRequest,
    SavedHotelResponse,
    SavedHotelSearchResponse,
    SearchHistoryResponse,
    UserResponse,
)
from .security import hash_password, verify_password
from .seed import DATA_DIRECTORY, SeedDataError, load_seed_data


DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "expedia_mini.db"
SEED_VERSION = "1"
DEMO_NIGHT_DATES = tuple(date(2026, 10, day) for day in range(10, 15))


class DataAccessError(RuntimeError):
    """Raised when SQLite cannot initialize or serve application data."""


class BookingNotFoundError(LookupError):
    """Raised when a referenced booking, user, or trip does not exist."""


class BookingConflictError(ValueError):
    """Raised when a booking operation conflicts with stored state."""


class AccountConflictError(ValueError):
    """Raised when an account username or email is already in use."""


class AuthenticationError(LookupError):
    """Raised when credentials do not match a stored account."""


class SavedHotelNotFoundError(LookupError):
    """Raised when a requested provider hotel is not saved locally."""


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
    display_name TEXT NOT NULL,
    username TEXT,
    email TEXT,
    password_hash TEXT,
    is_demo INTEGER NOT NULL DEFAULT 1 CHECK (is_demo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    trip_id TEXT NOT NULL REFERENCES trips(trip_id),
    booked_on TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('confirmed', 'cancelled')),
    is_seeded INTEGER NOT NULL DEFAULT 0 CHECK (is_seeded IN (0, 1))
);

-- NearbyHotelResponse mapping: place_id -> hotel_id,
-- formatted_address -> address, and the remaining names map directly.
CREATE TABLE IF NOT EXISTS saved_hotels (
    hotel_id TEXT PRIMARY KEY NOT NULL,
    name TEXT,
    address TEXT,
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180)
);

CREATE TABLE IF NOT EXISTS demo_hotel_nights (
    hotel_id TEXT NOT NULL REFERENCES saved_hotels(hotel_id),
    stay_date TEXT NOT NULL CHECK (
        length(stay_date) = 10
        AND stay_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        AND date(stay_date) = stay_date
    ),
    nightly_rate_cents INTEGER NOT NULL DEFAULT 10000 CHECK (
        typeof(nightly_rate_cents) = 'integer' AND nightly_rate_cents >= 0
    ),
    rooms_available INTEGER NOT NULL DEFAULT 20 CHECK (
        typeof(rooms_available) = 'integer' AND rooms_available >= 0
    ),
    PRIMARY KEY (hotel_id, stay_date)
);

CREATE TABLE IF NOT EXISTS saved_hotel_locations (
    hotel_id TEXT NOT NULL REFERENCES saved_hotels(hotel_id),
    searched_postcode TEXT NOT NULL CHECK (
        length(searched_postcode) = 5
        AND searched_postcode NOT GLOB '*[^0-9]*'
    ),
    center_locality TEXT,
    center_state TEXT,
    center_latitude REAL NOT NULL CHECK (center_latitude BETWEEN -90 AND 90),
    center_longitude REAL NOT NULL CHECK (center_longitude BETWEEN -180 AND 180),
    search_scope TEXT NOT NULL CHECK (
        search_scope IN ('postcode boundary', 'expanded radius')
    ),
    search_radius_miles INTEGER CHECK (search_radius_miles >= 1),
    hotel_city TEXT,
    hotel_state TEXT,
    hotel_postcode TEXT,
    distance_meters INTEGER NOT NULL CHECK (distance_meters >= 0),
    distance_miles REAL NOT NULL CHECK (distance_miles >= 0),
    inside_searched_postcode INTEGER CHECK (
        inside_searched_postcode IS NULL OR inside_searched_postcode IN (0, 1)
    ),
    PRIMARY KEY (hotel_id, searched_postcode),
    CHECK (
        (search_scope = 'postcode boundary' AND search_radius_miles IS NULL)
        OR
        (search_scope = 'expanded radius' AND search_radius_miles IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_trips_hotel_id ON trips(hotel_id);
CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_trip_id ON bookings(trip_id);
CREATE INDEX IF NOT EXISTS idx_saved_hotel_locations_postcode
    ON saved_hotel_locations(searched_postcode, distance_meters, hotel_id);
CREATE TABLE IF NOT EXISTS search_history (
    search_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    check_in TEXT,
    check_out TEXT,
    result_count INTEGER NOT NULL CHECK (result_count >= 0),
    searched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_search_history_user_time
    ON search_history(user_id, searched_at DESC, search_id DESC);
"""


def _demo_password(user_id: str) -> str:
    """Provide deterministic credentials for the six legacy demo travelers."""

    return f"Demo-{user_id}-Pass!"


def _ensure_auth_schema(connection: sqlite3.Connection) -> None:
    """Migrate databases created before account and search-history support."""

    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(users)")
    }
    migrations = {
        "username": "ALTER TABLE users ADD COLUMN username TEXT",
        "email": "ALTER TABLE users ADD COLUMN email TEXT",
        "password_hash": "ALTER TABLE users ADD COLUMN password_hash TEXT",
        "is_demo": "ALTER TABLE users ADD COLUMN is_demo INTEGER NOT NULL DEFAULT 1",
    }
    for column, statement in migrations.items():
        if column not in columns:
            connection.execute(statement)

    legacy_users = connection.execute(
        "SELECT user_id FROM users WHERE username IS NULL OR password_hash IS NULL"
    ).fetchall()
    for row in legacy_users:
        user_id = row["user_id"]
        connection.execute(
            """
            UPDATE users
            SET username = ?, password_hash = ?, is_demo = 1
            WHERE user_id = ?
            """,
            (f"demo_{user_id.lower()}", hash_password(_demo_password(user_id), user_id.encode()), user_id),
        )

    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username COLLATE NOCASE)"
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email
        ON users(email COLLATE NOCASE) WHERE email IS NOT NULL
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS search_history (
            search_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            query TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            result_count INTEGER NOT NULL CHECK (result_count >= 0),
            searched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_search_history_user_time
        ON search_history(user_id, searched_at DESC, search_id DESC)
        """
    )


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
            _ensure_auth_schema(connection)
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
                """
                INSERT INTO users (
                    user_id, display_name, username, password_hash, is_demo
                ) VALUES (?, ?, ?, ?, 1)
                """,
                [
                    (
                        user.user_id,
                        user.display_name,
                        f"demo_{user.user_id.lower()}",
                        hash_password(_demo_password(user.user_id), user.user_id.encode()),
                    )
                    for user in seed_data.users
                ],
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


def _saved_hotel_response(
    connection: sqlite3.Connection,
    row: sqlite3.Row,
) -> SavedHotelResponse:
    night_rows = connection.execute(
        """
        SELECT stay_date, nightly_rate_cents, rooms_available
        FROM demo_hotel_nights
        WHERE hotel_id = ?
        ORDER BY stay_date
        """,
        (row["hotel_id"],),
    ).fetchall()
    return SavedHotelResponse(
        place_id=row["hotel_id"],
        name=row["name"],
        formatted_address=row["address"],
        city=row["hotel_city"],
        state=row["hotel_state"],
        postcode=row["hotel_postcode"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        distance_meters=row["distance_meters"],
        distance_miles=row["distance_miles"],
        inside_searched_postcode=(
            None
            if row["inside_searched_postcode"] is None
            else bool(row["inside_searched_postcode"])
        ),
        demo_nights=[
            DemoHotelNightResponse(
                stay_date=date.fromisoformat(night["stay_date"]),
                nightly_rate_cents=night["nightly_rate_cents"],
                rooms_available=night["rooms_available"],
            )
            for night in night_rows
        ],
    )


SAVED_HOTEL_SELECT = """
SELECT
    sh.hotel_id,
    sh.name,
    sh.address,
    sh.latitude,
    sh.longitude,
    sl.center_locality,
    sl.center_state,
    sl.center_latitude,
    sl.center_longitude,
    sl.search_scope,
    sl.search_radius_miles,
    sl.hotel_city,
    sl.hotel_state,
    sl.hotel_postcode,
    sl.distance_meters,
    sl.distance_miles,
    sl.inside_searched_postcode
FROM saved_hotel_locations AS sl
JOIN saved_hotels AS sh ON sh.hotel_id = sl.hotel_id
WHERE sl.searched_postcode = ?
ORDER BY sl.distance_meters, sh.hotel_id
"""


def _list_saved_hotels(
    connection: sqlite3.Connection,
    postcode: str,
) -> SavedHotelSearchResponse:
    rows = connection.execute(SAVED_HOTEL_SELECT, (postcode,)).fetchall()
    saved_hotel_ids = [
        row["hotel_id"]
        for row in connection.execute(
            "SELECT hotel_id FROM saved_hotels ORDER BY hotel_id"
        )
    ]
    if not rows:
        return SavedHotelSearchResponse(
            query=postcode,
            count=0,
            results=[],
            saved_hotel_ids=saved_hotel_ids,
        )

    first = rows[0]
    center = PostcodeCenterResponse(
        postcode=postcode,
        country_code="us",
        latitude=first["center_latitude"],
        longitude=first["center_longitude"],
        locality=first["center_locality"],
        state=first["center_state"],
    )
    return SavedHotelSearchResponse(
        query=postcode,
        count=len(rows),
        search_scope=first["search_scope"],
        search_radius_miles=first["search_radius_miles"],
        center=center,
        results=[_saved_hotel_response(connection, row) for row in rows],
        saved_hotel_ids=saved_hotel_ids,
    )


def list_saved_hotels(
    postcode: str,
    database_path: Path = DATABASE_PATH,
) -> SavedHotelSearchResponse:
    """Return saved provider hotels associated with an exact searched ZIP."""

    initialize_database(database_path)
    connection = _connect(database_path)
    try:
        return _list_saved_hotels(connection, postcode)
    except sqlite3.Error as exc:
        raise DataAccessError("Saved hotels could not be read.") from exc
    finally:
        connection.close()


def save_api_hotel(
    payload: SavedHotelCreateRequest,
    database_path: Path = DATABASE_PATH,
) -> SavedHotelResponse:
    """Idempotently save one provider hotel, ZIP context, and demo nights."""

    initialize_database(database_path)
    connection = _connect(database_path)
    hotel = payload.hotel
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT OR IGNORE INTO saved_hotels (
                    hotel_id, name, address, latitude, longitude
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    hotel.place_id,
                    hotel.name,
                    hotel.formatted_address,
                    hotel.latitude,
                    hotel.longitude,
                ),
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO saved_hotel_locations (
                    hotel_id, searched_postcode, center_locality, center_state,
                    center_latitude, center_longitude, search_scope,
                    search_radius_miles, hotel_city, hotel_state,
                    hotel_postcode, distance_meters, distance_miles,
                    inside_searched_postcode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hotel.place_id,
                    payload.postcode,
                    payload.center.locality,
                    payload.center.state,
                    payload.center.latitude,
                    payload.center.longitude,
                    payload.search_scope,
                    payload.search_radius_miles,
                    hotel.city,
                    hotel.state,
                    hotel.postcode,
                    hotel.distance_meters,
                    hotel.distance_miles,
                    (
                        None
                        if hotel.inside_searched_postcode is None
                        else int(hotel.inside_searched_postcode)
                    ),
                ),
            )
            connection.executemany(
                """
                INSERT OR IGNORE INTO demo_hotel_nights (hotel_id, stay_date)
                VALUES (?, ?)
                """,
                [
                    (hotel.place_id, stay_date.isoformat())
                    for stay_date in DEMO_NIGHT_DATES
                ],
            )
            saved_search = _list_saved_hotels(connection, payload.postcode)
            saved_hotel = next(
                (
                    result
                    for result in saved_search.results
                    if result.place_id == hotel.place_id
                ),
                None,
            )
            if saved_hotel is None:
                raise DataAccessError("The saved hotel could not be read after saving.")
            return saved_hotel
    except DataAccessError:
        raise
    except sqlite3.Error as exc:
        raise DataAccessError("The hotel could not be saved locally.") from exc
    finally:
        connection.close()


def delete_saved_hotel(
    hotel_id: str,
    database_path: Path = DATABASE_PATH,
) -> None:
    """Delete one saved hotel and all dependent local demo data atomically."""

    initialize_database(database_path)
    connection = _connect(database_path)
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            exists = connection.execute(
                "SELECT 1 FROM saved_hotels WHERE hotel_id = ?", (hotel_id,)
            ).fetchone()
            if exists is None:
                raise SavedHotelNotFoundError("Saved hotel was not found.")
            connection.execute(
                "DELETE FROM demo_hotel_nights WHERE hotel_id = ?", (hotel_id,)
            )
            connection.execute(
                "DELETE FROM saved_hotel_locations WHERE hotel_id = ?", (hotel_id,)
            )
            connection.execute(
                "DELETE FROM saved_hotels WHERE hotel_id = ?", (hotel_id,)
            )
    except SavedHotelNotFoundError:
        raise
    except sqlite3.Error as exc:
        raise DataAccessError("The saved hotel could not be removed.") from exc
    finally:
        connection.close()


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
            "SELECT user_id, display_name, username, email FROM users ORDER BY user_id"
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


def _auth_user_from_row(row: sqlite3.Row) -> AuthUserResponse:
    return AuthUserResponse(
        user_id=row["user_id"],
        username=row["username"],
        display_name=row["display_name"],
        email=row["email"],
    )


def create_user_account(
    username: str,
    password: str,
    email: str | None = None,
    database_path: Path = DATABASE_PATH,
) -> AuthUserResponse:
    """Create a non-seeded account with a unique username and optional email."""

    initialize_database(database_path)
    connection = _connect(database_path)
    normalized_username = username.strip().lower()
    normalized_email = email.strip().lower() if email and email.strip() else None
    try:
        with connection:
            if connection.execute(
                "SELECT 1 FROM users WHERE username = ? COLLATE NOCASE",
                (normalized_username,),
            ).fetchone():
                raise AccountConflictError("That username is already in use.")
            if normalized_email and connection.execute(
                "SELECT 1 FROM users WHERE email = ? COLLATE NOCASE",
                (normalized_email,),
            ).fetchone():
                raise AccountConflictError("That email is already in use.")

            existing_ids = [
                row["user_id"] for row in connection.execute("SELECT user_id FROM users")
            ]
            numeric_ids = [
                int(value[1:])
                for value in existing_ids
                if value.startswith("U") and value[1:].isdigit()
            ]
            user_id = f"U{max(numeric_ids, default=0) + 1:03d}"
            connection.execute(
                """
                INSERT INTO users (
                    user_id, display_name, username, email, password_hash, is_demo
                ) VALUES (?, ?, ?, ?, ?, 0)
                """,
                (
                    user_id,
                    normalized_username,
                    normalized_username,
                    normalized_email,
                    hash_password(password),
                ),
            )
            row = connection.execute(
                "SELECT user_id, display_name, username, email FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            assert row is not None
            return _auth_user_from_row(row)
    except sqlite3.IntegrityError as exc:
        raise AccountConflictError("That username or email is already in use.") from exc
    except sqlite3.Error as exc:
        raise DataAccessError("The account could not be created.") from exc
    finally:
        connection.close()


def authenticate_user(
    username: str, password: str, database_path: Path = DATABASE_PATH
) -> AuthUserResponse:
    """Verify an account password and return its public identity."""

    initialize_database(database_path)
    connection = _connect(database_path)
    try:
        row = connection.execute(
            """
            SELECT user_id, display_name, username, email, password_hash
            FROM users WHERE username = ? COLLATE NOCASE
            """,
            (username.strip().lower(),),
        ).fetchone()
        if row is None or not row["password_hash"] or not verify_password(
            password, row["password_hash"]
        ):
            raise AuthenticationError("Username or password is incorrect.")
        return _auth_user_from_row(row)
    except AuthenticationError:
        raise
    except sqlite3.Error as exc:
        raise DataAccessError("The account could not be read.") from exc
    finally:
        connection.close()


def get_auth_user(
    user_id: str, database_path: Path = DATABASE_PATH
) -> AuthUserResponse:
    """Read one public account identity for session validation."""

    initialize_database(database_path)
    connection = _connect(database_path)
    try:
        row = connection.execute(
            "SELECT user_id, display_name, username, email FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None or not row["username"]:
            raise AuthenticationError("Sign in to continue.")
        return _auth_user_from_row(row)
    except AuthenticationError:
        raise
    except sqlite3.Error as exc:
        raise DataAccessError("The account could not be read.") from exc
    finally:
        connection.close()


def record_search(
    user_id: str,
    query: str,
    check_in: date | None,
    check_out: date | None,
    result_count: int,
    database_path: Path = DATABASE_PATH,
) -> None:
    """Persist one successful search for the authenticated user."""

    initialize_database(database_path)
    connection = _connect(database_path)
    try:
        with connection:
            connection.execute(
                """
                INSERT INTO search_history (
                    user_id, query, check_in, check_out, result_count
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    query,
                    check_in.isoformat() if check_in else None,
                    check_out.isoformat() if check_out else None,
                    result_count,
                ),
            )
    except sqlite3.Error as exc:
        raise DataAccessError("Search history could not be saved.") from exc
    finally:
        connection.close()


def list_search_history(
    user_id: str,
    limit: int = 25,
    database_path: Path = DATABASE_PATH,
) -> list[SearchHistoryResponse]:
    """Return only the authenticated user's most recent searches."""

    initialize_database(database_path)
    connection = _connect(database_path)
    try:
        rows = connection.execute(
            """
            SELECT search_id, query, check_in, check_out, result_count, searched_at
            FROM search_history
            WHERE user_id = ?
            ORDER BY searched_at DESC, search_id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [
            SearchHistoryResponse(
                search_id=row["search_id"],
                query=row["query"],
                check_in=date.fromisoformat(row["check_in"]) if row["check_in"] else None,
                check_out=date.fromisoformat(row["check_out"]) if row["check_out"] else None,
                result_count=row["result_count"],
                searched_at=row["searched_at"],
            )
            for row in rows
        ]
    except sqlite3.Error as exc:
        raise DataAccessError("Search history could not be read.") from exc
    finally:
        connection.close()
