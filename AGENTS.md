# Project Rules

These rules apply to the entire repository.

## General workflow

- Keep changes small, focused, and easy to review.
- Read `README.md`, `report.md`, the relevant file in `docs/`, and the supplied
  data documentation before changing application behavior.
- If `handoffs/current.md` exists, read it before starting work in a new thread;
  treat it as temporary context and verify its claims against the repository.
- Do not modify the source CSV files unless a task explicitly requires it.
- Do not commit secrets, local environment files, virtual environments,
  dependency folders, generated databases, or build output.
- Update `README.md` when setup steps or user-facing behavior change.
- Update `report.md` after completing a meaningful milestone or making an
  architectural decision.
- Treat `report.md` as the primary human-reviewed submission record. Preserve
  its required Part headings, add verified implementation and review evidence
  as work develops, and never invent repository URLs, commit IDs, screenshots,
  or test results.
- Keep reusable task briefs in `prompts/` and durable technical context in
  `docs/`; do not use a prompt file as the only record of a project decision.

## Current product direction

- Treat the responsive location/hotel search, optional fixed-date filters,
  deterministic recommendation cards, simulated booking, and separate booking
  history page as the implemented interface baseline.
- SQLite persistence, the frontend booking lifecycle, demo account
  authentication, and per-user search history are implemented; personalized
  recommendation ranking remains a future enhancement.
- Every booking lifecycle action must be available through the frontend: create
  a booking, read it in history, cancel it by updating its status while keeping
  the record, and delete a test booking. Do not require the user to edit CSV or
  database files directly.
- Keep backend changes focused. Preserve working search behavior and add only
  the contracts, validation, persistence, and control logic needed to support
  the agreed frontend behavior.
- Do not present planned features as implemented. The current data supports
  hotel name, city/state, fixed stay dates, nightly price, derived stay price,
  trip names, demo users, and booking status. It does not provide room
  inventory, traveler capacity, taxes or fees, amenities, reviews, weather,
  live demand, flights, cars, cruises, or package inventory.
- Persistence seeds hotels, trips, users, and bookings into SQLite once, then
  uses SQLite for application reads and writes. Preserve supplied IDs and
  generate collision-free IDs for new records.
- Preserve clear Model–View–Controller responsibilities: models
  define entities, fields, stored records, and relationships; Vue components
  form the view; FastAPI routes plus a focused database controller/service
  coordinate validation and CRUD operations.
- Demo authentication is implemented as a process-local bearer-session layer;
  passwords must be hashed and credentials must never be stored in plaintext.
  Search history must always be filtered by the authenticated user. Production
  authentication and dynamic-pricing experiments remain lower priority and
  require separate authorization. Never vary price based on battery level or
  device type. Any later pricing demonstration must be transparent,
  deterministic, and based on disclosed travel-domain inputs such as trip dates
  or an explicit holiday calendar.

## Backend

- Keep FastAPI code under `backend/app/`.
- Keep entity definitions and Pydantic input/output contracts under
  `backend/app/models/`. Models may describe fields and relationships but must
  not open SQLite, execute SQL, or depend on Vue.
- Keep database access and business workflows under `backend/app/controllers/`.
  `database.py` is the only application module that opens SQLite and owns
  schema creation, one-time seeding, reference enforcement, account records,
  search-history persistence, and booking CRUD. `auth.py` may own process-local
  session tokens but must call the database controller for credential work.
  Separate controllers such as `catalog.py` may call it through typed model
  contracts; they must not bypass it with direct SQL.
- Keep `routes.py` as a thin HTTP adapter: validate web inputs, call a
  controller, translate expected errors, and return Pydantic contracts. Do not
  put SQL or presentation logic in routes.
- Use the four supplied CSV files only to seed an uninitialized database. Once
  the seed marker exists, every application read and write—including hotel
  search and recommendations—must use SQLite.
- Use `/api` as the prefix for application endpoints.
- Use Pydantic models for request and response contracts once domain endpoints
  are introduced.
- Validate inputs and return useful HTTP errors; do not expose stack traces or
  sensitive details to clients.
- Resolve data paths from the source file location rather than the terminal's
  current directory.
- Read the supplied CSV files as UTF-8 with BOM support (`utf-8-sig`).

## Frontend

- Keep Vue source code under `frontend/src/`.
- Treat all Vue pages, components, and CSS as the MVC View. The View may call
  FastAPI through `services/api.js`; it must not read CSV files or SQLite.
- Prefer Vue 3 Composition API and small, single-purpose components.
- Keep API access separate from presentation components when endpoints are
  added.
- Always show understandable loading, empty, and error states for API requests.
- Keep the interface keyboard accessible and use semantic HTML.

## Dependencies and verification

- Suggestions and recommendations for packages or software are allowed, but a
  suggestion is never authorization to download or install it.
- Before downloading or installing any package, dependency, runtime,
  application, or other software, explain the exact item, source, purpose,
  expected system or project changes, and whether administrator access is
  required. Then stop and request explicit user input and approval.
- Require that explicit approval even when the item is already declared in a
  manifest or a task broadly requests environment setup. Approval is limited to
  the exact download or installation described; do not expand its scope.
- Never use `sudo` automatically. If elevation is required, explain why and
  request explicit user approval. Never bypass operating-system security or a
  managed-computer policy.
- Add or update tests with behavior changes when a test setup exists.
- Run the narrowest relevant checks before broader test or build commands.
- Record checks that were run, and any checks that could not be run, in the
  completion summary.

## Cross-thread handoffs

- Create `handoffs/current.md` only when unfinished work must continue in a
  different thread.
- Base it on `handoffs/create-handoff.md` and include the objective, current
  state, files changed, verification, blockers, and one exact next action.
- While `handoffs/current.md` exists, update it after every relevant prompt or
  major change. A relevant prompt changes the objective, constraints, verified
  state, files, blockers, or next action.
- Also refresh the active handoff after material verification results and before
  ending unfinished work or moving it to another thread. Include when it was
  last updated, when its claims were last verified, and what triggered the
  update.
- The agent making a relevant change is responsible for updating the handoff
  before replying. Treat the handoff as a maintained snapshot, not an automatic
  real-time feed, and never claim it is current without checking it.
- Do not put secrets, tokens, or machine-specific credentials in a handoff.
- Update durable documentation before deleting a completed handoff.
