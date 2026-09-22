"""Tests for FastAPI route configuration and handlers."""

import asyncio
import unittest

from fastapi import HTTPException

from app.main import app
from app.routes import health_check, hotel_search, recommended_hotels


class RouteTests(unittest.TestCase):
    def test_required_get_routes_are_registered(self) -> None:
        api_paths = app.openapi()["paths"]

        self.assertIn("get", api_paths["/api/health"])
        self.assertIn("get", api_paths["/api/hotels/search"])
        self.assertIn("get", api_paths["/api/hotels/recommended"])
        self.assertIn("get", api_paths["/api/users"])
        self.assertIn("get", api_paths["/api/bookings"])
        self.assertIn("post", api_paths["/api/bookings"])
        self.assertIn("patch", api_paths["/api/bookings/{booking_id}/cancel"])
        self.assertIn("delete", api_paths["/api/bookings/{booking_id}"])

    def test_health_handler(self) -> None:
        response = asyncio.run(health_check())

        self.assertEqual(response.status, "ok")

    def test_search_handler(self) -> None:
        response = asyncio.run(hotel_search(" Boston "))

        self.assertEqual(response.query, "Boston")
        self.assertEqual(response.count, 4)

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
