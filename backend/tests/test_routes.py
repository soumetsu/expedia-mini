"""Tests for FastAPI route configuration and handlers."""

import asyncio
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.main import app
from app.controllers.geocoding import (
    GeoapifyConfigurationError,
    GeoapifyProviderError,
)
from app.models import (
    NearbyHotelResponse,
    NearbyHotelSearchResponse,
    PostcodeCenterResponse,
)
from app.routes import (
    health_check,
    hotel_search,
    nearby_hotels,
    recommended_hotels,
)


class RouteTests(unittest.TestCase):
    def test_required_get_routes_are_registered(self) -> None:
        api_paths = app.openapi()["paths"]

        self.assertIn("get", api_paths["/api/health"])
        self.assertNotIn("/api/demo/zip-location", api_paths)
        self.assertIn("get", api_paths["/api/hotels/nearby"])
        self.assertIn("get", api_paths["/api/hotels/search"])
        self.assertIn("get", api_paths["/api/hotels/recommended"])
        self.assertIn("get", api_paths["/api/users"])
        self.assertIn("get", api_paths["/api/bookings"])
        self.assertIn("post", api_paths["/api/bookings"])
        self.assertIn("patch", api_paths["/api/bookings/{booking_id}/cancel"])
        self.assertIn("delete", api_paths["/api/bookings/{booking_id}"])

    def test_health_handler(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            response = asyncio.run(health_check())

        self.assertEqual(response.status, "ok")
        self.assertEqual(response.geoapify_api_key_status, "key is not configured")

    def test_search_handler(self) -> None:
        response = asyncio.run(hotel_search(" Boston "))

        self.assertEqual(response.query, "Boston")
        self.assertEqual(response.count, 4)

    def test_nearby_hotels_returns_live_controller_response(self) -> None:
        expected = NearbyHotelSearchResponse(
            query="16802",
            count=1,
            center=PostcodeCenterResponse(
                postcode="16802",
                country_code="us",
                latitude=40.7989,
                longitude=-77.8599,
                locality="State College",
                state="Pennsylvania",
            ),
            results=[
                NearbyHotelResponse(
                    place_id="hotel-1",
                    name="Campus Hotel",
                    formatted_address="State College, PA 16802",
                    latitude=40.8,
                    longitude=-77.86,
                    distance_meters=123,
                    distance_miles=0.08,
                )
            ],
        )
        with patch(
            "app.routes.search_hotels_by_postcode", return_value=expected
        ) as mocked:
            response = asyncio.run(nearby_hotels("16802"))

        mocked.assert_called_once_with("16802", 20)
        self.assertEqual(response, expected)

    def test_nearby_hotels_rejects_invalid_zip(self) -> None:
        for postcode in ("1680", "ABCDE", "16802-1234"):
            with self.subTest(postcode=postcode), self.assertRaises(HTTPException) as raised:
                asyncio.run(nearby_hotels(postcode))
            self.assertEqual(raised.exception.status_code, 422)
            self.assertEqual(
                raised.exception.detail,
                "Enter a valid 5-digit U.S. ZIP code.",
            )

    def test_nearby_hotels_maps_unresolved_zip_to_not_found(self) -> None:
        with patch("app.routes.search_hotels_by_postcode", return_value=None):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(nearby_hotels("16802"))

        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(raised.exception.detail, "ZIP code 16802 could not be resolved.")

    def test_nearby_hotels_maps_missing_configuration(self) -> None:
        with patch(
            "app.routes.search_hotels_by_postcode",
            side_effect=GeoapifyConfigurationError("secret must not escape"),
        ):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(nearby_hotels("16802"))

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "Live hotel search is not configured.")

    def test_nearby_hotels_maps_provider_failure(self) -> None:
        with patch(
            "app.routes.search_hotels_by_postcode",
            side_effect=GeoapifyProviderError("provider URL with secret must not escape"),
        ):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(nearby_hotels("16802"))

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "The live hotel provider request failed.")

    def test_recommendations_handler(self) -> None:
        response = asyncio.run(recommended_hotels(3))

        self.assertEqual(response.count, 3)
        self.assertEqual(
            [result.trip_id for result in response.results],
            ["T008", "T005", "T001"],
        )

    def test_search_handler_rejects_whitespace(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            asyncio.run(hotel_search("   "))

        self.assertEqual(raised.exception.status_code, 422)
        self.assertEqual(raised.exception.detail, "Search location must not be blank.")


if __name__ == "__main__":
    unittest.main()
