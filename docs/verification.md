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

The Prompt 03 suite contains 12 tests for stable data paths, CSV validation and
relationships, search normalization and results, calculated display fields,
route registration, health behavior, and blank-query rejection.

Start the API from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify that `GET http://127.0.0.1:8000/api/health` returns HTTP 200 and:

```json
{"status":"ok"}
```

Verify `GET /api/hotels/search?name=%20hArBoR%20lAnTeRn%20` returns count 2 with
T001 and T009. Verify `No Such Expedia-Mini Hotel` returns count 0 and an empty
list. Keep the API running when continuing with the integrated frontend check.

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
5. Confirm a direct search for `hArBoR lAnTeRn` returns count 2 and trip IDs
   T001 and T009. Confirm `No Such Expedia-Mini Hotel` returns count 0.
6. Open `http://127.0.0.1:5173/`. Confirm the page has a visible Hotel name
   label and Search button.
7. Submit whitespace-padded `hArBoR lAnTeRn` with Enter. Confirm the input is
   trimmed, the count is 2, and the table matches the API values for T001 and
   T009.
8. Search for `No Such Expedia-Mini Hotel` with the button. Confirm the old
   table is removed and a clear no-results message appears.
9. Submit a blank value and confirm that inline validation prevents a request.
10. If testing failure feedback, stop only a backend process started for this
    check, search once, confirm the distinct API-error message, and restart the
    backend before finishing.
11. At a 375-by-700 viewport, confirm the form remains usable and the wide
    table stays inside its horizontal scroll region.
12. Confirm a clean browser run has no warning or error console entries, and
    inspect both service logs for unexpected errors.

Store browser evidence under `docs/screenshots/part1/`. Prompt 04 evidence uses:

- `hotel-search-success.png`
- `hotel-search-no-results.png`
- `hotel-search-narrow-viewport.png`

## Persistence checks

Before adding any SQLite package, check whether the selected Python interpreter
can import the standard-library `sqlite3` module. When persistence is added,
write a test record, close the connection, reopen the same database, and verify
that the record remains. Restarting the application must not overwrite new or
changed records with seed CSV data.
