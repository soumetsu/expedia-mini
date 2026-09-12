"""Tests for hotel-name search and joined stay responses."""

from decimal import Decimal
import unittest

from app.csv_data import load_catalog
from app.search import search_hotel_stays


class HotelSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_catalog()

    def test_search_trims_casefolds_and_returns_all_matching_stays(self) -> None:
        response = search_hotel_stays(self.catalog, "  hArBoR lAnTeRn  ")

        self.assertEqual(response.query, "hArBoR lAnTeRn")
        self.assertEqual(response.count, 2)
        self.assertEqual(
            [result.trip_id for result in response.results],
            ["T001", "T009"],
        )
        self.assertTrue(
            all(result.hotel_id == "H001" for result in response.results)
        )

    def test_result_includes_display_and_calculated_fields(self) -> None:
        result = search_hotel_stays(
            self.catalog, "Harbor Lantern Hotel"
        ).results[0]

        self.assertEqual(result.hotel_name, "Harbor Lantern Hotel")
        self.assertEqual(result.city, "Boston")
        self.assertEqual(result.state, "MA")
        self.assertEqual(result.nightly_rate_usd, Decimal("150"))
        self.assertEqual(result.trip_name, "Boston Harbor Weekend")
        self.assertEqual(result.nights, 2)
        self.assertEqual(result.estimated_stay_price_usd, Decimal("300"))

    def test_partial_name_can_match_multiple_hotels(self) -> None:
        response = search_hotel_stays(self.catalog, "hotel")

        self.assertEqual(response.count, 8)
        self.assertEqual(
            {result.hotel_id for result in response.results},
            {"H001", "H003", "H004", "H006", "H007"},
        )

    def test_unknown_name_returns_empty_results(self) -> None:
        response = search_hotel_stays(self.catalog, "No Such Expedia-Mini Hotel")

        self.assertEqual(response.count, 0)
        self.assertEqual(response.results, [])

    def test_blank_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be blank"):
            search_hotel_stays(self.catalog, "   ")


if __name__ == "__main__":
    unittest.main()
