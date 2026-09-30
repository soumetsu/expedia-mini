"""Mocked contract tests for live Geoapify hotel discovery."""

import json
import os
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
from unittest import TestCase
from unittest.mock import patch

from app.controllers.geocoding import (
    GEOAPIFY_GEOCODING_URL,
    GEOAPIFY_PLACES_URL,
    GEOAPIFY_TIMEOUT_SECONDS,
    GeoapifyProviderError,
    lookup_postcode,
    search_hotels_by_postcode,
)


class MockResponse:
    def __init__(self, payload: object, status: int = 200) -> None:
        self.status = status
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "MockResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def postcode_payload() -> dict[str, object]:
    return {
        "results": [
            {
                "postcode": "16802",
                "country_code": "us",
                "lat": 40.7989,
                "lon": -77.8599,
                "city": "State College",
                "state": "Pennsylvania",
                "place_id": "postcode-place-id",
            }
        ]
    }


class GeocodingTests(TestCase):
    def test_matching_postcode_returns_boundary_and_center(self) -> None:
        with patch.dict(os.environ, {"GEOAPIFY_API_KEY": "test-key"}, clear=True), patch(
            "app.controllers.geocoding.urlopen",
            return_value=MockResponse(postcode_payload()),
        ) as mocked_urlopen:
            response = lookup_postcode("16802")

        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual(response.place_id, "postcode-place-id")
        self.assertEqual(response.center.postcode, "16802")
        self.assertEqual(response.center.locality, "State College")
        self.assertEqual(response.center.state, "Pennsylvania")
        request, = mocked_urlopen.call_args.args
        self.assertTrue(request.full_url.startswith(GEOAPIFY_GEOCODING_URL))
        query = parse_qs(urlparse(request.full_url).query)
        self.assertEqual(query["postcode"], ["16802"])
        self.assertEqual(query["type"], ["postcode"])
        self.assertEqual(query["filter"], ["countrycode:us"])
        self.assertEqual(query["format"], ["json"])
        self.assertEqual(query["limit"], ["5"])
        mocked_urlopen.assert_called_once_with(request, timeout=GEOAPIFY_TIMEOUT_SECONDS)

    def test_mismatched_or_incomplete_location_is_unresolved(self) -> None:
        payload = {
            "results": [
                {
                    "postcode": "16803",
                    "country_code": "us",
                    "lat": 40.8,
                    "lon": -77.8,
                    "place_id": "wrong-postcode",
                },
                {
                    "postcode": "16802",
                    "country_code": "us",
                    "lat": 999,
                    "lon": -77.8,
                    "place_id": "invalid-coordinates",
                },
                {
                    "postcode": "16802",
                    "country_code": "us",
                    "lat": 40.8,
                    "lon": -77.8,
                },
            ]
        }
        with patch.dict(os.environ, {"GEOAPIFY_API_KEY": "test-key"}, clear=True), patch(
            "app.controllers.geocoding.urlopen",
            return_value=MockResponse(payload),
        ):
            self.assertIsNone(lookup_postcode("16802"))

    def test_hotel_search_uses_zip_boundary_and_returns_sorted_distances(self) -> None:
        places_payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "place_id": "hotel-farther",
                        "name": "Farther Hotel",
                        "formatted": "2 College Avenue, State College, PA 16802",
                        "city": "State College",
                        "state": "Pennsylvania",
                        "postcode": "16802",
                        "lat": 40.8089,
                        "lon": -77.8599,
                    },
                    "geometry": {"type": "Point", "coordinates": [-77.8599, 40.8089]},
                },
                {
                    "type": "Feature",
                    "properties": {
                        "place_id": "hotel-farther-duplicate",
                        "name": "FARTHER HOTEL",
                        "formatted": "Alternate provider record, State College, PA 16802",
                        "city": "State College",
                        "state": "Pennsylvania",
                        "postcode": "16802",
                        "lat": 40.8189,
                        "lon": -77.8599,
                    },
                },
                {
                    "type": "Feature",
                    "properties": {
                        "place_id": "hotel-nearer",
                        "name": "  Campus Hotel  ",
                        "formatted": "1 College Avenue, State College, PA 16802",
                        "city": "State College",
                        "state": "Pennsylvania",
                        "postcode": "16802",
                    },
                    "geometry": {"type": "Point", "coordinates": [-77.8599, 40.8009]},
                },
            ],
        }
        with patch.dict(os.environ, {"GEOAPIFY_API_KEY": "test-key"}, clear=True), patch(
            "app.controllers.geocoding.urlopen",
            side_effect=[MockResponse(postcode_payload()), MockResponse(places_payload)],
        ) as mocked_urlopen:
            response = search_hotels_by_postcode("16802")

        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual(response.count, 2)
        self.assertEqual(
            [hotel.place_id for hotel in response.results],
            ["hotel-nearer", "hotel-farther"],
        )
        self.assertEqual(response.results[0].name, "Campus Hotel")
        self.assertGreater(response.results[0].distance_meters, 0)
        self.assertGreater(response.results[0].distance_miles, 0)
        self.assertTrue(response.results[0].inside_searched_postcode)
        self.assertEqual(response.search_scope, "postcode boundary")
        self.assertIsNone(response.search_radius_miles)
        self.assertEqual(response.hotel_source, "Geoapify Places API")
        self.assertEqual(response.postcode_source, "Geoapify Geocoding API")

        places_request = mocked_urlopen.call_args_list[1].args[0]
        self.assertTrue(places_request.full_url.startswith(GEOAPIFY_PLACES_URL))
        query = parse_qs(urlparse(places_request.full_url).query)
        self.assertEqual(query["categories"], ["accommodation.hotel"])
        self.assertEqual(query["filter"], ["place:postcode-place-id"])
        self.assertEqual(query["bias"], ["proximity:-77.8599,40.7989"])
        self.assertEqual(query["limit"], ["20"])

    def test_empty_places_response_is_a_successful_search(self) -> None:
        with patch.dict(os.environ, {"GEOAPIFY_API_KEY": "test-key"}, clear=True), patch(
            "app.controllers.geocoding.urlopen",
            side_effect=[
                MockResponse(postcode_payload()),
                MockResponse({"type": "FeatureCollection", "features": []}),
                MockResponse({"type": "FeatureCollection", "features": []}),
                MockResponse({"type": "FeatureCollection", "features": []}),
                MockResponse({"type": "FeatureCollection", "features": []}),
            ],
        ):
            response = search_hotels_by_postcode("16802")

        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual(response.count, 0)
        self.assertEqual(response.results, [])
        self.assertEqual(response.search_scope, "expanded radius")
        self.assertEqual(response.search_radius_miles, 30)

    def test_empty_boundary_falls_back_to_live_five_mile_circle(self) -> None:
        boundary_payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "place_id": "adjacent-boundary-result",
                        "name": "Nearby Live Hotel",
                        "postcode": "16801",
                        "lat": 40.8089,
                        "lon": -77.8599,
                    },
                }
            ],
        }
        circle_payload = {
            "type": "FeatureCollection",
            "features": [
                boundary_payload["features"][0],
                {
                    "type": "Feature",
                    "properties": {
                        "place_id": "missing-postcode",
                        "name": "Provider Postcode Missing",
                        "lat": 40.7989,
                        "lon": -77.8499,
                    },
                },
                {
                    "type": "Feature",
                    "properties": {
                        "place_id": "outside-circle",
                        "name": "Outside Requested Radius",
                        "postcode": "16801",
                        "lat": 40.9989,
                        "lon": -77.8599,
                    },
                },
            ],
        }
        with patch.dict(os.environ, {"GEOAPIFY_API_KEY": "test-key"}, clear=True), patch(
            "app.controllers.geocoding.urlopen",
            side_effect=[
                MockResponse(postcode_payload()),
                MockResponse(boundary_payload),
                MockResponse(circle_payload),
            ],
        ) as mocked_urlopen:
            response = search_hotels_by_postcode("16802")

        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual(response.search_scope, "expanded radius")
        self.assertEqual(response.search_radius_miles, 5)
        self.assertEqual(response.count, 2)
        self.assertEqual(
            [hotel.place_id for hotel in response.results],
            ["missing-postcode", "adjacent-boundary-result"],
        )
        self.assertIsNone(response.results[0].inside_searched_postcode)
        self.assertFalse(response.results[1].inside_searched_postcode)

        circle_request = mocked_urlopen.call_args_list[2].args[0]
        query = parse_qs(urlparse(circle_request.full_url).query)
        self.assertEqual(query["filter"], ["circle:-77.8599,40.7989,8047"])
        self.assertEqual(query["bias"], ["proximity:-77.8599,40.7989"])

    def test_fallback_stops_at_first_nonempty_expanded_radius(self) -> None:
        empty_places = {"type": "FeatureCollection", "features": []}
        fifteen_mile_payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "place_id": "hotel-within-fifteen",
                        "name": "Regional Hotel",
                        "postcode": "16801",
                        "lat": 40.8989,
                        "lon": -77.8599,
                    },
                }
            ],
        }
        with patch.dict(os.environ, {"GEOAPIFY_API_KEY": "test-key"}, clear=True), patch(
            "app.controllers.geocoding.urlopen",
            side_effect=[
                MockResponse(postcode_payload()),
                MockResponse(empty_places),
                MockResponse(empty_places),
                MockResponse(fifteen_mile_payload),
            ],
        ) as mocked_urlopen:
            response = search_hotels_by_postcode("16802")

        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual(response.search_radius_miles, 15)
        self.assertEqual(response.count, 1)
        self.assertEqual(len(mocked_urlopen.call_args_list), 4)
        fifteen_mile_request = mocked_urlopen.call_args_list[3].args[0]
        query = parse_qs(urlparse(fifteen_mile_request.full_url).query)
        self.assertEqual(query["filter"], ["circle:-77.8599,40.7989,24140"])

    def test_places_omit_unusable_features_and_preserve_missing_name(self) -> None:
        places_payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "place_id": "unnamed-hotel",
                        "formatted": "State College, PA 16802",
                        "postcode": "16802",
                        "lat": 40.8,
                        "lon": -77.86,
                    },
                },
                {
                    "type": "Feature",
                    "properties": {
                        "name": "Missing identifier",
                        "postcode": "16802",
                    },
                    "geometry": {"type": "Point", "coordinates": [-77.8, 40.8]},
                },
                {
                    "type": "Feature",
                    "properties": {
                        "place_id": "outside-postcode",
                        "name": "Outside ZIP",
                        "postcode": "16801",
                        "lat": 40.801,
                        "lon": -77.86,
                    },
                },
            ],
        }
        with patch.dict(os.environ, {"GEOAPIFY_API_KEY": "test-key"}, clear=True), patch(
            "app.controllers.geocoding.urlopen",
            side_effect=[MockResponse(postcode_payload()), MockResponse(places_payload)],
        ):
            response = search_hotels_by_postcode("16802")

        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual(response.count, 1)
        self.assertIsNone(response.results[0].name)

    def test_provider_failure_is_distinct_from_empty_results(self) -> None:
        with patch.dict(os.environ, {"GEOAPIFY_API_KEY": "test-key"}, clear=True), patch(
            "app.controllers.geocoding.urlopen",
            side_effect=URLError("provider failure with secret-like details"),
        ):
            with self.assertRaises(GeoapifyProviderError) as raised:
                lookup_postcode("16802")

        self.assertEqual(str(raised.exception), "Geoapify request failed.")

    def test_missing_key_prevents_provider_requests(self) -> None:
        with patch.dict(os.environ, {}, clear=True), patch(
            "app.controllers.geocoding.urlopen"
        ) as mocked_urlopen:
            with self.assertRaises(GeoapifyProviderError) as raised:
                search_hotels_by_postcode("16802")

        self.assertEqual(str(raised.exception), "Geoapify is not configured.")
        mocked_urlopen.assert_not_called()


if __name__ == "__main__":
    import unittest

    unittest.main()
