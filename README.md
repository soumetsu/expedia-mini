# Expedia-Mini

Expedia-Mini is a small full-stack travel application with live ZIP-based hotel
discovery plus a clearly separated fictional booking exercise. FastAPI proxies
Geoapify Geocoding and Places requests, Vue renders the connected results and
Leaflet map, and SQLite preserves the supplied classroom booking data.

## Project layout

```text
.
|-- backend/              FastAPI application
|   |-- app/
|   |   |-- controllers/
|   |   |   |-- catalog.py
|   |   |   |-- database.py
|   |   |   `-- seed.py
|   |   |-- models/
|   |   |   |-- entities.py
|   |   |   `-- schemas.py
|   |   |-- main.py
|   |   `-- routes.py
|   |-- tests/            Backend unittest suite
|   `-- requirements.txt
|-- frontend/             Vue 3 application powered by Vite
|   |-- src/
|   |   |-- components/
|   |   |   |-- HotelResultsTable.vue
|   |   |   |-- HotelSearchForm.vue
|   |   |   |-- HotelMap.vue
|   |   |   |-- NearbyHotelList.vue
|   |   |   `-- RecommendedStays.vue
|   |   |-- services/
|   |   |   `-- api.js
|   |   |-- pages/
|   |   |   |-- BookingHistoryPage.vue
|   |   |   `-- SearchPage.vue
|   |   |-- App.vue
|   |   |-- main.js
|   |   `-- style.css
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js
|-- docs/
|   |-- screenshots/part1/ Part 1 browser evidence
|   |-- design.md
|   `-- verification.md
|-- prompts/
|   |-- 01-project-setup-and-development.md
|   |-- 02-complete-project-local-environments.md
|   |-- 03-part-1-backend-csv-search.md
|   |-- 04-part-1-frontend-csv-search.md
|   |-- 05-sqlite-persistence-preflight.md
|   `-- hotel-assistant.md
|-- handoffs/
|   |-- create-handoff.md
|   `-- current.md
|-- expedia-lite-data/    Supplied fictional CSV data
|-- AGENTS.md             Project working rules
`-- report.md             Part 1 submission report
```

`handoffs/current.md` is the maintained continuation snapshot for a new task.

## Verified local environment

- Python 3.13.15 in `backend/.venv/`
- Python standard-library `sqlite3` backed by SQLite 3.50.4
- FastAPI 0.141.1 and Uvicorn 0.52.4
- Node.js v24.20.0 and npm 11.19.0
- Vue 3.5.42, Leaflet 1.9.4, Vite 7.3.6, and `@vitejs/plugin-vue` 6.0.8 in
  `frontend/node_modules/`

Do not reinstall a working environment. Agents must obtain explicit approval
before every download or installation; see `AGENTS.md`.

## SQLite persistence

The intended interpreter at `backend/.venv/Scripts/python.exe` imports
Python's standard-library `sqlite3` module successfully. On September 17,
2026, a temporary on-disk database was created, written and committed, closed,
reopened, and read back successfully with SQLite 3.50.4. The temporary database
was removed after the check, and `pip check` reported no broken requirements.

No SQLite package was downloaded or installed because support is already
available. The application now creates `backend/data/expedia_mini.db` on the
backend startup, creates its schema, and imports the supplied
hotel, trip, user, and booking rows exactly once. Demo-user and booking reads
and writes use SQLite, as do hotel search and recommendations. CSV access is
limited to the initial seed of an uninitialized database. Restarting does not
restore deleted rows or duplicate seeds. The generated database remains
excluded from Git. See
`prompts/05-sqlite-persistence-preflight.md` for the original decision gate.

The schema also includes an additive Assignment 2 storage foundation for live
API hotels. `saved_hotels.hotel_id` stores the provider's `place_id` exactly as
a primary key; API `name`, `formatted_address`, `latitude`, and `longitude` map
to `name`, `address`, `latitude`, and `longitude`. `demo_hotel_nights` uses
`(hotel_id, stay_date)` as its primary key and references `saved_hotels`.
Its default $100.00 nightly rate and 20-room count are explicitly fictional
classroom values, not Geoapify data. `saved_hotel_zips` separately records
the searched ZIP, ZIP center, provider locality/postcode, distance, and search
scope needed to reconstruct the existing list and map without changing the
provider response contract. Startup migrates the earlier
`saved_hotel_locations` name without dropping saved rows. Conversation messages
and labeled SQL workflow traces are stored separately from the model's
read-only hotel query connection.

## Run the backend

From the project root:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The project-local environment and requirements are already installed in this
workspace.

## Backend environment configuration

The backend configuration helper at `backend/app/config.py` loads the
project-root `.env` file at `.env` and reads `GEOAPIFY_API_KEY` and
`GEMINI_API_KEY`. Both credentials remain backend-only. The health endpoint
reports only whether the Geoapify setting is configured; it never returns a key
value. Restart the backend process after editing `.env` so new settings load.
The hotel assistant uses `gemini-3.5-flash-lite` as its primary model and
`gemini-3.1-flash-lite` only as a labeled availability fallback after exhausted
primary 5xx/network attempts. Backend startup loads its versioned instructions
from `prompts/hotel-assistant.md`; restart the backend after editing that prompt.

## Run and build the frontend

In a second terminal:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Build the production bundle with:

```powershell
cd frontend
npm run build
```

The verified Windows shell does not currently discover `npm` through normal
command lookup. On that machine, use the already-installed executable directly:

```powershell
& 'C:\Users\henry\AppData\Local\Programs\node-v24.20.0-win-x64\npm.cmd' run dev -- --host 127.0.0.1 --port 5173
```

The frontend uses the same-origin `/api` path. During development, Vite proxies
it to `http://127.0.0.1:8000`, so no frontend environment variable is required
for the verified local setup.

## Implemented behavior

The backend keeps the supplied CSV files unchanged, validates their
relationships, seeds SQLite from all four CSV files, and provides:

- `GET /api/health`
- `POST /api/chat`
- `GET /api/hotels/nearby?postcode=<ZIP>&limit=<1–50>`
- `GET /api/saved-hotels?postcode=<ZIP>`
- `POST /api/saved-hotels`
- `DELETE /api/saved-hotels/{provider hotel ID}`
- `GET /api/hotels/search?name=<city, state, or hotel name>&check_in=<date>&check_out=<date>`
- `GET /api/hotels/recommended?limit=<1–6>`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me` and `POST /api/auth/logout`
- `GET /api/search-history` (signed-in account only)
- `GET /api/users`
- `GET /api/bookings?user_id=<user ID>`
- `POST /api/bookings`
- `PATCH /api/bookings/{booking_id}/cancel`
- `DELETE /api/bookings/{booking_id}`

The fixed bottom-right **Support / Chatbot** control opens a compact conversation
panel on desktop and can be expanded to occupy most of the viewport. Vue sends
the current message, bounded history, and an opaque conversation ID to
`POST /api/chat`; it never receives the Gemini key. For a saved-hotel question,
Gemini first proposes one SQL `SELECT` using the prompt's real schema. The
backend rejects multiple statements, writes, unapproved tables/functions, and
slow queries, opens SQLite read-only, and caps returned rows. A second Gemini
request receives the original question plus checked SQL and retrieved rows and
returns a grounded answer. The frontend labels this path, exposes the checked
SQL and records, and distinguishes it from support-only responses. Rates and
availability remain simulated course data. Pending, provider-error, restore,
close, keyboard, narrow-screen, model, and combined token-usage states remain
visible. Each Gemini stage makes at most three primary-model attempts for
transient timeouts, 429 responses, and selected 5xx responses. Exhausted
5xx/network availability failures receive at most two attempts on the fallback;
authentication and 429 failures do not switch models. Delays use capped
exponential backoff with jitter and honor a bounded provider `Retry-After`
value. The response identifies every model actually used, while permanent
errors remain sanitized instead of being exposed to the browser.

Search trims whitespace, ignores capitalization, and matches partial hotel
names, cities, states, and combined city/state labels. Optional dates narrow
the fixed-date catalog; they do not imply arbitrary availability. Search
returns one joined row per available stay with dates, calculated nights, and
estimated price. Blank input and invalid date windows are rejected.

The primary search accepts exactly one five-digit U.S. ZIP code. FastAPI first
resolves the postcode and its Geoapify `place_id`, then requests
`accommodation.hotel` places using the postcode boundary and a proximity bias.
It defensively keeps only places whose returned postcode matches the request,
deduplicates provider records by normalized hotel name, and calculates
straight-line distance from the ZIP reference center. When that exact-boundary
pass is empty, FastAPI searches live Geoapify Places circles at 5, 15, and 30
miles, stopping at the first populated radius. Circle results are defensively
distance-checked and identify whether their provider postcode matches the
query. Unresolved ZIPs, valid searches with no hotels through 30 miles, missing
configuration, and provider failures remain distinct outcomes. The former
`/api/demo/zip-location` placeholder is removed.

The Vue search bar no longer calls the fictional SQLite catalog. It renders
live hotel cards next to a Leaflet map using OpenStreetMap imagery and required
attribution. Cards and markers share Geoapify `place_id` selection state, so
selecting either identifies and reveals the same hotel in the other view.
Provider text is rendered safely, and missing values receive honest unavailable
labels. Expanded results identify the applied radius and label adjacent or
missing provider postcodes. Distance text says **Nearby**, **Far**, or **Very
far** and uses blue, orange, or red at the 5- and 15-mile thresholds. The page
lists Geoapify Places as the live hotel source, Geoapify Geocoding as the ZIP
source, and OpenStreetMap as the imagery source. Live results never infer
prices, ratings, reviews, room availability, or booking status.

ZIP lookup is local-first. Vue first requests saved provider hotels associated
with the entered ZIP. When that read succeeds with saved matches, it shows only
that explicitly labeled local subset using the stored ZIP center and result
context; it never describes the subset as a complete area inventory. Each
local card shows the October 10–14, 2026 simulated nightly rows. Only a
successful empty local response triggers the unchanged live
`/api/hotels/nearby` request. A local-storage error stops the search instead of
silently falling through to the provider.

Live API cards expose **Add to Local**. A successful save inserts the provider
hotel once, adds its ZIP association, and inserts missing demo-night rows with
the fictional $100.00 and 20-room defaults. Repeated saves do not overwrite
nightly edits. Saved cards expose **Remove from Local**, which transactionally
deletes that provider hotel, all of its ZIP associations, and its demo nights
without affecting other hotels or the Assignment 1 tables. Saved status is
loaded from SQLite by provider ID after each search, including after refresh.

Each live result also provides an **Open address in Google Maps** link in a new
tab. The link uses Google's keyless Maps URL search format with the exact
Geoapify-formatted address; if Geoapify omits the address, it uses the returned
latitude and longitude instead. Google controls the final search match, so the
link is navigation assistance rather than confirmation of hotel identity,
availability, or booking status.

The live search form includes a compact **Clear ZIP** control. A separate,
explicitly fictional catalog remains below it so booking create/read/cancel/
delete continues to be available through the frontend. Seed bookings remain
protected from deletion.

The account pages provide sign-in and account creation. Usernames are unique,
passwords are stored as salted PBKDF2 hashes, and an email is optional but must
match a normal address shape and be unique when supplied. The six legacy demo
travelers receive deterministic demo usernames (`demo_u001` through
`demo_u006`) and passwords (`Demo-U001-Pass!` through `Demo-U006-Pass!`) so
their seeded booking history remains testable. New accounts receive collision-
free user IDs.

Signed-in searches are recorded in SQLite and shown on the separate **Search
history** page. History is filtered by the authenticated user, so switching
accounts never exposes another user's searches. Search remains usable without
sign-in, but those guest searches are not persisted.

`App.vue` owns the shared shell, URL-backed page navigation, and the short-lived
demo session. `LoginPage.vue`, `RegisterPage.vue`, and `SearchHistoryPage.vue`
own account and activity views. `SearchPage.vue` and `BookingHistoryPage.vue`
own page state. `HotelSearchForm.vue` owns five-digit ZIP validation,
`NearbyHotelList.vue` owns live result cards, `HotelMap.vue` owns Leaflet
lifecycle and markers, and `services/api.js` owns HTTP requests and response
checks. `RecommendedStays.vue` now presents the separate fictional booking
sandbox. The responsive live-search treatment uses a distinct blue/cyan panel
while retaining the established navy palette.

## Current product objective

The live hotel-search milestone is implemented: a five-digit ZIP travels
through FastAPI to Geoapify Geocoding and Places, and Vue presents factual
hotels in a synchronized list and Leaflet map. The backend key remains in the
ignored project-root `.env`; it is never copied into frontend configuration or
returned to the browser. OpenStreetMap tiles require no client credential.

The current interface milestone is implemented: the responsive application has
location and optional fixed-date search, revamped stay cards above transparent
catalog recommendations, simulated booking, and a separate booking-history
page. A demo user can create a booking, read it in history, cancel it while
retaining the record, and delete a user-created test booking. Every action is
initiated in Vue and sent through FastAPI to SQLite.

The account milestone is also implemented: users can register and sign in,
maintain a process-local demo session, and review search history isolated to
their account. Guest search remains available without persistence.

Recommendations select one stay per hotel by lowest estimated total, then lower
nightly rate, earlier check-in date, and `trip_id`. Personalization based on
recent searches remains future work.

### Feature fit with the current data

| Interface idea | Data fit | Planned treatment |
| --- | --- | --- |
| Live ZIP hotel discovery | Supported by Geoapify postcode and Places responses | Implemented through FastAPI with exact filtering followed by live 5/15/30-mile fallback radii |
| Connected list and map | Supported by returned place IDs and coordinates | Implemented with Leaflet and shared selection state |
| Hotel or destination search | Supported by hotel name, city, and state | Implemented without implying live availability |
| Check-in/check-out controls | Partially supported by fixed trip dates | Filter or select offered stays; do not imply arbitrary-date inventory |
| Price comparison | Supported by nightly rate, dates, and derived stay total | Implemented with nightly and estimated total prices |
| Recommended stay | Supported with limited factual criteria | Implemented with a deterministic rule and visible explanation |
| Demo user and booking history | Supported by users, trips, and bookings | Implemented with empty, confirmed, and cancelled states |
| Booking CRUD | Supported by SQLite persistence | Implemented through Vue, FastAPI, and the database controller |
| Travelers, rooms, multi-hotel, bundles, flights, cars, or cruises | Not supported | Omit unless the data model is deliberately expanded later |
| Taxes, fees, amenities, reviews, weather, crowds, or live demand | Not supported | Do not display or infer these values |

## Implemented persistence and architecture

The supplied hotel, trip, user, and booking records seed SQLite once. The seed
is an initial state, not a fixed limit: users can add new bookings, and later
application reads and writes use SQLite without re-importing over changes.
Existing IDs stay unchanged and new records receive collision-free IDs.

The implementation follows clear MVC responsibilities:

- **Model:** `backend/app/models/` contains typed Hotel, Trip, User, and Booking
  entities plus Pydantic request/response contracts. Trip references Hotel;
  Booking references User and Trip;
- **View:** `frontend/src/` contains Vue pages, components, API client, and CSS
  for search, recommendations, booking actions, history, status, and feedback;
  and
- **Controller:** thin FastAPI routes call `controllers/catalog.py` for search
  rules and `controllers/database.py` for SQLite access, reference enforcement,
  and create/read/update/delete operations.

Dynamic-pricing logic remains lower priority. Authentication is intentionally a
demo session layer: tokens are process-local and expire when the backend
restarts; it is not production identity management. Any future pricing demonstration should use
disclosed, travel-relevant inputs such as an explicit holiday calendar; battery
level or device type must not affect price.

## Verification

Run the backend suite from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Run the configured frontend production build from `frontend/`:

```powershell
npm run build
```

No frontend lint or test script is currently configured. Follow
`docs/verification.md` for the integrated API and browser procedure.

## Local URLs

- Frontend: `http://127.0.0.1:5173/`
- Booking history: `http://127.0.0.1:5173/bookings`
- Backend health: `http://127.0.0.1:8000/api/health`
- Backend documentation: `http://127.0.0.1:8000/docs`
- Example location search:
  `http://127.0.0.1:8000/api/hotels/search?name=Boston`
- Live ZIP hotel search:
  `http://127.0.0.1:8000/api/hotels/nearby?postcode=10036&limit=20`
- Recommended stays:
  `http://127.0.0.1:8000/api/hotels/recommended?limit=3`
- Demo users: `http://127.0.0.1:8000/api/users`
- Sign in: `http://127.0.0.1:5173/login`
- Create account: `http://127.0.0.1:5173/register`
- Search history: `http://127.0.0.1:5173/search-history`

## Current boundary

Official Prompts 01–04 cover setup, project-local environments, the Part 1 CSV
API, and the initial Vue integration. Prompt 05 records that the project
interpreter is ready for SQLite without installation. SQLite schema creation,
one-time CSV seeding, date filtering, and booking CRUD are now implemented.
The main browser search no longer queries fictional CSV/SQLite hotel names,
cities, or states. The legacy catalog endpoint remains available for the
separate simulated booking exercise and regression coverage.
Production-grade authentication, dynamic pricing, payments, flights, taxes,
live availability, and personalized hotel recommendations based on prior
searches remain future work. Demo authentication and per-user search history
are now implemented. See
`expedia-lite-data/README.md` for the authoritative data dictionary.

## Working across tasks

Use the numbered files in `prompts/` as the official task record. Before
continuing in another task, verify and refresh `handoffs/current.md` with the
current objective, completed work, evidence, blockers, and one exact next
action. Keep durable decisions in `README.md`, `report.md`, `AGENTS.md`, or
`docs/`, not only in a handoff.
