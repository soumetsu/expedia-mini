# Expedia-Mini Design

## Purpose

Expedia-Mini is a browser application for searching fictional hotel stays and,
in a later part, managing bookings. It uses the supplied classroom dataset and
does not represent live inventory, real reservations, or real travelers.

## Responsibilities

### Frontend

The Vue 3 application in `frontend/` owns the browser interface. `src/App.vue`
owns the query, loading, results, count, empty, and error state and coordinates
each request. `HotelSearchForm.vue` owns the labeled input, blank-input
validation, trimming, Enter submission, and busy controls.
`HotelResultsTable.vue` renders the joined stays with semantic table markup, and
`services/api.js` isolates the fetch call and response-envelope checks from the
components.

The interface uses the Composition API with `<script setup>`. Its CSS is
intentionally functional: clear focus states, readable spacing and contrast,
and a horizontally scrollable table at narrow widths. Final branding, images,
and decorative design are deferred.

### FastAPI

FastAPI is the HTTP interface inside `backend/app/`. It owns route definitions,
input validation, Pydantic request and response contracts, HTTP status codes,
and generated API documentation. Application routes use the `/api` prefix.
`GET /api/health` reports service status, and
`GET /api/hotels/search?name=...` returns the hotel-name search response.

### Backend

The backend owns business rules and data access rather than leaving those
responsibilities in Vue components or route handlers. `csv_data.py` resolves,
loads, and validates the source files; `search.py` joins hotels to trips and
performs normalized matching; `models.py` defines the response contracts; and
`routes.py` maps those responsibilities to HTTP endpoints. The search result is
one flattened row per offered stay and includes calculated nights and estimated
stay price.

### CSV seed data

The files in `expedia-lite-data/` are the read-only source for Part 1. Paths must
be resolved from backend source locations, and CSV files must be read with
`utf-8-sig` encoding. Hotels join to trips through `hotel_id`; users and trips
join to bookings through `user_id` and `trip_id`. The dataset README and
relationship diagram are the authoritative data reference.

#### Verified Part 1 data profile

- Exact hotel path:
  `C:\Users\henry\Desktop\IST 402\assignment 1\expedia-lite-data\hotels.csv`
- Exact trip path:
  `C:\Users\henry\Desktop\IST 402\assignment 1\expedia-lite-data\trips.csv`
- Both files are valid UTF-8 with a byte-order mark and use comma delimiters.
- `hotels.csv` has 8 records and columns `hotel_id`, `hotel_name`, `city`,
  `state`, and `nightly_rate_usd`.
- `trips.csv` has 12 records and columns `trip_id`, `hotel_id`, `trip_name`,
  `check_in`, and `check_out`.
- IDs are preserved as text. Hotel IDs match `H` plus three digits; trip IDs
  match `T` plus three digits.
- Hotel and trip IDs are unique in their source files, and every trip references
  an existing hotel. H001, H002, H003, and H007 each have two trips.
- The frontend display fields are `hotel_id`, `hotel_name`, `city`, `state`,
  `nightly_rate_usd`, `trip_id`, `trip_name`, `check_in`, `check_out`, calculated
  `nights`, and calculated `estimated_stay_price_usd`.
- `Harbor Lantern Hotel` is the successful full-name fixture and joins to T001
  and T009. `No Such Expedia-Mini Hotel` is the verified no-result fixture.

### Future SQLite persistence

Part 2 may import the CSV records into SQLite once, when initializing an empty
database. After that import, SQLite becomes the durable source of application
state. Restarting the application must not overwrite changes, restore deleted
bookings, or duplicate seed records. Python's standard-library `sqlite3`
support must be checked before considering an additional database dependency.

## Implemented Part 1 data flow

1. The user submits all or part of a hotel name through
   `HotelSearchForm.vue`. The component trims the value and rejects a blank
   submission in the browser.
2. `App.vue` clears stale result/error state, exposes a loading state, and calls
   `searchHotels()` in `services/api.js`.
3. The service encodes the query with `URLSearchParams` and requests
   `/api/hotels/search`. Vite proxies `/api` to `http://127.0.0.1:8000` in local
   development.
4. FastAPI validates the query, and the backend reads and joins the supplied
   CSV records by `hotel_id`.
5. FastAPI returns the stable `query`, `count`, and `results` envelope.
6. `App.vue` distinguishes an empty success from a request failure and passes
   successful rows to `HotelResultsTable.vue`.

The browser never reads the CSV files directly. The frontend retains each
complete response row in state while displaying hotel name, city/state, stay ID
and name, dates, nights, nightly rate, and estimated price.

## Current boundary

The Part 1 FastAPI CSV hotel-name search, its backend tests, and the barebones
Vue search interface are implemented. Booking management, SQLite persistence,
final visual design, and application image selection are not implemented.
Authentication, payments, flights, taxes, and live availability remain outside
the supplied data model.
