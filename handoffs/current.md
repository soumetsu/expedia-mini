# Current Handoff

## Handoff status

- Last updated: `2026-09-29 22:54 EDT`
- Claims last verified: `2026-09-29 22:54 EDT`
- Update trigger: Added and reviewed separate Google Maps links for live hotel
  cards after the user's browser annotation and continuation request.

## Objective

The live hotel-search and connected-map milestone is implemented. A five-digit U.S. ZIP is
resolved through FastAPI and Geoapify Geocoding, hotel places are retrieved
through Geoapify Places, and Vue displays the factual response in a synchronized
list and Leaflet map. If an exact postcode boundary has no usable hotel records,
the backend searches live Geoapify Places circles at 5, 15, then 30 miles and
stops at the first populated radius. The remaining guide stage is the
**recorded demonstration**.

Each live result now keeps Leaflet selection as one button and offers a separate
Google Maps search link that opens in a new tab. The link uses the provider
address when present and provider coordinates otherwise.

Live results must never imply provider-unsupported prices, ratings, reviews,
room availability, or booking confirmation. The fictional SQLite booking
sandbox remains visually and behaviorally separate.

## Git publication state

- Current branch: `main`.
- `HEAD` and `origin/main` both resolve to
  `78fff519c18d44f6790ae9ef21e2bbcf5d725556`.
- The complete Geoapify/Leaflet milestone is uncommitted. The working tree was
  intentionally preserved; no commit or push was requested.
- Existing untracked Geoapify configuration/controller/test files are part of
  this milestone and must not be discarded.

## Current state

- `GET /api/hotels/nearby?postcode=<ZIP>&limit=<1-50>` is the live contract.
  It validates five-digit ZIPs, resolves the exact U.S. postcode, searches
  `accommodation.hotel` inside the returned Geoapify `place_id`, and applies a
  proximity bias from the ZIP reference center.
- The controller requires finite coordinates and a returned hotel postcode
  equal to the query. This defensive check was added after live Geoapify review
  showed that a `place:` result could contain adjacent postcodes.
- If the exact filtered result is empty, the controller makes live-only circle
  searches at 5, 15, then 30 miles and stops at the first usable set. It never
  falls back to SQLite or CSV. Circle results are independently distance-checked
  and report whether their provider postcode matches the searched ZIP.
- Provider records are deduplicated by normalized hotel name, their
  straight-line distance is calculated with the Haversine formula, and results
  are sorted nearest first. Missing names/addresses are not invented.
- Invalid input is 422, an unresolved ZIP is 404, missing backend configuration
  is 503, and provider failure is 502. A resolved ZIP with no hotels through
  the 30-mile fallback is a successful HTTP 200 empty result.
- The temporary `/api/demo/zip-location` route and fixed-`16802` Vue panel are
  removed.
- The primary Vue search accepts ZIP codes only and no longer calls the
  fictional `/api/hotels/search` catalog endpoint.
- `NearbyHotelList.vue` and `HotelMap.vue` share Geoapify `place_id` selection.
  Card selection focuses the numbered marker and safe-text tooltip; marker
  selection highlights and scrolls/focuses the matching card.
- Each live card contains a sibling Google Maps link rather than nesting an
  anchor inside the selection button. It uses Google's `api=1` search URL,
  safely encodes provider data, opens `_blank`, and sets
  `rel="noopener noreferrer"`. No Google API key is required.
- Leaflet 1.9.4 is installed. The map uses OpenStreetMap tiles and attribution,
  so no browser tile credential is configured. The backend Geoapify key remains
  only in the ignored project-root `.env` and is never returned to Vue.
- The live-search UI uses a distinct blue/cyan treatment. Desktop uses list and
  map columns; narrow screens place the map above the cards.
- The result panel names Geoapify Places, Geoapify Geocoding, and OpenStreetMap.
  Expanded results show the selected radius and provider-postcode relationship.
  Distance text is blue/Nearby through 5 miles, orange/Far above 5 through 15,
  and red/Very far above 15.
- The separate fictional booking sandbox retains frontend create, history/read,
  cancel-with-retention, and user-created-test-record deletion.
- `README.md`, `report.md`, `docs/design.md`, and `docs/verification.md` contain
  the durable implementation, architecture, and verification record.
- The supplied CSV files were not modified.

## Files changed for this milestone

- Backend contracts/routes: `backend/app/models/schemas.py`,
  `backend/app/models/__init__.py`, `backend/app/routes.py`.
- Geoapify/configuration: `backend/app/config.py`,
  `backend/app/controllers/geocoding.py`.
- Backend tests: `backend/tests/test_config.py`,
  `backend/tests/test_geocoding.py`, `backend/tests/test_routes.py`.
- Frontend dependency: `frontend/package.json`, `frontend/package-lock.json`.
- Frontend live search/map: `frontend/src/components/HotelSearchForm.vue`,
  `frontend/src/components/HotelMap.vue`,
  `frontend/src/components/NearbyHotelList.vue`,
  `frontend/src/pages/SearchPage.vue`, `frontend/src/services/api.js`, and
  `frontend/src/style.css`.
- Booking separation: `frontend/src/components/RecommendedStays.vue`.
- Documentation: `README.md`, `report.md`, `docs/design.md`,
  `docs/verification.md`, and this handoff.

## Verification

- Pre-change baseline: all 43 backend tests passed; the Vue build passed with
  19 modules transformed.
- The user explicitly approved `leaflet@1.9.4`. npm installed that exact package,
  audited 37 packages, and reported zero vulnerabilities.
- Focused Geoapify/controller/route suite: 19 tests passed.
- Final backend regression suite: all 47 tests passed in 19.040 seconds.
- Final Vue production build: passed with 25 modules transformed after the ZIP
  input visibility correction and again after the fallback UI copy update.
- `git diff --check` passed; warnings only describe future LF-to-CRLF conversion.
- `.env` exists, is ignored, is not tracked, and its value was never printed.
- Live API: health returned `ok` and status-only configured-key feedback;
  invalid ZIP returned 422; removed demo route returned 404.
- Live provider: `16802` returned 20 current hotels in the first populated
  5-mile fallback; the nearest was 0.60 miles away and adjacent postcodes were
  preserved and labeled. `10036` remained in exact-boundary mode with 16 unique
  normalized hotel names.
- Browser at the narrow viewport verified source disclosure, expanded-radius
  explanation, outside-ZIP badges, blue Nearby distance text, OpenStreetMap
  attribution, list-to-marker selection, marker-to-card selection, and the
  separated booking sandbox. Browser console warnings/errors were empty.
- The Google Maps card update passed the Vue build with 25 transformed modules.
  Browser inspection of ZIP `22150` verified separate selection/link controls,
  the encoded Residence Inn provider address, `_blank`,
  `noopener noreferrer`, and the narrow layout. The in-app browser did not
  expose an external Google tab after automated activation, so no Google page
  load is claimed; the rendered new-tab link contract was verified directly.
- The final rerun built 25 Vue modules in 1.76 seconds. `git diff --check`
  passed with line-ending notices only, `.env` remained ignored, and no supplied
  CSV file was modified.
- The npm-managed dependency directory was restored immediately after the
  bundled pnpm wrapper tried to relocate four ignored local packages. No package
  download completed, its generated `.pnpm-store/` cache was removed, and the
  direct local Vite build passed afterward.

## Running services

- FastAPI was restarted for verification in session `2527` with server process
  `15116` at `http://127.0.0.1:8000`.
- Vite was started for verification in session `2706` at
  `http://127.0.0.1:5173`.
- These are timestamped claims. Verify ownership and reachability before reusing
  or stopping either process.

## Decisions and constraints

- The main search is live ZIP-only. Keep the legacy fictional catalog API only
  for the explicitly labeled booking exercise and regression coverage.
- The response limit defaults to 20 and is capped at 50. Provider coverage and
  ordering can change; never hard-code a live result count in application logic.
- The implemented fallback must remain live-only: exact boundary, then 5, 15,
  and 30 miles, stopping at the first nonempty radius. Do not substitute the
  SQLite catalog or source CSV files.
- Keep the implemented source disclosure: hotel records are live Geoapify
  Places data, the ZIP center is Geoapify Geocoding data, and map imagery uses
  OpenStreetMap tiles.
- Treat all provider strings as untrusted text. Leaflet tooltips build DOM nodes
  with `textContent` rather than injecting provider HTML.
- Google Maps links must use only the returned address or coordinates. Google
  controls the final place match, so do not describe the link as identity,
  availability, or booking confirmation.
- Keep the backend Geoapify key in `.env`. Do not create a `VITE_` copy or expose
  it in response payloads.
- The attached RAG diagram and example prompt remain chat-only context. SQLite
  proxy RAG is a possible future milestone, not part of this implementation.

## Blockers or risks

- No implementation blocker remains.
- Geoapify data may be incomplete or change between requests. Adjacent-postcode
  fallback records are intentionally retained and labeled rather than omitted.
- Google may resolve a provider address or coordinate query differently over
  time. The app supplies navigation context but does not verify Google's match.
- A recorded demonstration has not been created yet.

## Exact next action

Record the demonstration in this order: show invalid ZIP feedback, search
`16802` and explain the live sources and 5-mile fallback, select a card and then
a different marker to demonstrate two-way synchronization, show one Google Maps
link opening from a live card, search `10036` to show exact-boundary mode, and
finish by pointing out provider-field limits and the separate fictional booking
sandbox. After the recording, review the working-tree diff and commit or publish
only if the user explicitly requests it.
