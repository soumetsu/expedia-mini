"""Hotel and trip joining plus hotel-name search behavior."""

from __future__ import annotations

from .csv_data import TravelCatalog
from .models import HotelSearchResponse, HotelStayResponse


def search_hotel_stays(catalog: TravelCatalog, name: str) -> HotelSearchResponse:
    """Return every stay for hotels whose names contain the trimmed query."""

    query = name.strip()
    if not query:
        raise ValueError("Hotel name must not be blank.")

    normalized_query = query.casefold()
    matching_hotels = {
        hotel.hotel_id: hotel
        for hotel in catalog.hotels
        if normalized_query in hotel.hotel_name.casefold()
    }

    results: list[HotelStayResponse] = []
    for trip in catalog.trips:
        hotel = matching_hotels.get(trip.hotel_id)
        if hotel is None:
            continue
        nights = (trip.check_out - trip.check_in).days
        results.append(
            HotelStayResponse(
                hotel_id=hotel.hotel_id,
                hotel_name=hotel.hotel_name,
                city=hotel.city,
                state=hotel.state,
                nightly_rate_usd=hotel.nightly_rate_usd,
                trip_id=trip.trip_id,
                trip_name=trip.trip_name,
                check_in=trip.check_in,
                check_out=trip.check_out,
                nights=nights,
                estimated_stay_price_usd=hotel.nightly_rate_usd * nights,
            )
        )

    return HotelSearchResponse(query=query, count=len(results), results=results)
