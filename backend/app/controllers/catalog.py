"""Catalog business rules operating on stays retrieved from SQLite."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ..models import HotelSearchResponse, HotelStayResponse
from .database import DATABASE_PATH, fetch_hotel_stays, record_search


def search_hotel_stays(
    name: str,
    check_in: date | None = None,
    check_out: date | None = None,
    database_path: Path = DATABASE_PATH,
    user_id: str | None = None,
) -> HotelSearchResponse:
    """Search SQLite-backed stays by destination or partial hotel name."""

    query = name.strip()
    if not query:
        raise ValueError("Search location must not be blank.")
    if check_in and check_out and check_out <= check_in:
        raise ValueError("Check-out must be after check-in.")

    normalized_query = query.casefold()
    results = [
        stay
        for stay in fetch_hotel_stays(database_path)
        if (
            normalized_query in stay.hotel_name.casefold()
            or normalized_query in stay.city.casefold()
            or normalized_query in stay.state.casefold()
            or normalized_query in f"{stay.city}, {stay.state}".casefold()
        )
        and (not check_in or stay.check_in >= check_in)
        and (not check_out or stay.check_out <= check_out)
    ]
    response = HotelSearchResponse(query=query, count=len(results), results=results)
    if user_id:
        record_search(user_id, query, check_in, check_out, response.count, database_path)
    return response


def recommend_hotel_stays(
    limit: int = 3,
    database_path: Path = DATABASE_PATH,
) -> HotelSearchResponse:
    """Rank SQLite-backed stays and keep one best-value trip per hotel."""

    if limit < 1:
        raise ValueError("Recommendation limit must be at least one.")

    ranked_stays: list[HotelStayResponse] = sorted(
        fetch_hotel_stays(database_path),
        key=lambda stay: (
            stay.estimated_stay_price_usd,
            stay.nightly_rate_usd,
            stay.check_in,
            stay.trip_id,
        ),
    )
    unique_hotels: list[HotelStayResponse] = []
    seen_hotel_ids: set[str] = set()
    for stay in ranked_stays:
        if stay.hotel_id in seen_hotel_ids:
            continue
        seen_hotel_ids.add(stay.hotel_id)
        unique_hotels.append(stay)
        if len(unique_hotels) == limit:
            break

    return HotelSearchResponse(
        query="Recommended stays",
        count=len(unique_hotels),
        results=unique_hotels,
    )
