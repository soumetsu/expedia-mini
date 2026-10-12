# Expedia-Mini Design

## Purpose

Expedia-Mini is a browser application for discovering live hotel places by U.S.
ZIP code and managing a separate simulated booking exercise. Live Geoapify
place records do not represent room inventory, prices, availability, or
reservations; the supplied fictional dataset remains the source for booking
practice only.

## Product experience

The implemented interface has a prominent five-digit ZIP search in a distinct
blue/cyan panel, scannable live hotel cards, and an interactive Leaflet map.
Selecting a card or marker updates the same `place_id` selection. Desktop uses a
two-column list/map layout; narrow screens place the map above the cards.
Loading, invalid input, unresolved ZIP, successful empty result, populated
result, and failed provider request remain separate states.

The fictional booking catalog is visibly separated below the live experience.
Create, history/read, cancellation, and test-record deletion remain available
from Vue without suggesting that a Geoapify hotel is bookable. Separate sign-in,
account creation, and per-user search-history pages provide a lightweight demo
identity layer.

The current files support hotel name, city/state, fixed check-in/check-out
dates, trip labels, nightly price, derived total price, demo users, and booking
status. This allows destination search, fixed-stay selection, price comparison,
booking history, and the simulated booking lifecycle. It does not support
arbitrary-date availability, rooms, occupancy, multi-hotel itineraries,
packages, transportation, amenities, reviews, taxes/fees, weather, crowds, or
live demand.

### Implemented recommendation rule

Recommendations remain factual and explainable. The backend ranks all stays by
lowest estimated total price, lower nightly rate, earlier check-in date, and
finally `trip_id`, then returns only the best-ranked stay from each hotel. The
frontend shows three recommendation cards and explains the selection basis.
User preferences or recent searches may later adjust ranking, but no hotel
description, amenity, review, crowd, or weather claim may be invented because
those fields do not exist.

## Responsibilities

### Frontend

The Vue 3 application in `frontend/` owns the browser interface. `src/App.vue`
owns the shared shell, demo-user state, short-lived auth session, and URL-backed
navigation.
`SearchPage.vue` coordinates search, recommendations, and creation;
`BookingHistoryPage.vue` coordinates history, cancellation, and deletion.
`LoginPage.vue` and `RegisterPage.vue` own account forms, while
`SearchHistoryPage.vue` renders the signed-in user's activity.
`HotelSearchForm.vue` owns the five-digit ZIP field, validation, Enter
submission, clear control, and busy state. `NearbyHotelList.vue` renders live
place cards and builds keyless Google Maps search links from provider addresses
or coordinates; `HotelMap.vue` owns Leaflet setup, OpenStreetMap attribution,
markers, safe text tooltips, map fitting, and selected-marker focus.
`RecommendedStays.vue` owns the explicitly fictional booking sandbox.
`services/api.js` isolates all HTTP requests and response checks from
presentation components and no longer exposes the old fictional-catalog search
to the primary page.

The interface uses the Composition API with `<script setup>`. Its CSS provides
clear focus states, readable spacing and contrast, responsive card stacking,
and decorative geometry without requiring a wide mobile table.

### FastAPI

FastAPI is the HTTP interface inside `backend/app/`. It owns route definitions,
input validation, Pydantic request and response contracts, HTTP status codes,
and generated API documentation. Application routes use the `/api` prefix.
`GET /api/health` reports service status, and
`GET /api/hotels/nearby?postcode=...&limit=...` returns live hotels inside a
resolved ZIP boundary. It maps invalid input to 422, unresolved ZIPs to 404,
missing configuration to 503, and provider failure to 502; a successful search
with no hotel matches remains HTTP 200 with an empty list.
`GET /api/hotels/search?name=...` returns location or hotel-name matches.
`GET /api/hotels/recommended?limit=...` returns deterministic best-value stays
from distinct hotels. `/api/users` and `/api/bookings` expose the demo traveler
and booking lifecycle, including `PATCH .../cancel` and protected deletion.
`/api/auth/register`, `/api/auth/login`, `/api/auth/me`, and
`/api/auth/logout` manage demo sessions; `/api/search-history` returns only the
current token's history.

### Backend

The backend owns business rules and data access rather than leaving those
responsibilities in Vue components or route handlers.
`models/entities.py` defines Hotel, Trip, User, Booking, and SeedData;
`models/schemas.py` defines the Pydantic HTTP contracts.
`controllers/seed.py` reads and validates the four CSV files only during first
initialization. `controllers/database.py` is the sole SQLite access layer and
owns schema creation, foreign keys, one-time seeding, joined reads,
transactions, account credentials, search-history records, and booking CRUD.
`controllers/auth.py` creates process-local bearer sessions while delegating
credential reads and writes to the database controller. `controllers/catalog.py`
applies search and recommendation rules to typed stays returned by the database
controller and records authenticated catalog searches.
`controllers/geocoding.py` performs both Geoapify steps using the configuration
helper and standard-library HTTP client. It resolves an exact U.S. postcode,
retains its `place_id` and reference coordinates, then requests
`accommodation.hotel` with a postcode-boundary filter and proximity bias. It
requires each returned hotel's own postcode to match the query, drops unusable
coordinates, deduplicates normalized hotel names, computes straight-line
distance with the Haversine formula, and sorts nearest first. When no exact
records remain, it queries live Geoapify circles of 5, 15, and 30 miles in
order, stopping at the first populated radius. Circle results do not require a
matching postcode, but are independently checked against the requested radius
and expose a true, false, or unavailable postcode relationship. It returns
`None` only for an unresolved ZIP and raises sanitized provider/configuration
errors for failed requests. The API key is sent only to Geoapify and never
returned to Vue.
`routes.py` is a thin HTTP adapter.

### CSV seed data

The files in `expedia-lite-data/` are read-only initial data. Paths are resolved
from backend source locations, and the seed loader reads CSV with `utf-8-sig`
encoding. Hotels join to trips through `hotel_id`; users and trips join to
bookings through `user_id` and `trip_id`. After the seed marker is written,
application requests do not reread the CSV files.

#### Verified seed data profile

- Repository-relative hotel path: `expedia-lite-data/hotels.csv`.
- Repository-relative trip path: `expedia-lite-data/trips.csv`.
- Both files are valid UTF-8 with a byte-order mark and use comma delimiters.
- `hotels.csv` has 8 records and columns `hotel_id`, `hotel_name`, `city`,
  `state`, and `nightly_rate_usd`.
- `trips.csv` has 12 records and columns `trip_id`, `hotel_id`, `trip_name`,
  `check_in`, and `check_out`.
- `users.csv` has 6 records and columns `user_id` and `display_name`.
- `bookings.csv` has 6 records and columns `booking_id`, `user_id`, `trip_id`,
  `booked_on`, and `status`.
- IDs are preserved as text. Hotel IDs match `H` plus three digits; trip IDs
  match `T` plus three digits.
- Hotel and trip IDs are unique in their source files, and every trip references
  an existing hotel. H001, H002, H003, and H007 each have two trips.
- The frontend display fields are `hotel_id`, `hotel_name`, `city`, `state`,
  `nightly_rate_usd`, `trip_id`, `trip_name`, `check_in`, `check_out`, calculated
  `nights`, and calculated `estimated_stay_price_usd`.
- `Harbor Lantern Hotel` is the successful full-name fixture and joins to T001
  and T009. `No Such Expedia-Mini Hotel` is the verified no-result fixture.

### Implemented SQLite persistence

The application imports the CSV records into SQLite once at backend startup
when the database has no seed marker. After that import, SQLite is the durable
source for hotels, trips, demo users, bookings, search, and recommendations.
Restarting does not overwrite changes, restore deleted bookings, or duplicate
seed records. The runtime database is generated under `backend/data/` and
excluded from Git.

The preflight completed on September 17, 2026. The intended project interpreter
(`backend/.venv/Scripts/python.exe`, Python 3.13.15) imports `sqlite3` and uses
SQLite 3.50.4. A temporary file-backed database retained a committed row after
the connection was closed and reopened, and the temporary file was then
removed. No package installation is needed.

`controllers/database.py` defines the path, foreign-key schema and constraints,
idempotent seed marker, transactions, joined reads, collision-free booking IDs,
and CRUD functions. All application reads and writes use SQLite after seeding.

An additive, repeatable schema migration creates `saved_hotels` and
`demo_hotel_nights` before the seed-marker check, so it applies to both existing
and fresh databases without reseeding or changing Assignment 1 records. The
live response mapping is `place_id` to `saved_hotels.hotel_id`,
`formatted_address` to `address`, and `name`, `latitude`, and `longitude` to
columns with the same names. Provider IDs use SQLite's default case-sensitive
text comparison and form the non-null primary key. Coordinates have database
range checks. Each fictional nightly row is keyed by `(hotel_id, stay_date)`,
references a saved provider hotel, and defaults to 10,000 cents and 20 rooms.
These defaults are classroom simulation data and are not supplied by Geoapify.
`saved_hotel_locations` keeps a separate provider-hotel/ZIP association plus
the stored ZIP center, provider locality/postcode, distance, and search scope.
The save controller uses insert-if-missing operations for the hotel,
association, and five October 10–14 demo nights, so retries neither duplicate
rows nor overwrite edited rates or availability. Removal explicitly deletes
the hotel's nights, associations, and provider record in one transaction.

The Vue orchestration is local-first: `GET /api/saved-hotels` must succeed
before the unchanged live endpoint can be called. Saved matches are adapted to
the existing `place_id`-based list and map contract, preserving card/marker
selection. An empty local result falls through to Geoapify; a local-storage
failure is shown to the user and blocks that fallback. Provider IDs returned
alongside a local lookup restore Add/Remove state after a page refresh.

## Implemented MVC and CRUD responsibilities

The supplied MVC references map to this client/server application as follows:

| Role | Expedia-Mini responsibility | Examples |
| --- | --- | --- |
| Model | Entity fields, validation contracts, stored records, and relationships | Hotel, Trip, User, and Booking; booking references a user and trip |
| View | Screens, components, layout, CSS, and user feedback | Search/results, recommendation, booking action, and history views |
| Controller | Request coordination, business rules, database access, validation, and CRUD | Validate references, assign a unique booking ID, create/read/cancel/delete a booking |

The proposed top-level `backend/models/` and `backend/controllers/` split fits
conceptually but not literally: this FastAPI project already uses the importable
`backend/app` package. The adopted structure is therefore
`backend/app/models/` and `backend/app/controllers/`. This preserves the MVC
boundaries without breaking application imports or placing backend modules
outside the configured package. FastAPI `routes.py` remains an HTTP adapter,
not a second data-access layer.

FastAPI routes are thin HTTP entry points. The focused database controller owns
SQL execution and transactions, while
Pydantic/domain models define contracts and Vue remains responsible for
presentation. “All CRUD through the frontend” means every user operation starts
in Vue and travels through FastAPI; it does not mean the browser accesses
SQLite directly.

The SQLite seed is initial data rather than a cap on records. Initialization
preserves existing IDs, adds seed records only once, and assigns collision-free
IDs to new bookings. Cancellation updates `status` to `cancelled` and retains
the history row; deletion is limited to user-created test bookings.

Demo authentication is implemented with unique usernames, optional unique
emails, PBKDF2 password hashes, and process-local bearer tokens. Search history
rows reference a user and are only returned for that authenticated user. A
production identity provider, durable sessions, password reset, and account
management remain out of scope. A later pricing demonstration may use a
disclosed holiday/date rule and show the base price and adjustment separately.
Battery state and device type are not acceptable pricing inputs because they are
unrelated to the stored travel model and would make pricing opaque and
inconsistent.

## Implemented live search, map, and booking data flow

1. The user submits a five-digit ZIP through `HotelSearchForm.vue`; invalid
   values are rejected before a request.
2. `services/api.js` requests `/api/hotels/nearby` through the Vite `/api`
   proxy and optionally includes the demo bearer token.
3. FastAPI validates the ZIP, resolves its Geoapify postcode record, then sends
   the boundary-constrained and proximity-biased Geoapify Places request.
4. The controller validates, exact-postcode filters, deduplicates, measures,
   and sorts those records. If none remain, it repeats the live Places search
   with 5-, 15-, then 30-mile circle filters and stops at the first usable set.
5. `SearchPage.vue` distinguishes unresolved, empty-success, and failed-request
   outcomes. It also presents the returned boundary/radius scope and names the
   live hotel, ZIP-center, and map-imagery sources. Successful records are
   passed to `NearbyHotelList.vue` and `HotelMap.vue`.
6. Both components read one `selectedPlaceId`. A card selection focuses its
   marker and safe tooltip; a marker selection highlights and scrolls/focuses
   its card.
7. Each result exposes a separate Google Maps link using the provider-formatted
   address, or its coordinates when the address is unavailable. The link opens
   a new tab without a Google API key; Google controls the resulting match.
8. If signed in, a successful ZIP search records the ZIP and result count in
   that user's SQLite search history.
9. The separate fictional catalog loads deterministic stays. “Create demo
   booking” posts the selected demo user and trip; `/bookings` retains the
   existing read/cancel/delete lifecycle.

The browser never receives the Geoapify backend key and never reads CSV or
SQLite directly. OpenStreetMap supplies browser-visible tiles without using the
backend credential. Expanded results label outside or unavailable postcodes,
and their distance labels use text plus blue/orange/red severity so color is not
the only distinction.

## Support chatbot flow

1. `ChatbotWidget.vue` owns the floating launcher, compact conversation view,
   optional expanded view, local history, pending state, and error feedback.
2. `services/api.js` posts a bounded message and conversation history to
   `/api/chat`; no provider credential is present in the browser request.
3. The thin FastAPI route validates `ChatRequest` and calls
   `controllers/chat.py`.
4. The controller sends the support instruction and conversation to the pinned
   `gemini-3.5-flash-lite` model with the backend-only `GEMINI_API_KEY` header.
5. FastAPI returns the reply, model name, and optional provider-reported token
   usage. The widget identifies the pinned model in its header and shows input,
   output, and total tokens below a successful reply. Provider and configuration
   failures become sanitized 502 and 503 responses.

The chatbot provides application help only. It does not query arbitrary SQL,
perform RAG, create bookings, or convert live hotel places into claims about
price, availability, ratings, reviews, amenities, or reservations. A single
retry covers transient provider-capacity failures; the frontend keeps a clear
retryable error when the provider remains unavailable.

## Current boundary

Live ZIP hotel discovery, the synchronized Leaflet list/map, legacy catalog
filtering, the separated booking sandbox, SQLite seeding, booking CRUD, demo
authentication, per-user search history, and backend-mediated Gemini support
chat are implemented. Provider coverage
can be incomplete, and results are capped per request. Prices, ratings, reviews,
room inventory, real booking, personalized ranking, production identity,
dynamic pricing, payments, flights, and taxes remain outside the live search.
