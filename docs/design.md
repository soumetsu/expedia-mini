# Expedia-Mini Design

## Purpose

Expedia-Mini is a browser application for searching fictional hotel stays and
managing simulated bookings. It uses the supplied fictional dataset and
does not represent live inventory, real reservations, or real travelers.

## Product experience

The implemented interface has a prominent location search area, secondary
fixed-date and demo-traveler controls, scannable stay cards above clearly
explained recommendations, and a separate booking-history page. It uses strong
hierarchy, an orange primary search action against the navy/blue palette,
compact mobile stacking, and explicit loading, empty, success, and error
feedback. Create, history/read, cancellation, and test-record deletion are all
available from the Vue interface.

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
owns the shared shell, demo-user state, and URL-backed navigation.
`SearchPage.vue` coordinates search, recommendations, and creation;
`BookingHistoryPage.vue` coordinates history, cancellation, and deletion.
`HotelSearchForm.vue` owns the primary location field, secondary date/user
controls, validation, Enter submission, and busy state. `RecommendedStays.vue`
owns best-value cards and the catalog-only personalization note.
`HotelResultsTable.vue` renders the revamped stay cards, and `services/api.js`
isolates all HTTP requests and response checks from presentation components.

The interface uses the Composition API with `<script setup>`. Its CSS provides
clear focus states, readable spacing and contrast, responsive card stacking,
and decorative geometry without requiring a wide mobile table.

### FastAPI

FastAPI is the HTTP interface inside `backend/app/`. It owns route definitions,
input validation, Pydantic request and response contracts, HTTP status codes,
and generated API documentation. Application routes use the `/api` prefix.
`GET /api/health` reports service status, and
`GET /api/hotels/search?name=...` returns location or hotel-name matches.
`GET /api/hotels/recommended?limit=...` returns deterministic best-value stays
from distinct hotels. `/api/users` and `/api/bookings` expose the demo traveler
and booking lifecycle, including `PATCH .../cancel` and protected deletion.

### Backend

The backend owns business rules and data access rather than leaving those
responsibilities in Vue components or route handlers.
`models/entities.py` defines Hotel, Trip, User, Booking, and SeedData;
`models/schemas.py` defines the Pydantic HTTP contracts.
`controllers/seed.py` reads and validates the four CSV files only during first
initialization. `controllers/database.py` is the sole SQLite access layer and
owns schema creation, foreign keys, one-time seeding, joined reads,
transactions, and booking CRUD. `controllers/catalog.py` applies search and
recommendation rules to typed stays returned by the database controller.
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

Demo authentication and dynamic pricing are deliberately lower priority. The
existing users can support a demo identity selector, but they contain no
credentials. A later pricing demonstration may use a disclosed holiday/date
rule and show the base price and adjustment separately. Battery state and
device type are not acceptable pricing inputs because they are unrelated to
the stored travel model and would make pricing opaque and inconsistent.

## Implemented search, recommendation, and booking data flow

1. When the search page mounts, `SearchPage.vue` calls
   `getRecommendedHotels()` and renders
   the returned distinct best-value stays through `RecommendedStays.vue`.
2. The user submits a city, state, or hotel name through
   `HotelSearchForm.vue`; the component trims the value and rejects a blank
   submission in the browser.
3. `SearchPage.vue` clears stale result/error state, exposes a loading state,
   and calls `searchHotels()` in `services/api.js` with optional date filters.
4. The service encodes the query with `URLSearchParams` and requests
   `/api/hotels/search`. Vite proxies `/api` to `http://127.0.0.1:8000` in local
   development.
5. FastAPI validates the query and optional window. The catalog controller gets
   joined hotel/trip models from SQLite and applies name/city/state/date rules.
6. FastAPI returns the stable `query`, `count`, and `results` envelope.
7. `SearchPage.vue` distinguishes an empty success from a request failure and
   passes successful rows to `HotelResultsTable.vue` above recommendations.
8. “Book this stay” posts the selected demo user and trip to FastAPI, where the
   database controller validates references, assigns an ID, and inserts it.
9. `/bookings` reads joined history for the selected demo user. Cancel sends a
   status-update request and retains the row; delete requires a two-step UI
   confirmation and is accepted only for a user-created test booking.

The browser never reads the CSV files directly. The frontend retains each
complete response row in state while displaying hotel name, city/state, stay ID
and name, dates, nights, nightly rate, and estimated price.

## Current boundary

The FastAPI search, city/state and date filtering, catalog recommendations,
responsive Vue pages, SQLite seeding, and booking CRUD are implemented.
Personalized recommendations based on prior searches, authentication, dynamic
pricing, payments, flights, taxes, and live availability remain outside the
current implementation.
