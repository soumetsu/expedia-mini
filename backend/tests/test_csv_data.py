"""Tests for typed four-file seed loading and validation."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.controllers.seed import DATA_DIRECTORY, SeedDataError, load_seed_data


class SeedDataTests(unittest.TestCase):
    def test_supplied_counts_and_relationships(self) -> None:
        seed = load_seed_data()

        self.assertEqual(len(seed.hotels), 8)
        self.assertEqual(len(seed.trips), 12)
        self.assertEqual(len(seed.users), 6)
        self.assertEqual(len(seed.bookings), 6)

        hotel_ids = {hotel.hotel_id for hotel in seed.hotels}
        trip_ids = {trip.trip_id for trip in seed.trips}
        user_ids = {user.user_id for user in seed.users}
        self.assertTrue(all(trip.hotel_id in hotel_ids for trip in seed.trips))
        self.assertTrue(
            all(booking.trip_id in trip_ids for booking in seed.bookings)
        )
        self.assertTrue(
            all(booking.user_id in user_ids for booking in seed.bookings)
        )

    def test_default_data_path_does_not_depend_on_working_directory(self) -> None:
        original_directory = Path.cwd()
        with TemporaryDirectory() as temporary_directory:
            try:
                os.chdir(temporary_directory)
                seed = load_seed_data()
            finally:
                os.chdir(original_directory)

        self.assertTrue(DATA_DIRECTORY.is_absolute())
        self.assertEqual(len(seed.bookings), 6)

    def test_missing_csv_is_reported_as_seed_error(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(SeedDataError, "Unable to read hotels.csv"):
                load_seed_data(Path(temporary_directory))


if __name__ == "__main__":
    unittest.main()
