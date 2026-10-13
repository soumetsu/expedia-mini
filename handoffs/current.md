# Current Handoff

## Handoff status

- Last updated: `2026-10-13 EDT`
- Claims last verified: `2026-10-13 EDT`
- Update trigger: Captured the current Part 2 foundation and chatbot gap as five
  screenshots and linked them from `FINAL_REPORT.MD`.

## Objective

The current milestone is a support-only chatbot using
`gemini-3.5-flash-lite`. A fixed bottom-right Vue widget opens compactly,
optionally expands across most of the viewport, and sends bounded conversation
data through FastAPI. The Gemini key remains backend-only. SQL generation and
RAG are not implemented in this step. The header identifies the pinned model,
and successful replies show optional Gemini usage counts. Existing search,
saved-hotel, account, and booking behavior remains intact.

## Git publication state

- Assignment 2 commit: `1a47b59` (`Implement local saved-hotel workflow`).
- Local `main` was fast-forwarded to that commit without conflicts.
- `origin/main` remains at `5b882d5`; no push was requested or performed.
- Current branch: `rag_integration`; chatbot changes are committed.
- The verified implementation is committed as `72810dc` (`Add Gemini support
  chatbot`). `FINAL_REPORT.MD` is the canonical report for this chat and is
  included in the following documentation commit.
- The user's pre-existing `report.md` edits were preserved and extended only
  with the required chatbot milestone record.
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

- Chat provider/configuration: `backend/app/controllers/chat.py`,
  `backend/app/config.py`
- Chat contracts/route: `backend/app/models/schemas.py`,
  `backend/app/models/__init__.py`, `backend/app/routes.py`
- Chat tests: `backend/tests/test_chat.py`, `backend/tests/test_config.py`,
  `backend/tests/test_routes.py`
- Chat view/API: `frontend/src/components/ChatbotWidget.vue`,
  `frontend/src/App.vue`, `frontend/src/services/api.js`,
  `frontend/src/style.css`
- Chat documentation: `README.md`, `report.md`, `docs/design.md`,
  `docs/verification.md`, `FINAL_REPORT.MD`, and this handoff

Earlier Assignment 2 files remain:

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

- Focused chatbot/configuration/route suite: 22 tests passed.
- Full backend regression suite: 61 tests passed in 25.118 seconds.
- Vue production build passed with 26 modules transformed.
- Browser checkpoint confirmed the compact 384×544 desktop panel and optional
  1024×736 expanded mode at a 1280×800 viewport.
- One live browser request completed `/api/chat` with HTTP 200 and rendered a
  Gemini reply. A later repeat received Gemini HTTP 503 `UNAVAILABLE` due to
  high demand; FastAPI returned a sanitized 502 and Vue showed its retry state.
- The chatbot now retries one transient 429/5xx response and excludes failed
  user messages from later conversation history.
- The annotated header now shows `gemini-3.5-flash-lite`. A live HTTP 200 reply
  displayed provider-reported usage of 160 input + 149 output = 309 total
  tokens.
- October 13 browser evidence captured ZIP `16802` with 20 live results in the
  first populated 5-mile radius, ZIP `16801` with four saved hotels and labeled
  demo-night rows, and the support chatbot declining a date/price comparison.

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

- FastAPI: `http://127.0.0.1:8000`, listener PID `5404`, command owned by this
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
- Do not add dependencies, SQL/RAG behavior, booking actions, or provider-search
  writes to the support chatbot without separate authorization.

## Blockers or risks

- No implementation blocker remains.
- Geoapify results can change, so observed provider counts are timestamped.
- The condensed report deliberately treats automated tests as the evidence for
  schema constraints, idempotency, and transactional deletion.
- Gemini `gemini-3.5-flash-lite` can temporarily return HTTP 503 under high
  demand. The application exposes only a sanitized retryable error.

## Exact next action

Implement the Part 2 SQL-grounded RAG workflow only after explicit user
authorization. The new screenshots document the before state.
