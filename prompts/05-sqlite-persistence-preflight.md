# Prompt 05 — SQLite Persistence Preflight

## Status

Completed on September 17, 2026. This is a readiness check, not authorization
to implement Part 2 persistence.

## Goal

Determine whether the intended project interpreter already supports SQLite,
avoid unnecessary installation, verify a real file-backed persistence
round-trip, and record the remaining setup gaps before application persistence
work begins.

## Scope and authority

This prompt authorizes reading the project instructions and data documentation,
running read-only environment and dependency checks, creating and removing one
temporary SQLite database for verification, and updating Markdown records with
observed evidence.

It does not authorize adding or upgrading packages, modifying source CSV files,
creating the application's runtime database, defining the production schema,
changing backend or frontend behavior, implementing bookings, or beginning any
other Part 2 feature.

## CHECK

Use the intended interpreter at `backend/.venv/Scripts/python.exe`. Report the
resolved executable, Python version, and SQLite library version. Do not infer
support from the system Python or from a package manifest.

Observed result:

- Executable:
  `C:\Users\henry\Desktop\IST 402\assignment 1\backend\.venv\Scripts\python.exe`
- Python: 3.13.15
- Standard-library `sqlite3` import: successful
- SQLite library: 3.50.4

## TAKE ACTION decision gate

SQLite support is present, so installation was skipped. No package was
downloaded, installed, or added to `backend/requirements.txt`.

If this check fails in a future environment, stop before installing anything.
Describe the exact missing capability, proposed item and source, purpose,
commands, expected project or system changes, network use, and elevation needs,
then obtain explicit user approval for that exact installation.

## VERIFY

The project interpreter created a temporary file-backed SQLite database,
created a table, inserted and committed one row, closed the connection,
reopened the same file, and read `(1, 'persisted')`. The temporary database was
then removed. `python -m pip check` reported `No broken requirements found.`

The repository already excludes `*.db`, `*.sqlite`, and `*.sqlite3` runtime
files from Git.

## Remaining setup gaps

The Python environment is ready, but the application persistence layer is not.
A separately authorized implementation still needs to define:

- the runtime database location and stable path resolution;
- tables, keys, constraints, and indexes for the supplied data model;
- idempotent initialization and a one-time CSV seed/import strategy;
- data-access and transaction boundaries;
- booking create, history, cancellation, and deletion behavior;
- tests proving that restarts preserve changes and do not duplicate or restore
  seed records.

The existing Part 1 API remains CSV-backed and no application behavior changed
during this preflight.

## Acceptance evidence

- Correct project interpreter selected: passed.
- `sqlite3` import and version check: passed with SQLite 3.50.4.
- File-backed close/reopen round-trip: passed.
- Temporary verification database removed: passed.
- Dependency integrity check: passed.
- Installation decision: skipped because support already exists.
- Application persistence implementation: intentionally not started.

## Follow-on implementation status

The scope above records the original September 17 preflight and remains an
accurate history of what that check authorized. A later explicit user request
on September 21 authorized the persistence milestone. That follow-on work is
now complete:

- the application database is `backend/data/expedia_mini.db`;
- all four CSV files are validated and imported once at backend startup;
- the seed marker prevents duplicate imports and preserves later changes;
- all application reads and writes use SQLite after seeding, including search
  and recommendations;
- typed models live under `backend/app/models/`, while SQLite and catalog
  controllers live under `backend/app/controllers/`;
- booking create, history/read, cancel/update, and test-record deletion are
  exposed through FastAPI and initiated by the Vue View; and
- 25 backend tests cover seed models and relationships, persistence, catalog
  reads, CRUD, and routes.

No SQLite package was installed for the follow-on milestone.
