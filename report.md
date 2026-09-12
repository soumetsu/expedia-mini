# Expedia-Mini — Part 1

## Repository and commit

- Repository: [github.com/soumetsu/expedia-mini](https://github.com/soumetsu/expedia-mini)
- Part 1 implementation commit:
  [`73fee4df1db360c8c8506f5df5b4d56dbdc060e0`](https://github.com/soumetsu/expedia-mini/commit/73fee4df1db360c8c8506f5df5b4d56dbdc060e0)

## Implementation

Expedia-Mini is a Vue 3 and FastAPI application for searching the supplied
fictional hotel stays. The backend provides a health endpoint and a hotel-name
search endpoint under `/api`. Search is case-insensitive, accepts full or
partial names, trims whitespace, and rejects blank input.

The backend reads the unchanged `hotels.csv` and `trips.csv` files, joins stays
to hotels through `hotel_id`, and calculates the number of nights and estimated
stay price. The browser receives a structured API response; it does not read
the CSV files directly.

The Vue interface supports keyboard and button submission and gives clear
loading, validation, no-results, success, and API-error feedback. Results show
the hotel, location, stay details, dates, nightly rate, and estimated price in
an accessible table that can scroll horizontally on narrow screens.

## Verification

The following checks were completed with automated commands and browser
control. They do not represent manual user or developer review.

- All 12 backend `unittest` tests passed.
- The Vue production build passed with 13 modules transformed.
- `/api/health` returned HTTP 200 with `{"status":"ok"}`.
- A mixed-case search for `hArBoR lAnTeRn` returned the expected T001 and T009
  stays. An unknown name returned an empty result, and blank API input was
  rejected.
- Browser checks confirmed blank-input validation, Enter and button submission,
  correct result replacement, useful API-error feedback, and a usable 375×700
  layout.
- The final browser run had no unexpected warnings or errors.
- The Part 1 implementation commit was published to the repository above.

No frontend lint or automated frontend test script is currently configured.

### Automated browser evidence

![Successful Harbor Lantern search](docs/screenshots/part1/hotel-search-success.png)

![No-results search](docs/screenshots/part1/hotel-search-no-results.png)

![Narrow viewport with horizontally scrollable results](docs/screenshots/part1/hotel-search-narrow-viewport.png)

## Project context and next steps

The [README](README.md) explains setup and current behavior. More detailed
technical and test notes remain in [docs/design.md](docs/design.md) and
[docs/verification.md](docs/verification.md).

Part 1 is complete. Final visual design, image selection, SQLite persistence,
and booking management are not implemented. Authentication, payments, flights,
taxes, and live availability are outside the supplied data model.
