# Prompt 03 — Part 1 Backend CSV Search

## Goal

Build and verify the FastAPI backend for Part 1 of the travel application.

The backend must read the supplied `hotels.csv` and `trips.csv` files, connect
their records through `hotel_id`, and provide a hotel-name search API for the
future Vue frontend.

Complete the backend and its tests in this task. Do not begin frontend
development.

## Scope and authority

Treat the assignment description, course guide, and supplied data README as
reference requirements.

This prompt authorizes:

- inspecting the project and CSV data;
- creating or modifying backend source code;
- creating backend tests;
- running backend tests;
- briefly starting the backend for an API smoke check; and
- updating relevant project documentation.

This prompt does not authorize:

- Vue or other frontend development;
- SQLite or Part 2 functionality;
- users, bookings, booking history, or CRUD;
- reinstalling system-level Python, Node.js, or npm;
- unnecessary dependency additions;
- Git commits, pushes, merges, or submission; or
- changing or regenerating the supplied CSV files.

## Verified starting state

Prompts 01 and 02 completed the project setup and project-local environment
checkpoints.

The following are already verified:

- a compatible Python installation exists;
- the project-specific Python environment is ready;
- FastAPI and the required backend dependencies are available;
- Node.js and npm are installed;
- the frontend package environment is ready; and
- no backend or frontend feature development has started.

Do not repeat the full setup process or recreate working environments.

Before development, perform only a brief readiness check:

- identify the project-specific Python interpreter;
- confirm FastAPI imports from that interpreter;
- confirm the backend test runner is available; and
- confirm `hotels.csv` and `trips.csv` exist.

If these checks pass, begin implementation immediately.

If the actual environment conflicts with the verified Prompts 01 and 02 result,
report the exact conflict before changing dependencies. If an additional
dependency is genuinely required, explain its purpose and exact project-local
installation command, then stop for permission.

Never use `sudo`, request administrator access, or install packages globally.

## Read the project context

Before editing code, read:

- `AGENTS.md`
- `README.md`
- `report.md`
- `docs/design.md`
- `handoffs/current.md`
- `.gitignore`
- existing backend source and tests
- the README supplied with the CSV data
- `hotels.csv`
- `trips.csv`

Preserve useful existing work and follow the project-specific conventions in
`AGENTS.md`.

## Inspect the CSV data

Inspect `hotels.csv` and `trips.csv` before designing the API.

Determine and record:

- the exact path of each file;
- the text encoding and delimiters;
- the actual column names;
- record counts;
- the type and format of each ID;
- whether `hotel_id` is unique in `hotels.csv`;
- whether every trip references an existing `hotel_id`;
- whether one hotel can have multiple trips;
- the fields needed to display hotel and stay information;
- one real hotel name that can be used for a successful test; and
- one search value guaranteed to return no results.

Do not alter, normalize, or regenerate the supplied CSV files.

If a required CSV is missing, unreadable, or contains relationships that cannot
be interpreted safely, stop and report the evidence.

## Backend design

Keep backend application code under `backend/app/` and tests under the project's
established backend test location.

Use small modules grouped by responsibility. At minimum, separate:

- FastAPI application and route configuration;
- CSV loading and validation;
- hotel/trip joining and search behavior; and
- API response models when appropriate.

Use Python type hints for public functions and route handlers. Add concise
docstrings where they clarify behavior.

Resolve CSV paths from stable project or module locations. The backend must not
depend on whichever directory happens to be the terminal's current working
directory.

Prefer Python's standard CSV facilities unless an existing approved dependency
provides a clear project-specific benefit.

## Required API behavior

Implement these endpoints unless an existing documented backend convention
requires an equivalent path.

### Health endpoint

`GET /api/health`

Return a small JSON response confirming that the backend is running.

### Hotel search endpoint

`GET /api/hotels/search?name=<hotel name>`

The search must:

- trim leading and trailing whitespace;
- compare hotel names case-insensitively;
- support partial hotel-name matching;
- find matching hotels in `hotels.csv`;
- join their available stays from `trips.csv` through `hotel_id`;
- include all matching stays;
- preserve the supplied `hotel_id` and trip IDs; and
- return JSON that the Vue frontend can display without reading the CSV files
  itself.

Use a stable response structure similar to:

```json
{
  "query": "example",
  "count": 1,
  "results": [
    {
      "hotel_id": "supplied value",
      "hotel_name": "supplied value",
      "trip_id": "supplied value",
      "other_hotel_fields": "values from hotels.csv",
      "other_trip_fields": "values from trips.csv"
    }
  ]
}
```

## Completion record

Completed on September 11, 2026, without frontend, SQLite, booking, dependency,
Git, or supplied-data changes.

- Readiness passed with `backend/.venv/Scripts/python.exe`, Python 3.13.15,
  FastAPI 0.141.1, and standard-library `unittest`.
- The required UTF-8-with-BOM comma-delimited CSVs passed schema, count, unique
  ID, and relationship checks.
- Backend responsibilities were separated across `main.py`, `routes.py`,
  `models.py`, `csv_data.py`, and `search.py`.
- Twelve backend tests passed with `unittest`.
- A live Uvicorn smoke check returned HTTP 200 for health, a two-stay Harbor
  Lantern search, and a zero-result unknown-hotel search.
- Uvicorn was stopped cleanly after the smoke check.
