# Expedia-Mini: 2.1, part 1

## Repository and commit

- Repository: [github.com/soumetsu/expedia-mini](https://github.com/soumetsu/expedia-mini)
- Published Part 1 commit:
  [`73fee4df1db360c8c8506f5df5b4d56dbdc060e0`](https://github.com/soumetsu/expedia-mini/commit/73fee4df1db360c8c8506f5df5b4d56dbdc060e0)
- SQLite, MVC, and booking milestone: `a49e4a8` on `main`
- Earlier completed parts were committed through October 2, 2026.

- Recording of API Hotel Search implementation (Assignment 2.1): https://drive.google.com/file/d/1RE18yXONS_yBIjWmDBg6zdNJDlAgtJaS/view?usp=drive_link

# Research Notes/Notes In General
- Used Leaflet 1.9.4
- Initial behavior of the search was to find hotels within a 5(?) mile radius. This worked as intended, but most apps will show hotels that are the closest, despite being outside of the desired radius. I made a subtle change to include hotels close to the zip code, if there are no hotels within the 5 mile radius (or after the closest results).
- One feature I wanted to add after implementing the search was the ability to open the queried address/hotel in Google Maps, in an external tab.
-



## Implementation

Expedia-Mini is a Vue 3 and FastAPI application with two deliberately separate
experiences. The primary search resolves a five-digit U.S. ZIP through
Geoapify, finds hotels within the postcode or the first populated 5-, 15-, or
30-mile radius, and presents the results in synchronized cards and a Leaflet
map. Provider names, addresses, postcodes, coordinates, and distances are
displayed without inventing prices, reviews, room availability, or booking
status. Each card also offers a keyless Google Maps address link.

The fictional classroom catalog remains a separate booking sandbox. It
supports fixed-date destination search, deterministic recommendations,
simulated booking creation, booking history, cancellation that retains the
record, and deletion of user-created test bookings. Demo accounts use hashed
passwords and process-local bearer sessions; authenticated search history is
stored and filtered by user.

SQLite is initialized from the four unchanged CSV files once. Existing IDs are
preserved, new IDs are collision-free, and subsequent catalog, account,
history, and booking operations use SQLite rather than rereading the CSVs. The
architecture keeps entities and Pydantic contracts in `backend/app/models/`,
database and workflow logic in `backend/app/controllers/`, thin HTTP adapters
in `routes.py`, and the Vue interface under `frontend/src/`.

The latest Assignment 2 work adds local storage for selected Geoapify hotels:

- `saved_hotels` preserves the provider `place_id`, name, address, and
  coordinates.
- `saved_hotel_locations` records the searched ZIP and result context.
- `demo_hotel_nights` stores October 10–14, 2026 classroom rows with clearly
  fictional defaults of $100 per night and 20 rooms.
- Saved-hotel GET, POST, and DELETE routes provide idempotent save and
  transactional removal without changing the Assignment 1 records.
- Vue checks the saved subset first, labels local and provider results
  honestly, preserves card/map selection by provider ID, and uses live
  Geoapify only after a successful empty local response.

The current support milestone adds a bottom-right chatbot that stays compact on
desktop unless the user selects **Expand**. Vue sends bounded conversation data
to FastAPI, and the backend calls `gemini-3.5-flash-lite` without exposing the
API key to the browser. The interface shows conversation, pending, and
retryable error states, identifies the model in its header, and shows Gemini's
per-reply token counts when supplied. This step is support chat only; SQL
generation and RAG remain unimplemented.

##

## Verification

Automated verification for the latest addition included:

- 22 focused database and route tests and the full 54-test backend regression
  suite;
- SQLite integrity `ok`, no foreign-key violations, unchanged Assignment 1
  runtime counts of 8 hotels, 12 trips, 8 users, and 9 bookings, and initially
  empty Assignment 2 tables;
- a successful Vue production build with 25 modules transformed; and
- browser-controlled ZIP `10036` inspection confirming local-first fallback,
  API labels, Add controls, synchronized list/map results, and no console
  warnings or errors.

Earlier verification covered exact-postcode and radius-based live search,
sanitized error responses, responsive layouts, Google Maps link contracts,
booking create/read/cancel/delete with cleanup, authentication, and per-user
search-history isolation. The backend suite and production build are the
repeatable checks; no frontend lint or automated component-test script is
configured.

Per user confirmation, manual spot checks were also completed on the portions
most suited to direct review in the latest addition: the local-first ZIP flow,
API-versus-saved labels, Add/Remove controls, refreshed saved results,
synchronized card/map behavior, responsive presentation, and disclosure that
rates and room counts are simulated classroom data. Schema constraints,
idempotency, and transactional deletion remain supported by the automated
database tests.

The support-chat addition passed its focused mocked tests and the full backend
suite, and the Vue production build completed with 26 modules. Browser review
confirmed compact and expanded desktop modes and a live `/api/chat` HTTP 200
round trip with a rendered Gemini reply. A later provider-capacity check
returned Gemini HTTP 503 `UNAVAILABLE`; the application converted it to a
sanitized 502 and displayed the intended retryable error. A follow-up live HTTP
200 response displayed Gemini's reported 160 input, 149 output, and 309 total
tokens.

### Existing browser evidence

![Successful hotel search](docs/screenshots/part1/hotel-search-success.png)

![No-results search](docs/screenshots/part1/hotel-search-no-results.png)

![Narrow viewport search](docs/screenshots/part1/hotel-search-narrow-viewport.png)

## Project context and next steps

The [README](README.md) contains setup, endpoints, and current behavior.
[docs/design.md](docs/design.md) records the architecture, and
[docs/verification.md](docs/verification.md) contains the repeatable test and
smoke-test procedures.

Production authentication, payments, arbitrary availability, taxes and fees,
amenities, reviews, transportation bundles, and personalized recommendations
remain outside scope. Geoapify results may change over time. Live hotel data
must remain distinct from fictional classroom prices, room counts, and
bookings; battery level or device type must never affect price.
