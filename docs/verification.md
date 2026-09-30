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

The backend suite contains 47 tests. In addition to the SQLite, catalog,
booking, authentication, and search-history coverage, mocked Geoapify tests
verify exact U.S. ZIP resolution, postcode boundary and hotel-category request
parameters, exact returned-postcode filtering, 5/15/30-mile circle fallback,
first-populated-radius stopping, defensive radius checks, missing names and
postcodes, invalid coordinates, normalized-name deduplication, Haversine
distance ordering, successful empty results, source metadata, missing
configuration, and provider failure. No automated test sends a live provider
request.

Start the API from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify that `GET http://127.0.0.1:8000/api/health` returns HTTP 200. Its
`geoapify_api_key_status` is either `key is configured` or
`key is not configured`; it must never return the key itself.

The live route is
`GET http://127.0.0.1:8000/api/hotels/nearby?postcode=<ZIP>&limit=20`.
With a configured key, `postcode=10036` should resolve and return only hotels
whose returned postcode is `10036`; provider data and counts can change. A
valid resolved ZIP with no exact hotel matches expands through live 5-, 15-,
and 30-mile Geoapify circle searches. It returns HTTP 200 with `count: 0` only
when the 30-mile search is also empty.
An invalid ZIP returns 422, an unresolved ZIP returns 404, missing configuration
returns 503, and a provider failure returns 502. The removed
`/api/demo/zip-location` route should return 404.

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

## Integrated live-search smoke test

1. Confirm ports 8000 and 5173 are available. Do not stop unrelated processes.
2. Start the backend with the command above.
3. From `frontend/`, start:

   ```powershell
   npm run dev -- --host 127.0.0.1 --port 5173
   ```

4. Confirm health returns HTTP 200 without exposing the configured key.
5. Confirm `postcode=ABCDE` returns 422 and the removed demo route returns 404.
6. Confirm `postcode=16802` currently reports `search_scope: expanded radius`,
   `search_radius_miles: 5`, live Geoapify source fields, and nearby records
   labeled with their returned postcodes. Provider data and counts can change.
7. Confirm `postcode=10036` returns hotel records and every result's `postcode`
   is `10036`. Provider counts can change; the September 29 live check returned
   16 normalized hotel names after deduplication.
8. Open `http://127.0.0.1:5173/`. Confirm the primary field accepts only five
   numeric characters and rejects an incomplete ZIP before a request.
9. Submit `16802`; confirm the page names all three sources, explains the first
   populated radius, labels results outside the ZIP, and displays distance text
   with Nearby/Far/Very far severity and blue/orange/red thresholds.
10. Submit `10036`; confirm it remains an exact-boundary result with live cards
    and an OpenStreetMap-attributed Leaflet
    map appear, with no live price, rating, review, room, availability, or
    booking claim.
11. Select a card. Confirm its numbered marker changes state, the map pans or
    keeps it visible, and a safe-text tooltip names the same hotel.
12. Select a different marker. Confirm the matching card becomes selected and
    is scrolled/focused into view.
13. Confirm each live card exposes a separate **Open address in Google Maps**
    link. Inspect that it uses an encoded `https://www.google.com/maps/search/`
    URL with `api=1`, opens a new tab, and does not replace or activate the
    card's Leaflet-selection action. For a provider record without an address,
    confirm the link label and query use its returned coordinates instead.
14. Activate **Clear ZIP** and confirm the ZIP, list, map, and request feedback
    are removed without changing booking records.
15. At a narrow viewport, confirm the map appears above the readable card list;
    at a wide viewport, confirm the list and map use two columns.
16. Confirm the visibly separated fictional booking sandbox still creates a
    demo booking and that history/cancel/delete remain available on `/bookings`.
17. Confirm a clean browser run has no warning or error console entries, and
    inspect both service logs for unexpected errors.

Earlier Part 1 browser evidence remains under `docs/screenshots/part1/`:

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

## Demo authentication and search-history smoke test

Authentication uses only the installed Python standard library for password
hashing and process-local bearer sessions. No package installation is needed.

1. Open `/register` and submit a unique username, an eight-character-or-longer
   password, and either a blank email or a made-up but syntactically valid email
   such as `traveler@example.test`.
2. Confirm a malformed value such as `#@!(*&*!(@#&@gmail.coma` is rejected,
   and that a repeated username or email returns a useful conflict message.
3. Confirm successful registration signs the user in and exposes the username
   plus **Log out** control. Passwords must never appear in API responses.
4. Search for Boston while signed in, open `/search-history`, and confirm the
   query and result count are shown for that account.
5. Sign out, sign in as another account, and confirm that the first account's
   search is not shown. Guest searches remain available but are not persisted.
6. Confirm `GET /api/auth/me` and `GET /api/search-history` return HTTP 401
   without the bearer token, while the existing hotel and booking flows remain
   available.

The September 22, 2026 verification used the migrated seeded account
`demo_u001` with its deterministic demo password, confirmed `/auth/login`,
`/auth/me`, the sign-in page, the registration page, and a private Boston search
history entry. The synthetic history row was removed after the check. The new
focused auth suite covers hashed-password verification, username/email
uniqueness, malformed-email rejection, and isolation between two users.
