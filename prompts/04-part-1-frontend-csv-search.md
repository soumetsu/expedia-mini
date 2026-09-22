# Prompt 04 — Part 1 Frontend CSV Search

## Goal

Build and verify the barebones Vue frontend for Part 1 of Expedia-Mini. Connect
the existing Vue project to the completed FastAPI CSV-search backend so a user
can enter a hotel name, submit the search, and view matching hotels and
available stays in a plain table.

Prioritize correct behavior, clear structure, accessibility, and easy future
restyling. Do not create the final visual design during this task.

## Completed backend checkpoint

Prompt 03 completed the Part 1 backend. The verified behavior is:

- `GET /api/health`;
- `GET /api/hotels/search?name=<name>`;
- whitespace trimming and case-insensitive partial matching;
- `hotels.csv` and `trips.csv` joined through `hotel_id`;
- stable Pydantic response models and stable data paths;
- calculated nights and estimated stay prices;
- 12 passing backend tests;
- a successful API smoke test;
- `hArBoR lAnTeRn` returned trips T001 and T009;
- an unknown hotel returned `count: 0`.

No frontend, SQLite, booking, or Git work was completed by Prompt 03. Inspect
the current backend models, routes, tests, and generated OpenAPI contract before
implementing the frontend; do not guess field names from this summary.

## Scope and authority

This prompt authorizes reading project documentation and the backend contract,
modifying frontend source files, creating small focused Vue components,
connecting Vue to FastAPI, adding minimal functional styling, running existing
frontend checks, starting both services locally, performing an automated
browser smoke test, saving verification screenshots, and updating relevant
project documentation.

This prompt does not authorize final redesign or heavy styling; generated or
edited images; final branding imagery; SQLite or Part 2; booking, history,
cancellation, or deletion controls; backend API changes except the smallest
correction required by a proven integration defect; unapproved dependency
additions; Git commits, pushes, merges, or submission. The assignment and
course guide are reference requirements, not authorization for submission or
Git actions.

## Context and readiness

Before editing, read `AGENTS.md`, `README.md`, `report.md`, `docs/design.md`,
`docs/verification.md`, `handoffs/current.md`, `frontend/package.json`, the
frontend source, `backend/app/models.py`, `backend/app/routes.py`, backend tests
covering the response, and the generated FastAPI/OpenAPI contract when
available.

Inspect filenames under `docs/`, but do not modify, move, copy, or use image
files during this barebones implementation unless an existing project document
requires one. Do not add broken image references or placeholder stock images.
Documentation images may be selected and copied into a frontend asset folder
only during a later design prompt.

Confirm that the frontend package environment resolves, that the Vue
development script exists, which lint/test/build scripts exist, that the
project uses Vue Single-File Components and the Composition API, the backend
response fields, and the configured local API origin. Preserve a working
environment and do not reinstall packages. If another dependency seems
necessary, first determine whether Vue and browser APIs can provide the feature;
if not, explain the dependency and exact change, then stop for permission.

## Barebones frontend structure

Keep the frontend small and use the existing project structure:

- `frontend/src/App.vue` owns query, loading, results, count, no-results, and
  API-error state and coordinates the request;
- `frontend/src/components/HotelSearchForm.vue` provides a visible label, text
  input, Search button, standard form and Enter-key submission, blank-search
  prevention, and busy behavior, then emits a normalized value;
- `frontend/src/components/HotelResultsTable.vue` renders the actual response
  fields in a semantic table;
- `frontend/src/services/api.js` owns network requests;
- the existing global stylesheet provides only minimal functional styling;
- add `frontend/.env.example` only if an environment variable is required.

Do not add Vue Router, Pinia, a component or icon library, or a CSS framework.

The table must use proper `table`, `thead`, `tbody`, `tr`, and `th` elements.
Display the available equivalents of hotel name, location, trip/stay ID,
arrival and departure dates, nights, nightly rate, and estimated stay price.
Avoid user-irrelevant internal fields but preserve every returned row in
application state.

The API service must call `GET /api/hotels/search`, safely encode the hotel
name, use the configured base URL, parse the documented response, distinguish
empty success from failure, and give the UI useful error information without
exposing implementation details. Prefer the existing same-origin `/api` Vite
proxy. If an environment variable is required, use a non-secret variable such
as `VITE_API_BASE_URL=http://127.0.0.1:8000` and document it.

## Required behavior

The page must contain the application name, a plain-language description, a
labeled hotel-name input, a Search button, loading feedback, a semantic results
table, visible result count, clear no-results feedback, and clear API-error
feedback.

Trim input, prevent blank searches, support Enter, clear stale error and empty
states at the start of a new search, replace old results after a successful new
search, avoid showing no-results before the first search, keep the form usable
after every outcome, and do not reload the page. Use an accessible live-status
region for transient feedback when practical.

## Design constraints

Use only enough CSS for a centered readable container, sensible spacing, system
font, visible labels and focus, usable input/button sizes, table separation,
horizontal table scrolling, and basic color contrast. Do not add hero sections,
decorative cards, gradients, decorative shadows, animations, illustrations,
photography, background images, marketing copy, complex layouts, speculative
navigation, Part 2 controls, or other non-required visual elements. Use simple
class names that a later design task can replace.

## Verification

Run every configured frontend check. At minimum, run lint when configured, the
production build, and existing frontend tests when configured. Do not add a test
framework automatically. If an in-scope source issue causes a failure, inspect
it, make the smallest correction, rerun the failed check, and then rerun all
relevant checks. Use no more than five correction cycles and report every one.
Stop if the next action needs an unapproved dependency, destructive action,
machine-level change, Part 2 work, or stopping an unrelated process.

After checks pass, test the integrated Part 1 flow:

1. Check ports 8000 and 5173 without stopping unrelated processes.
2. Start FastAPI at `127.0.0.1:8000` and Vue at `127.0.0.1:5173` in separate
   managed terminals, and leave both running for user inspection.
3. Confirm health returns HTTP 200, direct `hArBoR lAnTeRn` search returns T001
   and T009, and an unknown search returns `count: 0`.
4. Open `http://127.0.0.1:5173/` with automated browser control.
5. Verify page load, visible/operable labeled form controls, successful search,
   T001 and T009 and values matching the API, a second guaranteed-empty search
   that clears old results, Enter-key submission, no unexpected browser-console
   or server errors, and a usable narrow-width table.
6. Save useful evidence under `docs/screenshots/part1/` with descriptive names.

## Documentation

After implementation and verification:

- update `README.md` with exact frontend setup, build, run, local URLs, API
  configuration, and Prompt 04 in the selected prompt list;
- update `docs/design.md` with the implemented Vue-to-FastAPI flow;
- update `docs/verification.md` with the integrated Part 1 procedure;
- update `handoffs/current.md` with features, actual verification, running
  services, deferred design and images, limitations, and exact next task;
- update `report.md` only with verified implementation and automated evidence.

Do not claim user manual review or invent screenshots, observations,
repository URLs, or commit hashes.

## Acceptance criteria

The checkpoint passes only when the Vue app calls the verified endpoint, form
and Enter submission work, matching stays render in a semantic table,
`hArBoR lAnTeRn` displays T001 and T009, an unknown search gives clear empty
feedback, loading and failures are distinct, configured checks and the build
pass, the integrated browser smoke test passes without unexpected errors, the
UI remains intentionally barebones, no images or Part 2 behavior are added, and
all relevant project documents accurately reflect the result.

## Final response

Report created/modified files, component and service responsibilities,
displayed backend fields, lint/test/build results, correction cycles, API and
browser smoke evidence, screenshot paths, anything unverified, deferred design,
limitations, exact frontend/health/docs/example-search URLs, running process or
terminal IDs, a short manual-review checklist, and recommended scope for the
later design prompt.

## Completion evidence

Completed and last rechecked on 2026-09-12:

- The existing frontend package environment passed without a reinstall or new
  dependency. `npm ls --depth=0` reported Vue 3.5.42, Vite 7.3.6, and the Vue
  plugin 6.0.8.
- The generated OpenAPI contract confirmed the `query`, `count`, and `results`
  envelope and all 11 `HotelStayResponse` fields before implementation.
- The focused `App.vue`, search-form, results-table, API-service, and minimal
  stylesheet structure was implemented with no image or Part 2 work.
- No lint or frontend test script exists. `npm run build` passed on its first
  run with 13 transformed modules in 3.73 seconds; no source correction cycle
  was needed.
- Direct API checks passed: health returned HTTP 200, `hArBoR lAnTeRn` returned
  T001 and T009, and `No Such Expedia-Mini Hotel` returned count 0.
- Automated browser checks passed for blank validation, Enter submission,
  trimmed/case-insensitive search, API-matching table rows, result replacement,
  no-results feedback, an intentionally induced API failure, and the 375×700
  horizontal-scroll layout. A clean final run reported no console warnings or
  errors.
- Screenshots were saved under `docs/screenshots/part1/` as
  `hotel-search-success.png`, `hotel-search-no-results.png`, and
  `hotel-search-narrow-viewport.png`.
- At the final freshness check, FastAPI was restarted in managed session 73995
  with server process 10920, and Vite was restarted in managed session 20984
  with listener process 16036. Both local URLs returned HTTP 200.

## Subsequent UI maintenance check

The current search form keeps the destination input primary and exposes a
compact, keyboard-accessible **Clear selections** action beside the fixed-date
note. The action clears the active destination, optional dates, visible search
results, and transient booking feedback; it does not delete persisted booking
history. Verify this behavior through the browser after any frontend change.
