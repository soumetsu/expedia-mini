"""Tests for FastAPI route configuration and handlers."""

import asyncio
import unittest

from fastapi import HTTPException

from app.main import app
from app.routes import health_check, hotel_search


class RouteTests(unittest.TestCase):
    def test_required_get_routes_are_registered(self) -> None:
        api_paths = app.openapi()["paths"]

        self.assertIn("get", api_paths["/api/health"])
        self.assertIn("get", api_paths["/api/hotels/search"])

    def test_health_handler(self) -> None:
        response = asyncio.run(health_check())

        self.assertEqual(response.status, "ok")

    def test_search_handler(self) -> None:
        response = asyncio.run(hotel_search(" lantern "))

        self.assertEqual(response.query, "lantern")
        self.assertEqual(response.count, 2)

    def test_search_handler_rejects_whitespace(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            asyncio.run(hotel_search("   "))

        self.assertEqual(raised.exception.status_code, 422)
        self.assertEqual(raised.exception.detail, "Hotel name must not be blank.")


if __name__ == "__main__":
    unittest.main()
