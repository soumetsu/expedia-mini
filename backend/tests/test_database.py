"""Tests for SQLite seeding and booking CRUD behavior."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from app.controllers.database import (
    BookingConflictError,
    cancel_booking,
    create_booking,
    delete_booking,
    fetch_hotel_stays,
    initialize_database,
    list_bookings,
    list_users,
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
