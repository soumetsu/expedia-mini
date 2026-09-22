# Verification Guide

Use the narrowest relevant checks first. Record commands and outcomes in the
task completion summary and update `report.md` for milestone-level results.

## Scaffold checks

- Confirm every documented path exists.
- Parse `frontend/package.json` as JSON.
- Confirm `node_modules/`, `.venv/`, build output, and runtime databases remain
  excluded by `.gitignore`.
- Preserve the supplied CSV files.

## Backend checks

The backend environment is installed under `backend/.venv/`. Run its tests from
`backend/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The backend suite contains 25 tests for stable seed paths, validation of all
four CSV files and their relationships, hotel/city/state/date search,
deterministic distinct-hotel recommendations, calculated display fields,
SQLite seeding and CRUD, seed-record protection, route registration, health
behavior, and validation. One test changes a hotel name directly in a temporary
post-seed SQLite database and proves search returns that changed value, which
guards against accidental CSV reads during application requests.

Start the API from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify that `GET http://127.0.0.1:8000/api/health` returns HTTP 200 and:

```json
{"status":"ok"}
```

Verify `GET /api/hotels/search?name=%20hArBoR%20lAnTeRn%20` returns count 2 with
T001 and T009. Verify `name=Boston` returns T001, T002, T009, and T010. Verify
`GET /api/hotels/recommended?limit=3` returns T008, T005, and T001 in that
order. Verify `No Such Expedia-Mini Hotel` returns count 0 and an empty list.
Keep the API running when continuing with the integrated frontend check.

## Frontend checks

The frontend dependencies are already installed. From `frontend/`, run:

```powershell
npm run build
```

There is no configured frontend lint or test script. Do not add a test framework
without separate approval. `npm run build` is the current automated frontend
check.

## Integrated Part 1 smoke test

1. Confirm ports 8000 and 5173 are available. Do not stop unrelated processes.
2. Start the backend with the command above.
3. From `frontend/`, start:

   ```powershell
   npm run dev -- --host 127.0.0.1 --port 5173
   ```

4. Confirm `GET http://127.0.0.1:8000/api/health` returns HTTP 200 and
   `{"status":"ok"}`.
5. Confirm a direct `Boston` search returns count 4 and trip IDs T001, T002,
   T009, and T010. Confirm `No Such Expedia-Mini Hotel` returns count 0.
6. Confirm the recommendations endpoint returns three distinct hotels in the
   verified T008, T005, T001 order.
7. Open `http://127.0.0.1:5173/`. Confirm the page has a visible location label,
   Find stays button, and three recommended cards below the search panel.
8. Submit whitespace-padded `bOsToN` with Enter. Confirm the input is trimmed,
   the count is 4, and the cards match the API values for T001, T002, T009, and
   T010. Confirm results appear above recommendations.
9. Search for `No Such Expedia-Mini Hotel` with the button. Confirm the old
   table is removed and a clear no-results message appears.
10. Submit a blank value and confirm that inline validation prevents a request.
11. If testing failure feedback, stop only a backend process started for this
    check, search once, confirm the distinct API-error message, and restart the
    backend before finishing.
12. At a narrow viewport, confirm the primary search, secondary date/user
    controls, stay cards, and recommendation cards stack cleanly.
13. Confirm a clean browser run has no warning or error console entries, and
    inspect both service logs for unexpected errors.

Store browser evidence under `docs/screenshots/part1/`. Prompt 04 evidence uses:

- `hotel-search-success.png`
- `hotel-search-no-results.png`
- `hotel-search-narrow-viewport.png`

## SQLite persistence preflight

Run this from `backend/` before proposing any SQLite package:

```powershell
@'
import sqlite3
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    database = Path(directory) / "preflight.db"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE preflight (id INTEGER PRIMARY KEY, value TEXT NOT NULL)"
    )
    connection.execute(
        "INSERT INTO preflight (value) VALUES (?)", ("persisted",)
    )
    connection.commit()
    connection.close()

    reopened = sqlite3.connect(database)
    row = reopened.execute("SELECT id, value FROM preflight").fetchone()
    reopened.close()
    assert row == (1, "persisted")

print(f"executable={sys.executable}")
print(f"sqlite={sqlite3.sqlite_version}")
print(f"round_trip={row!r}")
'@ | .\.venv\Scripts\python.exe -

.\.venv\Scripts\python.exe -m pip check
```

The September 17, 2026 preflight used
`backend/.venv/Scripts/python.exe` (Python 3.13.15), reported SQLite 3.50.4,
returned `(1, 'persisted')` after closing and reopening the database, removed
the temporary database, and reported `No broken requirements found.` No
download or installation was needed.

Runtime support is ready and application persistence is implemented. The tests
verify the database path and schema, one-time CSV seeding without duplication
or reset, all-four-table counts and references, SQLite-backed catalog reads,
CRUD behavior, seed protection, and retention/removal semantics.
Runtime database files must remain excluded from Git.

For a freshly initialized test database, verify these seed counts:

| Table | Rows |
| --- | ---: |
| `hotels` | 8 |
| `trips` | 12 |
| `users` | 6 |
| `bookings` | 6 |

After initialization, temporarily removing access to the CSV directory or
editing a temporary SQLite row must not cause requests to fall back to CSV.
The `test_catalog_reads_reflect_sqlite_changes_after_seed` automated test
covers the positive version of this contract.

## Booking CRUD smoke test

Use Demo Traveler 6 so verification does not alter supplied booking examples:

1. Search New York with check-in `2026-09-21` and check-out `2026-10-01`.
   Confirm T003 and T004 appear above recommendations.
2. Select **Book this stay** on T003 and confirm the success message names Demo
   Traveler 6.
3. Open `/bookings`; confirm the new booking is shown as confirmed.
4. Select **Cancel booking**; confirm the status changes to cancelled and the
   card remains in history.
5. Select **Delete test booking**; confirm a second, explicit delete choice is
   displayed. Complete deletion only when the test run is authorized.
6. Confirm the record is removed and the empty-history state appears.
7. Check that a seeded booking offers cancellation but no delete action.

The verified September 21, 2026 run created B007, read it in U006 history,
cancelled it while retaining the row, displayed the two-step delete control,
then deleted that exact temporary record through the API for cleanup. U006
history was empty afterward.
