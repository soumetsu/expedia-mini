"""Tests for SQLite seeding and booking CRUD behavior."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from app.controllers.database import (
    BookingConflictError,
    HotelQueryValidationError,
    SavedHotelNotFoundError,
    cancel_booking,
    create_booking,
    delete_saved_hotel,
    delete_booking,
    execute_read_only_hotel_query,
    fetch_hotel_stays,
    initialize_database,
    list_bookings,
    list_saved_hotels,
    list_users,
    record_conversation_message,
    record_conversation_trace,
    save_api_hotel,
)
from app.models import (
    NearbyHotelResponse,
    PostcodeCenterResponse,
    SavedHotelCreateRequest,
)


def saved_hotel_payload(
    hotel_id: str = "provider-hotel-1",
    postcode: str = "16802",
) -> SavedHotelCreateRequest:
    return SavedHotelCreateRequest(
        postcode=postcode,
        center=PostcodeCenterResponse(
            postcode=postcode,
            country_code="us",
            latitude=40.7989,
            longitude=-77.8599,
            locality="State College",
            state="Pennsylvania",
        ),
        search_scope="postcode boundary",
        hotel=NearbyHotelResponse(
            place_id=hotel_id,
            name="Campus Hotel",
            formatted_address="1 College Avenue, State College, PA 16802",
            city="State College",
            state="Pennsylvania",
            postcode=postcode,
            latitude=40.8,
            longitude=-77.86,
            distance_meters=123,
            distance_miles=0.08,
            inside_searched_postcode=True,
        ),
    )


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "test.db"
        initialize_database(self.database_path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_seeded_users_and_history_are_available(self) -> None:
        self.assertEqual(len(list_users(self.database_path)), 6)
        history = list_bookings("U001", self.database_path)

        self.assertEqual([booking.booking_id for booking in history], ["B002", "B001"])
        self.assertEqual([booking.status for booking in history], ["cancelled", "confirmed"])
        self.assertTrue(all(not booking.can_delete for booking in history))

    def test_all_four_csv_files_seed_once_with_valid_relationships(self) -> None:
        connection = sqlite3.connect(self.database_path)
        try:
            counts = {
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("hotels", "trips", "users", "bookings")
            }
            broken_trip_refs = connection.execute(
                """
                SELECT COUNT(*) FROM trips AS t
                LEFT JOIN hotels AS h ON h.hotel_id = t.hotel_id
                WHERE h.hotel_id IS NULL
                """
            ).fetchone()[0]
            broken_booking_refs = connection.execute(
                """
                SELECT COUNT(*) FROM bookings AS b
                LEFT JOIN users AS u ON u.user_id = b.user_id
                LEFT JOIN trips AS t ON t.trip_id = b.trip_id
                WHERE u.user_id IS NULL OR t.trip_id IS NULL
                """
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertEqual(
            counts,
            {"hotels": 8, "trips": 12, "users": 6, "bookings": 6},
        )
        self.assertEqual(broken_trip_refs, 0)
        self.assertEqual(broken_booking_refs, 0)
        self.assertEqual(len(fetch_hotel_stays(self.database_path)), 12)

    def test_api_hotel_schema_uses_provider_id_and_fictional_night_defaults(self) -> None:
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        provider_id = "geoapify:Place/AbC-123"
        try:
            connection.execute(
                """
                INSERT INTO saved_hotels (
                    hotel_id, name, address, latitude, longitude
                ) VALUES (?, NULL, NULL, ?, ?)
                """,
                (provider_id, 40.758, -73.9855),
            )
            connection.execute(
                "INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)",
                (provider_id, "2026-10-02"),
            )
            saved_hotel = connection.execute(
                "SELECT * FROM saved_hotels WHERE hotel_id = ?", (provider_id,)
            ).fetchone()
            demo_night = connection.execute(
                "SELECT * FROM demo_hotel_nights WHERE hotel_id = ?",
                (provider_id,),
            ).fetchone()
            saved_columns = {
                row[1]: row
                for row in connection.execute("PRAGMA table_info(saved_hotels)")
            }
            night_columns = {
                row[1]: row
                for row in connection.execute("PRAGMA table_info(demo_hotel_nights)")
            }

            self.assertEqual(saved_hotel[0], provider_id)
            self.assertIsNone(saved_hotel[1])
            self.assertIsNone(saved_hotel[2])
            self.assertEqual(demo_night, (provider_id, "2026-10-02", 10000, 20))
            self.assertEqual(saved_columns["hotel_id"][5], 1)
            self.assertEqual(night_columns["hotel_id"][5], 1)
            self.assertEqual(night_columns["stay_date"][5], 2)

            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    """
                    INSERT INTO saved_hotels (
                        hotel_id, name, address, latitude, longitude
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (provider_id, "Duplicate", "Nowhere", 0, 0),
                )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)",
                    (provider_id, "2026-10-02"),
                )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)",
                    ("missing-provider", "2026-10-03"),
                )
        finally:
            connection.close()

    def test_api_hotel_schema_rejects_invalid_coordinates_dates_and_inventory(self) -> None:
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            invalid_hotels = (("bad-lat", 90.1, 0), ("bad-lon", 0, -180.1))
            for hotel_id, latitude, longitude in invalid_hotels:
                with self.subTest(hotel_id=hotel_id):
                    with self.assertRaises(sqlite3.IntegrityError):
                        connection.execute(
                            """
                            INSERT INTO saved_hotels (
                                hotel_id, latitude, longitude
                            ) VALUES (?, ?, ?)
                            """,
                            (hotel_id, latitude, longitude),
                        )

            connection.execute(
                "INSERT INTO saved_hotels (hotel_id, latitude, longitude) VALUES (?, ?, ?)",
                ("valid-provider", 0, 0),
            )
            invalid_nights = (
                ("2026/10/02", 10000, 20),
                ("2026-02-30", 10000, 20),
                ("2026-10-02", -1, 20),
                ("2026-10-02", 10000, -1),
                ("2026-10-02", 10000.5, 20),
            )
            for stay_date, rate, rooms in invalid_nights:
                with self.subTest(stay_date=stay_date, rate=rate, rooms=rooms):
                    with self.assertRaises(sqlite3.IntegrityError):
                        connection.execute(
                            """
                            INSERT INTO demo_hotel_nights (
                                hotel_id, stay_date, nightly_rate_cents,
                                rooms_available
                            ) VALUES (?, ?, ?, ?)
                            """,
                            ("valid-provider", stay_date, rate, rooms),
                        )
        finally:
            connection.close()

    def test_reinitialization_adds_api_hotel_tables_without_reseeding(self) -> None:
        connection = sqlite3.connect(self.database_path)
        try:
            connection.execute("DROP TABLE saved_hotel_zips")
            connection.execute("DROP TABLE demo_hotel_nights")
            connection.execute("DROP TABLE saved_hotels")
            connection.execute("DELETE FROM bookings WHERE booking_id = 'B006'")
            connection.commit()
        finally:
            connection.close()

        initialize_database(self.database_path)

        connection = sqlite3.connect(self.database_path)
        try:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            booking_count = connection.execute(
                "SELECT COUNT(*) FROM bookings"
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertTrue(
            {"saved_hotels", "saved_hotel_zips", "demo_hotel_nights"}
            <= tables
        )
        self.assertEqual(booking_count, 5)

    def test_save_api_hotel_is_idempotent_and_preserves_demo_night_edits(self) -> None:
        payload = saved_hotel_payload()
        saved = save_api_hotel(payload, self.database_path)

        self.assertEqual(saved.place_id, payload.hotel.place_id)
        self.assertEqual(
            [night.stay_date for night in saved.demo_nights],
            [date(2026, 10, day) for day in range(10, 15)],
        )
        self.assertTrue(
            all(
                night.nightly_rate_cents == 10000 and night.rooms_available == 20
                for night in saved.demo_nights
            )
        )

        connection = sqlite3.connect(self.database_path)
        try:
            connection.execute(
                """
                UPDATE demo_hotel_nights
                SET nightly_rate_cents = 23456, rooms_available = 3
                WHERE hotel_id = ? AND stay_date = '2026-10-12'
                """,
                (payload.hotel.place_id,),
            )
            connection.commit()
        finally:
            connection.close()

        repeated = save_api_hotel(payload, self.database_path)
        connection = sqlite3.connect(self.database_path)
        try:
            counts = {
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in (
                    "saved_hotels",
                    "saved_hotel_zips",
                    "demo_hotel_nights",
                )
            }
        finally:
            connection.close()

        edited_night = next(
            night for night in repeated.demo_nights if night.stay_date == date(2026, 10, 12)
        )
        self.assertEqual(
            counts,
            {
                "saved_hotels": 1,
                "saved_hotel_zips": 1,
                "demo_hotel_nights": 5,
            },
        )
        self.assertEqual(edited_night.nightly_rate_cents, 23456)
        self.assertEqual(edited_night.rooms_available, 3)

    def test_saved_hotel_lookup_is_zip_specific_with_global_saved_status(self) -> None:
        first = saved_hotel_payload()
        second = saved_hotel_payload(postcode="10036")
        save_api_hotel(first, self.database_path)
        save_api_hotel(second, self.database_path)

        state_college = list_saved_hotels("16802", self.database_path)
        new_york = list_saved_hotels("10036", self.database_path)
        empty = list_saved_hotels("22150", self.database_path)

        self.assertEqual(state_college.count, 1)
        self.assertEqual(state_college.center.postcode, "16802")
        self.assertEqual(new_york.count, 1)
        self.assertEqual(new_york.center.postcode, "10036")
        self.assertEqual(empty.count, 0)
        self.assertIsNone(empty.center)
        self.assertEqual(empty.saved_hotel_ids, [first.hotel.place_id])

    def test_chat_schema_and_read_only_hotel_query_are_separate(self) -> None:
        save_api_hotel(saved_hotel_payload(postcode="16803"), self.database_path)
        proposed_sql = """
        SELECT sh.name, sz.searched_postcode, dn.stay_date,
               dn.nightly_rate_cents / 100.0 AS nightly_rate_usd,
               dn.rooms_available
        FROM saved_hotels AS sh
        JOIN saved_hotel_zips AS sz ON sz.hotel_id = sh.hotel_id
        JOIN demo_hotel_nights AS dn ON dn.hotel_id = sh.hotel_id
        WHERE sz.searched_postcode = '16803'
          AND dn.stay_date = '2026-10-11'
          AND dn.rooms_available > 0
        ORDER BY dn.nightly_rate_cents, sh.name
        LIMIT 3
        """

        executed_sql, rows = execute_read_only_hotel_query(
            proposed_sql,
            self.database_path,
        )
        record_conversation_message(
            "conversation-1",
            "user",
            "Find three hotels.",
            self.database_path,
        )
        record_conversation_message(
            "conversation-1",
            "assistant",
            "One saved match.",
            self.database_path,
        )
        record_conversation_trace(
            "conversation-1",
            "generated_sql",
            proposed_sql,
            self.database_path,
        )

        connection = sqlite3.connect(self.database_path)
        try:
            messages = connection.execute(
                """
                SELECT message_id, conversation_id, timestamp, role, content
                FROM conversation_history ORDER BY message_id
                """
            ).fetchall()
            traces = connection.execute(
                "SELECT stage FROM conversation_traces ORDER BY trace_id"
            ).fetchall()
        finally:
            connection.close()

        self.assertIn("approved_hotel_query LIMIT 20", executed_sql)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["searched_postcode"], "16803")
        self.assertEqual(rows[0]["nightly_rate_usd"], 100.0)
        self.assertEqual([row[3] for row in messages], ["user", "assistant"])
        self.assertTrue(all(row[0] and row[1] and row[2] for row in messages))
        self.assertEqual(traces, [("generated_sql",)])

    def test_hotel_query_rejects_writes_and_unapproved_tables(self) -> None:
        invalid_queries = (
            "DELETE FROM saved_hotels",
            "SELECT * FROM users LIMIT 1",
            "SELECT * FROM saved_hotels; SELECT * FROM demo_hotel_nights",
        )
        for query in invalid_queries:
            with self.subTest(query=query), self.assertRaises(
                HotelQueryValidationError
            ):
                execute_read_only_hotel_query(query, self.database_path)

    def test_delete_saved_hotel_removes_only_its_local_graph(self) -> None:
        deleted_id = "provider-hotel-delete"
        kept_id = "provider-hotel-keep"
        save_api_hotel(saved_hotel_payload(deleted_id), self.database_path)
        save_api_hotel(saved_hotel_payload(deleted_id, "10036"), self.database_path)
        save_api_hotel(saved_hotel_payload(kept_id), self.database_path)

        delete_saved_hotel(deleted_id, self.database_path)

        connection = sqlite3.connect(self.database_path)
        try:
            deleted_counts = {
                table: connection.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE hotel_id = ?", (deleted_id,)
                ).fetchone()[0]
                for table in (
                    "saved_hotels",
                    "saved_hotel_zips",
                    "demo_hotel_nights",
                )
            }
            kept_counts = {
                table: connection.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE hotel_id = ?", (kept_id,)
                ).fetchone()[0]
                for table in (
                    "saved_hotels",
                    "saved_hotel_zips",
                    "demo_hotel_nights",
                )
            }
        finally:
            connection.close()

        self.assertEqual(deleted_counts, {table: 0 for table in deleted_counts})
        self.assertEqual(
            kept_counts,
            {
                "saved_hotels": 1,
                "saved_hotel_zips": 1,
                "demo_hotel_nights": 5,
            },
        )
        with self.assertRaises(SavedHotelNotFoundError):
            delete_saved_hotel(deleted_id, self.database_path)

    def test_create_read_cancel_and_delete_test_booking(self) -> None:
        created = create_booking(
            "U006", "T011", self.database_path, booked_on=date(2026, 9, 21)
        )

        self.assertEqual(created.booking_id, "B007")
        self.assertEqual(created.status, "confirmed")
        self.assertTrue(created.can_delete)
        self.assertEqual(
            [booking.booking_id for booking in list_bookings("U006", self.database_path)],
            ["B007"],
        )

        cancelled = cancel_booking("B007", self.database_path)
        self.assertEqual(cancelled.status, "cancelled")
        self.assertEqual(len(list_bookings("U006", self.database_path)), 1)

        delete_booking("B007", self.database_path)
        self.assertEqual(list_bookings("U006", self.database_path), [])

    def test_reinitialization_does_not_restore_deleted_or_duplicate_records(self) -> None:
        created = create_booking("U006", "T011", self.database_path)
        delete_booking(created.booking_id, self.database_path)
        initialize_database(self.database_path)

        self.assertEqual(list_bookings("U006", self.database_path), [])
        self.assertEqual(len(list_users(self.database_path)), 6)

    def test_seed_booking_cannot_be_deleted(self) -> None:
        with self.assertRaisesRegex(BookingConflictError, "Seed bookings"):
            delete_booking("B001", self.database_path)


if __name__ == "__main__":
    unittest.main()
