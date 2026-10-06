# Current Handoff

## Handoff status

- Last updated: `2026-10-06 EDT`
- Claims last verified: `2026-10-06 EDT`
- Update trigger: Condensed `report.md` and recorded the user-confirmed manual
  spot checks for the most applicable parts of the latest Assignment 2 work.

## Objective

Assignment 2 Part 2 is implemented on `assignment2_part2_in_class`. The frozen
Part 1 Geoapify ZIP search and synchronized list/map remain intact. ZIP lookup
is local-first, API hotels can be saved and removed, and saved hotels expose
fictional October 10–14, 2026 rates and room counts. `report.md` now summarizes
the implementation and verification without the previous chronological detail.

## Git publication state

- Current branch: `assignment2_part2_in_class`.
- No commit or push was requested or performed.
- Supplied CSV files and ignored local configuration were not modified.

## Current state

- SQLite initialization additively and repeatably creates `saved_hotels`,
  `saved_hotel_locations`, and `demo_hotel_nights` before the Assignment 1 seed
  marker check.
- `saved_hotels.hotel_id` preserves the exact Geoapify `place_id` and is the
  primary key. Name and address are nullable; latitude/longitude are required
  and range checked.
- `saved_hotel_locations` separately associates a provider hotel with the
  searched ZIP, stored ZIP center, result locality/postcode, search scope,
  radius, distance, and inside/outside relationship.
- `demo_hotel_nights` uses `(hotel_id, stay_date)` as its primary key, enforces
  the foreign key, and defaults to fictional 10,000-cent rates and 20 rooms.
- Saving inserts only missing rows for October 10–14, 2026. Repeated saves do
  not duplicate hotels/nights or overwrite edited rates or availability.
- Removing a hotel deletes only that provider hotel's nights, ZIP associations,
  and saved-hotel row in one transaction.
- `GET /api/saved-hotels?postcode=<ZIP>` returns the saved subset for that ZIP,
  its stored search context, all demo nights, and all saved provider IDs.
- `POST /api/saved-hotels` saves the provider hotel plus current ZIP context.
  `DELETE /api/saved-hotels/{hotel_id}` removes its local graph.
- Vue requests the local endpoint first. A successful empty response falls
  through to the unchanged `GET /api/hotels/nearby`; local failure stops and
  displays an error instead of silently calling the provider.
- Local results are labeled `Saved locally`, state that they are not the full
  area inventory, and label rates/rooms as simulated classroom data. Provider
  fallback results are labeled `API results`.
- Add is disabled for saved hotels and while pending. Remove appears only for
  saved hotels. UI saved state changes only after backend success and is
  restored from provider IDs after refresh.
- Card and Leaflet marker selection continue to share the provider ID.

## Files changed

- Backend persistence: `backend/app/controllers/database.py`
- Backend contracts: `backend/app/models/schemas.py`,
  `backend/app/models/__init__.py`
- FastAPI adapter: `backend/app/routes.py`
- Backend tests: `backend/tests/test_database.py`,
  `backend/tests/test_routes.py`
- Frontend API/orchestration: `frontend/src/services/api.js`,
  `frontend/src/pages/SearchPage.vue`
- Frontend result views: `frontend/src/components/NearbyHotelList.vue`,
  `frontend/src/components/HotelMap.vue`, `frontend/src/style.css`
- Documentation: `README.md`, `report.md`, `docs/design.md`,
  `docs/verification.md`, and this handoff

## Verification

- Focused database and route suite: 22 tests passed in 19.278 seconds.
- Full backend suite: 54 tests passed in 48.580 seconds.
- Final Vue production build: 25 modules transformed successfully.
- Temporary-database mutation tests cover repeat saves, preservation of edited
  nightly values, ZIP-specific association retrieval, global saved status,
  transactional deletion, and preservation of unrelated records.
- Runtime database path:
  `C:\Users\henry\Desktop\IST 402\assignment 1\backend\data\expedia_mini.db`.
- Runtime integrity is `ok`; foreign-key check has zero violations. Counts are
  unchanged for Assignment 1: 8 hotels, 12 trips, 8 users, 9 bookings.
- Runtime Assignment 2 tables are clean for manual review: 0 saved hotels,
  0 ZIP associations, and 0 demo nights.
- Read-only live HTTP verification returned healthy status and a successful
  empty saved-hotel response for ZIP `10036`.
- Browser inspection of ZIP `10036` confirmed local-first empty fallback to 16
  current API records, `API result` badges, Add controls, and the connected map.
  Browser console warnings/errors were empty. No Add/Remove mutation was made.
- The user reports that manual spot checks were completed on the most
  applicable user-facing portions of the latest addition: local-first search,
  saved/API labels, Add/Remove controls, refreshed saved results, list/map
  behavior, responsive presentation, and simulated-data disclosures.
- `git diff --check` passed with line-ending notices only.

## Running services

- FastAPI: `http://127.0.0.1:8000`, listener PID `5724`, command owned by this
  repository's `backend\.venv` and Uvicorn application.
- Vite: `http://127.0.0.1:5173`, listener PID `22620`, command owned by this
  repository's `frontend\node_modules\vite`.
- Ownership and reachability were rechecked after restart on October 1, 2026.

## Decisions and constraints

- Keep the live provider endpoint, ZIP behavior, fallback radii, response
  transformation, and map/list selection frozen.
- Never describe the fictional rates or room counts as Geoapify data.
- Local matches are a saved subset, not complete area inventory.
- Keep all SQLite access in `database.py`; routes remain thin adapters.
- Do not add dependencies, frontend chatbot features, or provider-search writes.

## Blockers or risks

- No implementation blocker remains.
- Geoapify results can change, so observed provider counts are timestamped.
- The condensed report deliberately treats automated tests as the evidence for
  schema constraints, idempotency, and transactional deletion.

## Exact next action

Review the condensed `report.md`. Do not commit or publish unless the user
explicitly requests it.
