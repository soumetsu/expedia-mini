# Current Handoff

## Handoff status

- Last updated: `2026-09-21 23:48 EDT`
- Claims last verified: `2026-09-21 23:48 EDT`
- Update trigger: The reviewed frontend and SQLite/MVC work was committed and
  pushed to the current GitHub remote.

## Objective

Publish the completed SQLite/MVC milestone and responsive booking interface.
The next independent product enhancement is recent-search personalization.
Authentication and dynamic pricing remain lower priority and require a
separate request.

## Git publication state

- Current branch: `main`.
- Upstream: `origin/main` at `https://github.com/soumetsu/expedia-mini.git`.
- Before this request, `HEAD` matched `origin/main` at `6b69d75`; the frontend
  and SQLite/MVC work was uncommitted in the working tree.
- No merge was required because there was no divergent local branch. The
  implementation was committed as `a49e4a8` and pushed to `origin/main`.
- A documentation-only follow-up commit records this publication state.

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
  users, and booking create/read/cancel/delete transactions.
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
- Live CRUD smoke test created B007 for U006/T011, read it, cancelled it while
  retaining one row, deleted that exact temporary record, and confirmed U006
  history returned to zero rows.
- `git diff --check` passed after code and documentation changes.
- No frontend lint or automated frontend test script is configured.

## Running services

- FastAPI session `75432`, process `18116`, URL `http://127.0.0.1:8000`
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
- Earlier uncommitted frontend work remains in the shared working tree and must
  be preserved.

## Remaining limitations

- Search dates filter fixed supplied trips; there is no arbitrary inventory.
- The application exposes full CRUD for bookings, not administrative CRUD
  screens for hotels, trips, or users.
- Recommendations do not yet learn from recent searches.
- Demo users have no credentials; real authentication is not implemented.
- No rooms, occupancy, amenities, reviews, taxes, payments, flights, cars,
  packages, live demand, or dynamic pricing are represented by the data.
- The working tree is intentionally dirty and has not been committed.

## Exact next action

Add recent-search persistence and use it as a transparent, deterministic input
to personalized recommendation ranking without inventing unsupported fields.
