"""Tests for CSV loading and validation."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.csv_data import CatalogDataError, DATA_DIRECTORY, load_catalog


class CsvDataTests(unittest.TestCase):
    def test_supplied_catalog_counts_and_relationships(self) -> None:
        catalog = load_catalog()

        self.assertEqual(len(catalog.hotels), 8)
        self.assertEqual(len(catalog.trips), 12)
        hotel_ids = {hotel.hotel_id for hotel in catalog.hotels}
        self.assertEqual(len(hotel_ids), len(catalog.hotels))
        self.assertTrue(all(trip.hotel_id in hotel_ids for trip in catalog.trips))

    def test_default_data_path_does_not_depend_on_working_directory(self) -> None:
        original_directory = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary_directory:
            try:
                os.chdir(temporary_directory)
                catalog = load_catalog()
            finally:
                os.chdir(original_directory)

        self.assertTrue(DATA_DIRECTORY.is_absolute())
        self.assertEqual(len(catalog.hotels), 8)

    def test_missing_csv_is_reported_as_data_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(CatalogDataError, "Unable to read hotels.csv"):
                load_catalog(Path(temporary_directory))


if __name__ == "__main__":
    unittest.main()
