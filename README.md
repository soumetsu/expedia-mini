# Expedia-Mini

Expedia-Mini is a small full-stack travel application for searching the
supplied hotel trips and managing simulated bookings. The project
uses a FastAPI backend, a Vue frontend, and the supplied fictional data in
`expedia-lite-data/`.

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
|   `-- 05-sqlite-persistence-preflight.md
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
- Vue 3.5.42, Vite 7.3.6, and `@vitejs/plugin-vue` 6.0.8 in
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

## Run the backend

From the project root:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The project-local environment and requirements are already installed in this
workspace.

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
- `GET /api/hotels/search?name=<city, state, or hotel name>&check_in=<date>&check_out=<date>`
- `GET /api/hotels/recommended?limit=<1–6>`
- `GET /api/users`
- `GET /api/bookings?user_id=<user ID>`
- `POST /api/bookings`
- `PATCH /api/bookings/{booking_id}/cancel`
- `DELETE /api/bookings/{booking_id}`

Search trims whitespace, ignores capitalization, and matches partial hotel
names, cities, states, and combined city/state labels. Optional dates narrow
the fixed-date catalog; they do not imply arbitrary availability. Search
returns one joined row per available stay with dates, calculated nights, and
estimated price. Blank input and invalid date windows are rejected.

The Vue interface uses a location-oriented primary search field with secondary
optional date and demo-traveler controls. Revamped result cards appear above
recommendations and include a booking action. A separate `/bookings` page reads
history, cancels by changing status while retaining the row, and offers a
two-step delete control for user-created test bookings. Seed bookings cannot be
deleted.

`App.vue` owns the shared shell and URL-backed page navigation. `SearchPage.vue`
and `BookingHistoryPage.vue` own page state, `HotelSearchForm.vue` owns
accessible form behavior, `HotelResultsTable.vue` owns result-card
presentation, and `services/api.js` owns HTTP requests and response checks.
`RecommendedStays.vue` presents three
distinct, deterministic best-value stays below the search panel. The responsive
visual design retains the navy/blue palette and uses orange only for the primary
search action.

## Current product objective

The current interface milestone is implemented: the responsive application has
location and optional fixed-date search, revamped stay cards above transparent
catalog recommendations, simulated booking, and a separate booking-history
page. A demo user can create a booking, read it in history, cancel it while
retaining the record, and delete a user-created test booking. Every action is
initiated in Vue and sent through FastAPI to SQLite.

Recommendations select one stay per hotel by lowest estimated total, then lower
nightly rate, earlier check-in date, and `trip_id`. Personalization based on
recent searches remains future work.

### Feature fit with the current data

| Interface idea | Data fit | Planned treatment |
| --- | --- | --- |
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

Demo authentication and dynamic-pricing logic are lower-priority ideas. The
current user records can support a transparent demo-user selector, not real
credential authentication. Any future pricing demonstration should use
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
- Recommended stays:
  `http://127.0.0.1:8000/api/hotels/recommended?limit=3`
- Demo users: `http://127.0.0.1:8000/api/users`

## Current boundary

Official Prompts 01–04 cover setup, project-local environments, the Part 1 CSV
API, and the initial Vue integration. Prompt 05 records that the project
interpreter is ready for SQLite without installation. SQLite schema creation,
one-time CSV seeding, date filtering, and booking CRUD are now implemented.
Authentication, dynamic pricing, payments, flights, taxes, live availability,
and personalized recommendations based on prior searches remain future work. See
`expedia-lite-data/README.md` for the authoritative data dictionary.

## Working across tasks

Use the numbered files in `prompts/` as the official task record. Before
continuing in another task, verify and refresh `handoffs/current.md` with the
current objective, completed work, evidence, blockers, and one exact next
action. Keep durable decisions in `README.md`, `report.md`, `AGENTS.md`, or
`docs/`, not only in a handoff.
