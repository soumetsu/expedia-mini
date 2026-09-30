"""Geoapify postcode resolution and live nearby-hotel discovery."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..config import get_geoapify_api_key
from ..models import (
    NearbyHotelResponse,
    NearbyHotelSearchResponse,
    PostcodeCenterResponse,
)


GEOAPIFY_GEOCODING_URL = "https://api.geoapify.com/v1/geocode/search"
GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"
GEOAPIFY_TIMEOUT_SECONDS = 10.0
DEFAULT_HOTEL_LIMIT = 20
MAX_HOTEL_LIMIT = 50
METERS_PER_MILE = 1609.344
EARTH_RADIUS_METERS = 6_371_008.8
FALLBACK_RADIUS_MILES = (5, 15, 30)


class GeoapifyProviderError(RuntimeError):
    """Raised when Geoapify cannot provide a usable response."""


class GeoapifyConfigurationError(GeoapifyProviderError):
    """Raised when the backend Geoapify API key is not configured."""


@dataclass(frozen=True)
class ResolvedPostcode:
    """Internal postcode data needed to constrain the Places request."""

    place_id: str
    center: PostcodeCenterResponse


def _clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _valid_coordinate(value: Any, minimum: float, maximum: float) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        coordinate = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(coordinate) or not minimum <= coordinate <= maximum:
        return None
    return coordinate


def _locality_from_result(result: dict[str, Any]) -> str | None:
    for field in ("locality", "city", "town", "village", "municipality"):
        locality = _clean_text(result.get(field))
        if locality:
            return locality
    return None


def _request_json(url: str, parameters: dict[str, object]) -> dict[str, Any]:
    request = Request(
        f"{url}?{urlencode(parameters)}",
        headers={"Accept": "application/json", "User-Agent": "Expedia-Mini/1.0"},
    )
    try:
        with urlopen(request, timeout=GEOAPIFY_TIMEOUT_SECONDS) as response:
            status_code = getattr(response, "status", 200)
            if not isinstance(status_code, int) or not 200 <= status_code < 300:
                raise GeoapifyProviderError(
                    "Geoapify returned an unsuccessful response."
                )
            payload = json.loads(response.read())
    except GeoapifyProviderError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError):
        raise GeoapifyProviderError("Geoapify request failed.") from None

    if not isinstance(payload, dict):
        raise GeoapifyProviderError("Geoapify returned an invalid response.")
    return payload


def _api_key() -> str:
    api_key = get_geoapify_api_key()
    if api_key is None:
        raise GeoapifyConfigurationError("Geoapify is not configured.")
    return api_key


def lookup_postcode(postcode: str) -> ResolvedPostcode | None:
    """Resolve an exact U.S. ZIP code and retain its Geoapify boundary ID."""

    requested_postcode = postcode.strip()
    if not requested_postcode:
        raise ValueError("ZIP code must not be blank.")

    payload = _request_json(
        GEOAPIFY_GEOCODING_URL,
        {
            "postcode": requested_postcode,
            "type": "postcode",
            "filter": "countrycode:us",
            "format": "json",
            "limit": 5,
            "apiKey": _api_key(),
        },
    )
    results = payload.get("results")
    if not isinstance(results, list):
        raise GeoapifyProviderError("Geoapify returned an invalid response.")

    for result in results:
        if not isinstance(result, dict):
            continue
        result_postcode = _clean_text(result.get("postcode"))
        country_code = _clean_text(result.get("country_code"))
        place_id = _clean_text(result.get("place_id"))
        if not result_postcode or not country_code or not place_id:
            continue
        if result_postcode.casefold() != requested_postcode.casefold():
            continue
        if country_code.casefold() != "us":
            continue

        latitude = _valid_coordinate(result.get("lat"), -90, 90)
        longitude = _valid_coordinate(result.get("lon"), -180, 180)
        if latitude is None or longitude is None:
            continue

        return ResolvedPostcode(
            place_id=place_id,
            center=PostcodeCenterResponse(
                postcode=requested_postcode,
                country_code="us",
                latitude=latitude,
                longitude=longitude,
                locality=_locality_from_result(result),
                state=_clean_text(result.get("state")),
            ),
        )
    return None


def _haversine_meters(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> float:
    origin_latitude_radians = math.radians(origin_latitude)
    destination_latitude_radians = math.radians(destination_latitude)
    latitude_delta = math.radians(destination_latitude - origin_latitude)
    longitude_delta = math.radians(destination_longitude - origin_longitude)
    haversine = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(origin_latitude_radians)
        * math.cos(destination_latitude_radians)
        * math.sin(longitude_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * math.asin(min(1.0, math.sqrt(haversine)))


def _coordinates_from_feature(
    feature: dict[str, Any], properties: dict[str, Any]
) -> tuple[float, float] | None:
    latitude = _valid_coordinate(properties.get("lat"), -90, 90)
    longitude = _valid_coordinate(properties.get("lon"), -180, 180)
    if latitude is not None and longitude is not None:
        return latitude, longitude

    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        return None
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    longitude = _valid_coordinate(coordinates[0], -180, 180)
    latitude = _valid_coordinate(coordinates[1], -90, 90)
    if latitude is None or longitude is None:
        return None
    return latitude, longitude


def _hotel_from_feature(
    feature: Any,
    center: PostcodeCenterResponse,
    *,
    require_postcode_match: bool,
    max_distance_meters: float | None = None,
) -> NearbyHotelResponse | None:
    if not isinstance(feature, dict):
        return None
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        return None
    place_id = _clean_text(properties.get("place_id"))
    hotel_postcode = _clean_text(properties.get("postcode"))
    coordinates = _coordinates_from_feature(feature, properties)
    if not place_id or coordinates is None:
        return None

    postcode_matches = (
        hotel_postcode.casefold() == center.postcode.casefold()
        if hotel_postcode
        else None
    )
    if require_postcode_match and postcode_matches is not True:
        return None

    latitude, longitude = coordinates
    distance = _haversine_meters(
        center.latitude,
        center.longitude,
        latitude,
        longitude,
    )
    if max_distance_meters is not None and distance > max_distance_meters:
        return None
    distance_meters = max(0, round(distance))
    return NearbyHotelResponse(
        place_id=place_id,
        name=_clean_text(properties.get("name")),
        formatted_address=_clean_text(properties.get("formatted")),
        city=_locality_from_result(properties),
        state=_clean_text(properties.get("state")),
        postcode=hotel_postcode,
        latitude=latitude,
        longitude=longitude,
        distance_meters=distance_meters,
        distance_miles=round(distance / METERS_PER_MILE, 2),
        inside_searched_postcode=postcode_matches,
    )


def _places_features(
    resolved: ResolvedPostcode,
    *,
    limit: int,
    filter_value: str,
) -> list[Any]:
    payload = _request_json(
        GEOAPIFY_PLACES_URL,
        {
            "categories": "accommodation.hotel",
            "filter": filter_value,
            "bias": (
                f"proximity:{resolved.center.longitude},{resolved.center.latitude}"
            ),
            "limit": limit,
            "lang": "en",
            "apiKey": _api_key(),
        },
    )
    features = payload.get("features")
    if not isinstance(features, list):
        raise GeoapifyProviderError("Geoapify returned an invalid response.")
    return features


def _normalized_hotels(
    features: list[Any],
    center: PostcodeCenterResponse,
    *,
    require_postcode_match: bool,
    max_distance_meters: float | None = None,
) -> list[NearbyHotelResponse]:
    hotels_by_identity: dict[str, NearbyHotelResponse] = {}
    for feature in features:
        hotel = _hotel_from_feature(
            feature,
            center,
            require_postcode_match=require_postcode_match,
            max_distance_meters=max_distance_meters,
        )
        if hotel is None:
            continue
        identity = (
            f"name:{hotel.name.casefold()}"
            if hotel.name
            else f"address:{(hotel.formatted_address or hotel.place_id).casefold()}"
        )
        existing = hotels_by_identity.get(identity)
        if existing is None or hotel.distance_meters < existing.distance_meters:
            hotels_by_identity[identity] = hotel

    return sorted(
        hotels_by_identity.values(),
        key=lambda hotel: (hotel.distance_meters, hotel.place_id),
    )


def search_hotels_by_postcode(
    postcode: str,
    limit: int = DEFAULT_HOTEL_LIMIT,
) -> NearbyHotelSearchResponse | None:
    """Return live hotels in a ZIP boundary or its nearest populated radius."""

    if not 1 <= limit <= MAX_HOTEL_LIMIT:
        raise ValueError(f"Hotel result limit must be between 1 and {MAX_HOTEL_LIMIT}.")

    resolved = lookup_postcode(postcode)
    if resolved is None:
        return None

    boundary_features = _places_features(
        resolved,
        limit=limit,
        filter_value=f"place:{resolved.place_id}",
    )
    hotels = _normalized_hotels(
        boundary_features,
        resolved.center,
        require_postcode_match=True,
    )
    if hotels:
        return NearbyHotelSearchResponse(
            query=resolved.center.postcode,
            count=len(hotels),
            center=resolved.center,
            results=hotels,
        )

    for radius_miles in FALLBACK_RADIUS_MILES:
        radius_meters = round(radius_miles * METERS_PER_MILE)
        radius_features = _places_features(
            resolved,
            limit=limit,
            filter_value=(
                "circle:"
                f"{resolved.center.longitude},{resolved.center.latitude},{radius_meters}"
            ),
        )
        hotels = _normalized_hotels(
            radius_features,
            resolved.center,
            require_postcode_match=False,
            max_distance_meters=radius_meters,
        )
        if hotels:
            return NearbyHotelSearchResponse(
                query=resolved.center.postcode,
                count=len(hotels),
                search_scope="expanded radius",
                search_radius_miles=radius_miles,
                center=resolved.center,
                results=hotels,
            )

    return NearbyHotelSearchResponse(
        query=resolved.center.postcode,
        count=0,
        search_scope="expanded radius",
        search_radius_miles=FALLBACK_RADIUS_MILES[-1],
        center=resolved.center,
        results=[],
    )
