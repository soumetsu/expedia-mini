# Expedia-Mini — Part 1

## Repository and commit

- Repository: [github.com/soumetsu/expedia-mini](https://github.com/soumetsu/expedia-mini)
- Published Part 1 implementation commit:
  [`73fee4df1db360c8c8506f5df5b4d56dbdc060e0`](https://github.com/soumetsu/expedia-mini/commit/73fee4df1db360c8c8506f5df5b4d56dbdc060e0)

The persistence and booking milestone described below is present in the working
tree; no later commit identifier is claimed here.

## Implementation

Expedia-Mini is a responsive Vue 3 and FastAPI application for searching the
supplied fictional stays and managing simulated bookings. Search accepts a
city, state, or hotel name and optional check-in/check-out dates. Because the
source data describes fixed trips, the date fields narrow the existing catalog
rather than suggesting arbitrary room availability.

Search results now appear above the recommendation section as scannable cards
with stay dates, length, nightly price, estimated total, and a booking action.
The main location control remains visually primary; dates and the demo-user
selector are secondary. A separate `/bookings` page presents booking history,
confirmed/cancelled status, cancellation that retains the record, and a
two-step delete control for user-created test bookings. Seeded examples remain
protected from deletion.

SQLite persistence is implemented with Python's standard-library `sqlite3`.
The backend creates the schema and imports the unchanged hotel, trip, user, and
booking CSV rows once. Existing IDs are preserved, new bookings receive a
collision-free ID, and later restarts do not duplicate seeds or restore deleted
records. After the initial import, hotel search, recommendations, demo-user
reads, and booking CRUD all use SQLite. No SQLite package was installed.

The implementation follows MVC responsibilities. Typed entities and Pydantic
contracts are under `backend/app/models/`; SQLite and business controllers are
under `backend/app/controllers/`; Vue pages, components, and CSS form the View.
The suggested folders were placed inside the existing `app` package so the
architecture fits FastAPI's import structure. Thin routes call the controllers
through agreed typed contracts. All user-facing CRUD starts in Vue and travels
through `/api`; the browser never accesses SQLite directly.

Recommendations remain factual and deterministic: one stay per hotel ranked
by estimated total, nightly rate, check-in date, and trip ID. Recent-search
personalization is still explicitly identified as future work.

## Verification

The following checks were completed with automated commands and browser
control; they do not represent manual user or developer review.

- The intended `backend/.venv` interpreter reported Python 3.13.15 and SQLite
  3.50.4. SQLite support was already present, so installation was skipped.
- All 25 backend `unittest` tests passed, including all-four-file model and
  relationship validation, one-time seeding,
  collision-free creation, history/read, cancellation retention, test-booking
  deletion, seed protection, date filtering, search, recommendations, and
  route registration, and proof that search reflects a post-seed SQLite change
  rather than rereading CSV.
- The Vue production build passed with 16 modules transformed. No frontend
  lint or automated frontend test script is configured.
- Browser verification on the local application selected Demo Traveler 6,
  searched New York with a date window, and returned T003 and T004 above the
  recommendation cards.
- The browser created B007 for T003, displayed it on the separate history page,
  changed its status from confirmed to cancelled while retaining it, and
  displayed the two-step delete confirmation. The exact temporary B007 record
  was then deleted through the API for cleanup, and U006 history returned an
  empty list.
- The production build was rerun after the final display-name/status correction
  and passed. Both development servers remained reachable afterward.

### Existing automated browser evidence

![Successful hotel search](docs/screenshots/part1/hotel-search-success.png)

![No-results search](docs/screenshots/part1/hotel-search-no-results.png)

![Narrow viewport search](docs/screenshots/part1/hotel-search-narrow-viewport.png)

## Project context and next steps

The [README](README.md) contains run commands, endpoints, current behavior, and
data boundaries. [docs/design.md](docs/design.md) records the architecture, and
[docs/verification.md](docs/verification.md) provides repeatable checks.

Authentication, payments, arbitrary availability, rooms, occupancy, amenities,
reviews, taxes, live demand, transportation bundles, and dynamic pricing are
outside the current implementation. Demo authentication and transparent
travel-domain pricing logic remain lower priority. Battery state and device type
must not affect price.
