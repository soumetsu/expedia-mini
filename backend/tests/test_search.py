"""Tests for SQLite-backed location search and recommendations."""

from datetime import date
from decimal import Decimal
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from app.controllers.catalog import recommend_hotel_stays, search_hotel_stays
from app.controllers.database import initialize_database


class HotelSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "test.db"
        initialize_database(self.database_path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def search(self, name: str, **kwargs):
        return search_hotel_stays(name, database_path=self.database_path, **kwargs)

    def test_search_trims_casefolds_and_returns_all_matching_stays(self) -> None:
        response = self.search("  hArBoR lAnTeRn  ")

        self.assertEqual(response.query, "hArBoR lAnTeRn")
        self.assertEqual(response.count, 2)
        self.assertEqual(
            [result.trip_id for result in response.results], ["T001", "T009"]
        )
        self.assertTrue(all(result.hotel_id == "H001" for result in response.results))

    def test_result_includes_display_and_calculated_fields(self) -> None:
        result = self.search("Harbor Lantern Hotel").results[0]

        self.assertEqual(result.hotel_name, "Harbor Lantern Hotel")
        self.assertEqual(result.city, "Boston")
        self.assertEqual(result.state, "MA")
        self.assertEqual(result.nightly_rate_usd, Decimal("150"))
        self.assertEqual(result.trip_name, "Boston Harbor Weekend")
        self.assertEqual(result.nights, 2)
        self.assertEqual(result.estimated_stay_price_usd, Decimal("300"))

    def test_partial_name_can_match_multiple_hotels(self) -> None:
        response = self.search("hotel")

        self.assertEqual(response.count, 8)
        self.assertEqual(
            {result.hotel_id for result in response.results},
            {"H001", "H003", "H004", "H006", "H007"},
        )

    def test_city_search_returns_every_stay_in_destination(self) -> None:
        response = self.search("  bOsToN ")

        self.assertEqual(response.query, "bOsToN")
        self.assertEqual(response.count, 4)
        self.assertEqual(
            [result.trip_id for result in response.results],
            ["T001", "T002", "T009", "T010"],
        )

    def test_state_search_returns_matching_destinations(self) -> None:
        response = self.search("PA")

        self.assertEqual(response.count, 3)
        self.assertEqual(
            {result.hotel_id for result in response.results},
            {"H005", "H006", "H008"},
        )

    def test_date_window_filters_fixed_stays(self) -> None:
        response = self.search(
            "New York",
            check_in=date(2026, 9, 21),
            check_out=date(2026, 10, 1),
        )

        self.assertEqual(
            [result.trip_id for result in response.results], ["T003", "T004"]
        )

    def test_invalid_date_window_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "after check-in"):
            self.search(
                "Boston",
                check_in=date(2026, 10, 2),
                check_out=date(2026, 10, 2),
            )

    def test_recommendations_are_ranked_and_use_distinct_hotels(self) -> None:
        response = recommend_hotel_stays(3, database_path=self.database_path)

        self.assertEqual(response.query, "Recommended stays")
        self.assertEqual(response.count, 3)
        self.assertEqual(
            [result.trip_id for result in response.results],
            ["T008", "T005", "T001"],
        )
        self.assertEqual(len({result.hotel_id for result in response.results}), 3)

    def test_unknown_name_returns_empty_results(self) -> None:
        response = self.search("No Such Expedia-Mini Hotel")

        self.assertEqual(response.count, 0)
        self.assertEqual(response.results, [])

    def test_blank_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be blank"):
            self.search("   ")

    def test_recommendation_limit_must_be_positive(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            recommend_hotel_stays(0, database_path=self.database_path)

    def test_catalog_reads_reflect_sqlite_changes_after_seed(self) -> None:
        connection = sqlite3.connect(self.database_path)
        try:
            connection.execute(
                "UPDATE hotels SET hotel_name = ? WHERE hotel_id = ?",
                ("SQLite Harbor Hotel", "H001"),
            )
            connection.commit()
        finally:
            connection.close()

        response = self.search("SQLite Harbor")

        self.assertEqual(response.count, 2)
        self.assertTrue(
            all(result.hotel_name == "SQLite Harbor Hotel" for result in response.results)
        )


if __name__ == "__main__":
    unittest.main()
