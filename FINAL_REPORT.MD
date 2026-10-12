# Expedia-Mini Final Report

Last updated: October 12, 2026

## Project access

- Repository: [github.com/soumetsu/expedia-mini](https://github.com/soumetsu/expedia-mini)
- Assessed implementation branch: `rag_integration`
- Assessed implementation commit: [`72810dc`](https://github.com/soumetsu/expedia-mini/commit/72810dc)
- Backend setup: create or activate `backend/.venv`, install the pinned packages
  from `backend/requirements.txt` when needed, configure the project-root `.env`,
  then run from `backend/`:

  ```powershell
  .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
  ```

- Frontend setup: install the packages declared in `frontend/package-lock.json`
  when needed, then run from `frontend/`:

  ```powershell
  npm run dev -- --host 127.0.0.1 --port 5173
  ```

The `.env` file and its Geoapify and Gemini credentials are local-only and must
not be committed. Full startup, endpoint, and configuration details are in
[README.md](README.md).

## What was added and changed

Expedia-Mini now combines a live hotel-discovery interface with a separate
fictional classroom booking workflow.

- A five-digit U.S. ZIP search resolves the ZIP through Geoapify and searches
  its boundary first, then the first populated 5-, 15-, or 30-mile radius.
- Live hotel cards and the Leaflet map share selection state and show provider
  place details, distance, search scope, and a Google Maps address link.
- Selected provider hotels can be saved to SQLite with their ZIP/search context.
  Saving is idempotent; removing a hotel transactionally removes only its local
  associations and fictional demo nights.
- Local saved results and live API results are labeled separately. Fictional
  October 10–14, 2026 rates and room counts are never presented as live data.
- The original classroom catalog supports deterministic recommendations,
  simulated booking creation, history, cancellation while retaining the record,
  and deletion of test bookings.
- Demo accounts use hashed passwords and process-local bearer sessions.
  Search history is persisted and filtered by the authenticated user.
- A bottom-right support chatbot opens as a compact desktop panel and can be
  expanded. Vue sends bounded conversation history only to FastAPI; the Gemini
  API key stays on the backend.
- The chatbot uses `gemini-3.5-flash-lite`, shows the model in its header, and
  displays Gemini-reported input, output, and total token counts when supplied.
  It includes pending, sanitized error, retry, close, restore, keyboard, and
  narrow-screen states.
- The chatbot is product support only. SQL generation and RAG are not presented
  as implemented.

The implementation preserves MVC boundaries: Pydantic/entity definitions are
under `backend/app/models/`, database and provider workflows are under
`backend/app/controllers/`, FastAPI routes remain HTTP adapters, and Vue owns
the view while `frontend/src/services/api.js` owns browser API requests.

## Research notes and design decisions

Sources consulted included the supplied CSV/data documentation, the existing
Expedia reference screenshots in `docs/`, Leaflet 1.9.4 documentation,
Geoapify API documentation, Vue 3 and FastAPI documentation, and the official
[Gemini Generate Content API reference](https://ai.google.dev/api/generate-content)
for response and token-usage metadata.

Useful observed patterns were ZIP-first hotel discovery, synchronized map/list
selection, a fixed help launcher, a compact desktop conversation window, and an
optional expanded chat view. Problematic or unsupported ideas included treating
nearby results as inside the requested ZIP, presenting fictional price or room
data as provider facts, exposing credentials to Vue, and allowing arbitrary
model-generated SQL. These observations produced the boundary-first/radius
fallback, explicit data-source labels, backend-only credentials, read-only
provider calls, and support-only chatbot scope.

## Early design evidence

The repository contains the early Expedia reference captures
[expediaFrontPage.png](docs/expediaFrontPage.png) and
[expediaFlights.png](docs/expediaFlights.png). The implemented design changed
into a smaller assignment-focused Vue interface with explicit live-versus-demo
labels, synchronized map/cards, and a compact support widget.

A separate pre-implementation wireframe or mockup was not saved in the
repository. That remains an evidence gap and should not be represented as
completed.

## Screen-recorded demonstration

- [API Hotel Search implementation recording](https://drive.google.com/file/d/1RE18yXONS_yBIjWmDBg6zdNJDlAgtJaS/view?usp=drive_link)

The existing link documents the Assignment 2.1 search work. A recording that
also covers the saved-hotel lifecycle and Gemini chatbot has not been linked and
remains a submission gap.

## Verification record

| Area | Input or action | Expected | Observed | Correction or limitation |
| --- | --- | --- | --- | --- |
| Backend regression | Run `python -m unittest discover -s tests` from `backend/` | All contracts and workflows pass | 61 tests passed on October 12, 2026 | No automated browser-component suite is configured |
| Frontend build | Run `npm run build` from `frontend/` | Production bundle builds | 26 modules transformed successfully on October 12, 2026 | Existing installed Node/Vite toolchain required |
| Live ZIP search | Search ZIP `10036` on October 1, 2026 | Local saved subset first; live fallback when empty | Empty local subset fell through to 16 then-current Geoapify records with API labels and synchronized map | Geoapify results and counts can change |
| Radius fallback | Search ZIP `16802` | Boundary first, then nearest populated radius | Live response reported a populated 5-mile expanded radius during review | Provider coverage is not guaranteed |
| Saved hotels | Add, refresh, and remove a provider hotel in temporary-database tests | Idempotent save, preserved edits, scoped transactional delete | Tests passed without changing Assignment 1 rows | Rates and rooms are explicitly fictional |
| Chat success | Submit `What can this app help me do?` | Browser calls `/api/chat`; response returns through FastAPI | HTTP 200 reply rendered with `160 input + 149 output = 309 total` provider-reported tokens | Token counts vary by conversation |
| Chat provider load | Repeat requests while Gemini is under load | No secret details; retryable failure | Gemini 503 was retried once, mapped to sanitized 502, and displayed as a retryable UI error | External model capacity remains variable |
| Secret boundary | Inspect request contract and mocked controller call | Browser request contains message/history only; key remains backend-side | Tests confirmed the key is sent only in the backend `x-goog-api-key` header and not the provider URL | Native browser Network-panel capture is not saved |
| Formatting | Run `git diff --check` | No whitespace errors | Passed; Git reported only LF/CRLF conversion notices | Line-ending notices are environment-specific |

Manual review also covered the applicable user-facing portions: local-first ZIP
behavior, saved/API labels, Add/Remove controls, refreshed results, synchronized
list/map selection, responsive layout, simulated-data disclosures, compact and
expanded chatbot modes, the model label, and per-reply usage display.

Part 2 does not currently include a standalone fixed JSON sample. Repeatable
checks instead use deterministic fixtures in `backend/tests/test_database.py`
and mocked provider payloads in `backend/tests/test_chat.py`. A separately
linked fixed JSON file remains a submission gap.

Detailed repeat instructions are in [docs/verification.md](docs/verification.md).

## AI disclosure and evidence log

- **OpenAI Codex, GPT-5:** repository inspection, focused edits, test execution,
  browser verification, documentation condensation, and Git preparation.
- **Google Gemini API, `gemini-3.5-flash-lite`:** runtime model used by the
  implemented support chatbot. It was not given direct database access and does
  not execute SQL.

Selected prompt-to-change evidence:

- “User question → LLM proposes SQL ... backend validates and executes a
  read-only local query ...” informed the documented future RAG direction, but
  the later instruction “Implement only the support/chatbot” limited this
  milestone to [chat.py](backend/app/controllers/chat.py),
  [routes.py](backend/app/routes.py), and
  [ChatbotWidget.vue](frontend/src/components/ChatbotWidget.vue).
- “The frontend should call your application, with no API key included in the
  request” led to the `/api/chat` proxy contract and backend-only key header,
  verified in [test_chat.py](backend/tests/test_chat.py).
- “Add here: The model being used” led to the visible model label and optional
  provider-reported token metric in the chatbot component and response schema.
- A revised approach is recorded by the live Gemini 503 result. The first
  implementation surfaced a generic provider failure; it was revised to retry
  one transient 429/5xx response, preserve a sanitized frontend error, and omit
  failed user messages from later model history.

No full chat export is required. The linked source, tests, verification record,
and selected excerpts identify the material AI-assisted decisions and changes.

## Remaining limitations

Production authentication, payments, taxes and fees, live prices and room
inventory, ratings, reviews, amenities, transportation bundles, personalized
ranking, arbitrary availability, SQL/RAG chat, and real booking are outside the
implemented scope. Live provider results may change. The early mockup, expanded
demo recording, and standalone fixed Part 2 JSON sample remain evidence gaps.
