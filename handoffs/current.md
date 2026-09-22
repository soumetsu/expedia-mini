# Current Handoff

## Handoff status

- Last updated: `2026-09-22 02:27 EDT`
- Claims last verified: `2026-09-22 02:27 EDT`
- Update trigger: Committed and pushed the demo account registration/login and
  per-user SQLite search-history milestone.

## Objective

Extend the completed SQLite/MVC milestone with demo authentication and isolated
search history while preserving the existing search and booking workflows.
Production identity management and recommendation personalization remain later
enhancements.

## Git publication state

- Current branch: `main`.
- Upstream: `origin/main` at `https://github.com/soumetsu/expedia-mini.git`.
- The clear-selection and authentication/search-history changes were committed
  as `ce71752` (`Add demo authentication and per-user search history`) and
  pushed successfully to `origin/main`.
- `HEAD` and `origin/main` both resolve to `ce71752`; no merge was required.
- The working tree was clean immediately after the push; this handoff update
  is the only follow-up publication record.

## Current state

- The intended interpreter is `backend/.venv/Scripts/python.exe`, Python
  3.13.15 with standard-library SQLite 3.50.4. No package was installed.
- FastAPI initializes `backend/data/expedia_mini.db` during application startup.
  The file is generated and ignored by Git.
- `controllers/seed.py` reads all four UTF-8-with-BOM CSV files only when the
  database has no seed marker. It creates typed seed models and validates
  unique IDs, dates, rates, statuses, and all foreign references.
- `controllers/database.py` is the only application SQLite access layer. It
  owns the schema, foreign keys, indexes, idempotent seed, joined catalog reads,
  account credentials, per-user search history, and booking
  create/read/cancel/delete transactions.
- `controllers/security.py` hashes and verifies passwords with salted PBKDF2;
  `controllers/auth.py` issues process-local bearer tokens for demo sessions.
- `controllers/catalog.py` receives typed SQLite stay rows from the database
  controller and applies search/date/recommendation business rules.
- `models/entities.py` defines Hotel, Trip, User, Booking, and SeedData.
  `models/schemas.py` defines the Pydantic HTTP contracts.
- `routes.py` is a thin `/api` adapter with validation and safe error mapping.
- All application reads and writes use SQLite after seeding. Search and
  recommendations no longer read CSV files during requests.
- Existing H/T/U/B IDs are preserved. New bookings receive the next available
  B### ID, so records can grow beyond the six examples.
- The Vue tree is the MVC View. It calls FastAPI through `services/api.js` and
  never accesses CSV or SQLite directly.
- Booking create, history/read, cancel while retaining, and test-record delete
  remain available in the frontend. Seed bookings remain protected from delete.
- The search form has a compact **Clear selections** action. It clears the
  active destination, optional dates, visible search results, and transient
  booking feedback without deleting persisted booking-history records.
- Separate Vue sign-in, create-account, and search-history pages are available.
  Account creation enforces unique usernames, optional unique valid emails, and
  minimum eight-character passwords. Authenticated searches are recorded in
  SQLite and history is filtered by the current user token.
- The supplied CSV files were not modified.

## MVC fit decision

The requested structure fits conceptually but was adapted to the existing
FastAPI package. The implementation uses `backend/app/models/` and
`backend/app/controllers/`, not top-level `backend/models/` and
`backend/controllers/`. This keeps importable application modules together
without weakening the Model/View/Controller boundaries. These rules are now
recorded in `AGENTS.md`.

## Verification

- Required pre-modification baseline: 23 backend tests passed; frontend build
  passed with 16 modules.
- Focused refactor suite: 25 tests passed.
- Final backend suite after removing superseded flat modules: 25 tests passed.
- Final frontend production build: 16 modules transformed successfully.
- Fresh temporary database counts: 8 hotels, 12 trips, 6 users, 6 bookings;
  no broken trip/hotel or booking/user/trip references.
- The new regression test edits a temporary post-seed SQLite hotel and proves
  search returns the edited value, guarding against runtime CSV fallback.
- Live API after restart: health `ok`; Boston returned T001, T002, T009, T010.
- Final Vite-proxied checks: frontend HTTP 200, health `ok`, Boston count 4,
  six demo users, and zero remaining U006 test bookings.
- Latest frontend production build: Vite transformed 16 modules successfully
  after the clear-selection UI change.
- Latest frontend production build after account pages: Vite transformed 19
  modules successfully.
- Full backend suite after auth changes: 29 tests passed, including four new
  auth/history tests for hashed credentials, duplicate validation, email
  validation, and two-user history isolation.
- Live auth/browser check: migrated `demo_u001` signed in, `/auth/me` returned
  the same identity, a Boston search appeared on `/search-history`, and the
  registration page exposed the account fields. The synthetic history row was
  removed afterward.
- Browser smoke check: submitted a Boston search, activated **Clear
  selections**, and confirmed both date fields and the location were empty,
  the four result cards and transient state were cleared, and recommended
  stays remained.
- Live CRUD smoke test created B007 for U006/T011, read it, cancelled it while
  retaining one row, deleted that exact temporary record, and confirmed U006
  history returned to zero rows.
- `git diff --check` passed after code and documentation changes.
- No frontend lint or automated frontend test script is configured.

## Running services

- FastAPI session `70669`, process `31620`, URL `http://127.0.0.1:8000`
- Vite session `57149`, process `27812`, URL `http://127.0.0.1:5173/`

These are timestamped process claims; verify reachability before reusing them.

## Files changed for this milestone

- Added `backend/app/models/` and `backend/app/controllers/` packages.
- Removed superseded `backend/app/models.py`, `database.py`, `search.py`, and
  `csv_data.py` flat modules.
- Updated `backend/app/main.py` and `routes.py` for startup initialization and
  controller contracts.
- Updated the backend tests for four-file models, SQLite catalog reads, CRUD,
  and route behavior.
- Updated `AGENTS.md`, `README.md`, `report.md`, `docs/design.md`,
  `docs/verification.md`, Prompt 05 follow-on status, and this handoff.
- Updated the implemented behavior in `README.md`, the integrated smoke steps
  in `docs/verification.md`, and the maintenance note in Prompt 04.
- Added authentication/search-history controllers, contracts, Vue pages,
  focused tests, and `prompts/06-demo-authentication-and-search-history.md`.

## Remaining limitations

- Search dates filter fixed supplied trips; there is no arbitrary inventory.
- The application exposes full CRUD for bookings, not administrative CRUD
  screens for hotels, trips, or users.
- Recommendations do not yet re-rank using recent searches.
- Sessions are process-local demo bearer tokens; production identity,
  persistent sessions, password reset, and account deletion are not implemented.
- No rooms, occupancy, amenities, reviews, taxes, payments, flights, cars,
  packages, live demand, or dynamic pricing are represented by the data.
- The clear-selection and authentication/search-history changes are published
  on `origin/main` at `ce71752`.

## Exact next action

The next product enhancement is transparent, deterministic recommendation
ranking informed by the stored search history.
