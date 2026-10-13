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
from app.controllers.chat import ChatConfigurationError, ChatProviderError
from app.models import (
    ChatRequest,
    ChatResponse,
    NearbyHotelResponse,
    NearbyHotelSearchResponse,
    PostcodeCenterResponse,
    SavedHotelCreateRequest,
    SavedHotelResponse,
    SavedHotelSearchResponse,
)
from app.routes import (
    health_check,
    hotel_search,
    nearby_hotels,
    remove_saved_hotel,
    recommended_hotels,
    save_hotel,
    saved_hotels,
    support_chat,
)


class RouteTests(unittest.TestCase):
    def test_required_get_routes_are_registered(self) -> None:
        api_paths = app.openapi()["paths"]

        self.assertIn("get", api_paths["/api/health"])
        self.assertIn("post", api_paths["/api/chat"])
        self.assertNotIn("/api/demo/zip-location", api_paths)
        self.assertIn("get", api_paths["/api/hotels/nearby"])
        self.assertIn("get", api_paths["/api/hotels/search"])
        self.assertIn("get", api_paths["/api/hotels/recommended"])
        self.assertIn("get", api_paths["/api/saved-hotels"])
        self.assertIn("post", api_paths["/api/saved-hotels"])
        self.assertIn("delete", api_paths["/api/saved-hotels/{hotel_id}"])
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

    def test_support_chat_uses_controller_and_sanitizes_failures(self) -> None:
        payload = ChatRequest(message="How do I search?")
        expected = ChatResponse(
            reply="Enter a five-digit U.S. ZIP.",
            model="gemini-3.5-flash-lite",
            conversation_id="conversation-1",
            retrieval_mode="support_only",
            generated_sql="NO_QUERY",
            result_summary='{"row_count":0}',
            retrieved_rows=[],
            usage={
                "prompt_tokens": 42,
                "response_tokens": 9,
                "total_tokens": 51,
            },
        )
        with patch("app.routes.request_support_reply", return_value=expected) as mocked:
            response = asyncio.run(support_chat(payload))
        mocked.assert_called_once_with(payload)
        self.assertEqual(response, expected)

        for error, status_code in (
            (ChatConfigurationError("secret"), 503),
            (ChatProviderError("secret"), 502),
        ):
            with self.subTest(status_code=status_code), patch(
                "app.routes.request_support_reply",
                side_effect=error,
            ), self.assertRaises(HTTPException) as raised:
                asyncio.run(support_chat(payload))
            self.assertEqual(raised.exception.status_code, status_code)
            self.assertNotIn("secret", raised.exception.detail)

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

    def test_saved_hotel_handlers_use_local_storage_controller(self) -> None:
        center = PostcodeCenterResponse(
            postcode="16802",
            country_code="us",
            latitude=40.7989,
            longitude=-77.8599,
            locality="State College",
            state="Pennsylvania",
        )
        hotel = NearbyHotelResponse(
            place_id="hotel-1",
            name="Campus Hotel",
            formatted_address="State College, PA 16802",
            latitude=40.8,
            longitude=-77.86,
            distance_meters=123,
            distance_miles=0.08,
        )
        payload = SavedHotelCreateRequest(
            postcode="16802",
            center=center,
            search_scope="postcode boundary",
            hotel=hotel,
        )
        saved = SavedHotelResponse(**hotel.model_dump(), demo_nights=[])
        search = SavedHotelSearchResponse(
            query="16802",
            count=1,
            search_scope="postcode boundary",
            center=center,
            results=[saved],
            saved_hotel_ids=["hotel-1"],
        )

        with patch("app.routes.list_saved_hotel_records", return_value=search) as listed:
            response = asyncio.run(saved_hotels("16802"))
        listed.assert_called_once_with("16802")
        self.assertEqual(response, search)

        with patch("app.routes.save_api_hotel_record", return_value=saved) as saved_call:
            response = asyncio.run(save_hotel(payload))
        saved_call.assert_called_once_with(payload)
        self.assertEqual(response, saved)

        with patch("app.routes.delete_saved_hotel_record") as deleted:
            response = asyncio.run(remove_saved_hotel("hotel-1"))
        deleted.assert_called_once_with("hotel-1")
        self.assertEqual(response.status_code, 204)

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
