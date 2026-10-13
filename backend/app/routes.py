"""Thin FastAPI HTTP adapters for Expedia-Mini controllers."""

from datetime import date
import re
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import geoapify_api_key_configured
from .controllers.auth import (
    login_account,
    logout_account,
    register_account,
    user_id_for_token,
)
from .controllers.chat import (
    ChatConfigurationError,
    ChatProviderError,
    request_support_reply,
)
from .controllers.catalog import recommend_hotel_stays, search_hotel_stays
from .controllers.geocoding import (
    DEFAULT_HOTEL_LIMIT,
    MAX_HOTEL_LIMIT,
    GeoapifyConfigurationError,
    GeoapifyProviderError,
    search_hotels_by_postcode,
)
from .controllers.database import (
    AccountConflictError,
    AuthenticationError,
    BookingConflictError,
    BookingNotFoundError,
    DataAccessError,
    SavedHotelNotFoundError,
    cancel_booking as cancel_booking_record,
    create_booking as create_booking_record,
    delete_saved_hotel as delete_saved_hotel_record,
    delete_booking as delete_booking_record,
    list_bookings as list_booking_records,
    list_search_history as list_search_history_records,
    list_saved_hotels as list_saved_hotel_records,
    list_users as list_user_records,
    record_search,
    save_api_hotel as save_api_hotel_record,
)
from .controllers.seed import SeedDataError
from .models import (
    BookingCreateRequest,
    BookingResponse,
    AuthResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    HotelSearchResponse,
    LoginRequest,
    NearbyHotelSearchResponse,
    RegisterRequest,
    SavedHotelCreateRequest,
    SavedHotelResponse,
    SavedHotelSearchResponse,
    SearchHistoryResponse,
    UserResponse,
)


router = APIRouter(prefix="/api")
optional_bearer = HTTPBearer(auto_error=False)


def _token_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if not isinstance(credentials, HTTPAuthorizationCredentials):
        return None
    return credentials.credentials


def _required_user_id(credentials: HTTPAuthorizationCredentials | None) -> str:
    try:
        return user_id_for_token(_token_from_credentials(credentials))
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    """Confirm that the backend is running."""

    key_status = (
        "key is configured"
        if geoapify_api_key_configured()
        else "key is not configured"
    )
    return HealthResponse(status="ok", geoapify_api_key_status=key_status)


@router.post("/chat", response_model=ChatResponse, tags=["support"])
async def support_chat(payload: ChatRequest) -> ChatResponse:
    """Return a backend-mediated Gemini support response."""

    try:
        return request_support_reply(payload)
    except ChatConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The support chatbot is not configured.",
        ) from exc
    except ChatProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The support chatbot could not provide a reply.",
        ) from exc
    except DataAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The support chatbot could not access its local records.",
        ) from exc


@router.post(
    "/auth/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
)
async def register(payload: RegisterRequest) -> AuthResponse:
    """Create an account and return a process-local demo session token."""

    try:
        token, user = register_account(payload.username, payload.password, payload.email)
        return AuthResponse(token=token, user=user)
    except AccountConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The account service is unavailable.",
        ) from exc


@router.post("/auth/login", response_model=AuthResponse, tags=["auth"])
async def login(payload: LoginRequest) -> AuthResponse:
    """Verify credentials and return a process-local demo session token."""

    try:
        token, user = login_account(payload.username, payload.password)
        return AuthResponse(token=token, user=user)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The account service is unavailable.",
        ) from exc


@router.get("/auth/me", response_model=AuthResponse, tags=["auth"])
async def current_account(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
) -> AuthResponse:
    """Return the identity represented by the current demo session."""

    user_id = _required_user_id(credentials)
    # The session controller intentionally keeps the public user object in the
    # token workflow; this endpoint is primarily a session validity check.
    try:
        from .controllers.database import get_auth_user

        user = get_auth_user(user_id)
        token = _token_from_credentials(credentials)
        assert token is not None
        return AuthResponse(token=token, user=user)
    except (AuthenticationError, LookupError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The account service is unavailable.",
        ) from exc


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["auth"])
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
) -> Response:
    logout_account(_token_from_credentials(credentials))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/hotels/nearby",
    response_model=NearbyHotelSearchResponse,
    tags=["hotels"],
)
async def nearby_hotels(
    postcode: Annotated[str, Query(min_length=5, max_length=5)],
    limit: Annotated[int, Query(ge=1, le=MAX_HOTEL_LIMIT)] = DEFAULT_HOTEL_LIMIT,
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
) -> NearbyHotelSearchResponse:
    """Return live Geoapify hotels inside or near one resolved U.S. ZIP."""

    requested_postcode = postcode.strip()
    if not re.fullmatch(r"\d{5}", requested_postcode):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Enter a valid 5-digit U.S. ZIP code.",
        )

    try:
        user_id = None
        token = _token_from_credentials(credentials)
        if token:
            user_id = user_id_for_token(token)
        response = search_hotels_by_postcode(requested_postcode, limit)
        if response is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ZIP code {requested_postcode} could not be resolved.",
            )
        if user_id:
            record_search(user_id, requested_postcode, None, None, response.count)
        return response
    except HTTPException:
        raise
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except GeoapifyConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Live hotel search is not configured.",
        ) from exc
    except GeoapifyProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The live hotel provider request failed.",
        ) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search history could not be saved.",
        ) from exc


@router.get(
    "/saved-hotels",
    response_model=SavedHotelSearchResponse,
    tags=["hotels"],
)
async def saved_hotels(
    postcode: Annotated[str, Query(min_length=5, max_length=5)],
) -> SavedHotelSearchResponse:
    """Return locally saved provider hotels associated with one ZIP."""

    requested_postcode = postcode.strip()
    if not re.fullmatch(r"\d{5}", requested_postcode):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Enter a valid 5-digit U.S. ZIP code.",
        )
    try:
        return list_saved_hotel_records(requested_postcode)
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Local hotel storage is unavailable.",
        ) from exc


@router.post(
    "/saved-hotels",
    response_model=SavedHotelResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["hotels"],
)
async def save_hotel(payload: SavedHotelCreateRequest) -> SavedHotelResponse:
    """Save a provider hotel with its searched ZIP context and demo nights."""

    try:
        return save_api_hotel_record(payload)
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The hotel could not be saved locally.",
        ) from exc


@router.delete(
    "/saved-hotels/{hotel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["hotels"],
)
async def remove_saved_hotel(hotel_id: str) -> Response:
    """Delete one saved provider hotel and all of its local demo data."""

    try:
        delete_saved_hotel_record(hotel_id)
    except SavedHotelNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The saved hotel could not be removed.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/hotels/search",
    response_model=HotelSearchResponse,
    tags=["hotels"],
)
async def hotel_search(
    name: Annotated[
        str,
        Query(min_length=1, description="City, state, or full/partial hotel name"),
    ],
    check_in: date | None = None,
    check_out: date | None = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
) -> HotelSearchResponse:
    """Search destinations or hotel names and return every matching stay."""

    try:
        user_id = None
        token = _token_from_credentials(credentials)
        if token:
            user_id = user_id_for_token(token)
        return search_hotel_stays(name, check_in, check_out, user_id=user_id)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc


def _booking_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, BookingNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/users", response_model=list[UserResponse], tags=["bookings"])
async def demo_users() -> list[UserResponse]:
    """List demo travelers available to the simulated booking interface."""

    try:
        return list_user_records()
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc


@router.get(
    "/search-history",
    response_model=list[SearchHistoryResponse],
    tags=["auth"],
)
async def search_history(
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
) -> list[SearchHistoryResponse]:
    """Read search history for the signed-in account only."""

    user_id = _required_user_id(credentials)
    try:
        return list_search_history_records(user_id, limit)
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search history is unavailable.",
        ) from exc


@router.get("/bookings", response_model=list[BookingResponse], tags=["bookings"])
async def booking_history(
    user_id: Annotated[str, Query(min_length=1)],
) -> list[BookingResponse]:
    """Read booking history for one demo traveler."""

    try:
        return list_booking_records(user_id)
    except BookingNotFoundError as exc:
        raise _booking_http_error(exc) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc


@router.post(
    "/bookings",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["bookings"],
)
async def create_booking(payload: BookingCreateRequest) -> BookingResponse:
    """Create and persist a simulated booking."""

    try:
        return create_booking_record(payload.user_id, payload.trip_id)
    except (BookingNotFoundError, BookingConflictError) as exc:
        raise _booking_http_error(exc) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc


@router.patch(
    "/bookings/{booking_id}/cancel",
    response_model=BookingResponse,
    tags=["bookings"],
)
async def cancel_booking(booking_id: str) -> BookingResponse:
    """Cancel a booking while retaining it in history."""

    try:
        return cancel_booking_record(booking_id)
    except BookingNotFoundError as exc:
        raise _booking_http_error(exc) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc


@router.delete(
    "/bookings/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["bookings"],
)
async def delete_booking(booking_id: str) -> Response:
    """Delete a user-created test booking."""

    try:
        delete_booking_record(booking_id)
    except (BookingNotFoundError, BookingConflictError) as exc:
        raise _booking_http_error(exc) from exc
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/hotels/recommended",
    response_model=HotelSearchResponse,
    tags=["hotels"],
)
async def recommended_hotels(
    limit: Annotated[int, Query(ge=1, le=6)] = 3,
) -> HotelSearchResponse:
    """Return deterministic best-value stays from distinct hotels."""

    try:
        return recommend_hotel_stays(limit)
    except (DataAccessError, SeedDataError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Travel data is unavailable.",
        ) from exc
