# Expedia-Mini Final Report

October 8th

Video demonstration for assignment 2.2: https://drive.google.com/file/d/1-9DexVkkuqMScmwMfjHwGXm6_Sdx9NDg/view?usp=drive_link

Status: final implementation draft; the new demo-video link and final pushed commit are still pending.

## Project access

- Repository: [github.com/soumetsu/expedia-mini](https://github.com/soumetsu/expedia-mini)
- Branch: `rag_integration`
- Last published commit: [`2643f66`](https://github.com/soumetsu/expedia-mini/commit/2643f66)
- SQL-grounded assistant implementation commit: `35e00b3`

Kept project-root `.env` local and uncommitted. It supplies the Geoapify and Gemini keys; the browser never receives the Gemini key. Gemini runs flash-mini, and has a fallback model.

```powershell
# Backend
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend, in a second terminal
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

## Implemented and revised

I preserved the Part 1 ZIP search, map/list behavior, local saved-hotel controls, SQLite persistence, demo authentication, booking lifecycle, and labeled simulated nightly data. (All, excluding the mock hotels and in class assignments,) I then added a compact, expandable support chatbot that calls FastAPI rather than Gemini directly.

Revisions made:

- Replaced the general support-only answer path with a two-request SQL RAG workflow for saved-hotel questions.
- Documented the real columns and both `hotel_id` joins, which the backend loads at startup.
- Restricted model-proposed SQL to one bounded, read-only `SELECT` over `saved_hotels`, `saved_hotel_zips`, and `demo_hotel_nights`.
- Added separate conversation messages and trace records for generated SQL, executed SQL, result summaries, and errors.
- Added loading, failure, no-match, model, token-usage, retrieval-path, checked-SQL, and retrieved-record states to the chatbot.This can be seen on the front-end at the bottom of the chat. Mainly used for demonstration/debugging.
- Clarified throughout the interface that rates and availability are simulated course data and that a missing date row means availability is unknown.
- For Gemini reliability, I had to set up billing, add retries, and configure flash lite from gemini as a fallback model.

FLOW FOR RAG:

User question -> Gemini proposes SQL from the approved schema and rules -> the backend validates and executes a read-only SQLite query -> the original question and retrieved rows go to Gemini -> the frontend displays a grounded answer.


## Research and design decisions

Implemented these throughout the project.
 [Geoapify](https://apidocs.geoapify.com/), [Leaflet](https://leafletjs.com/reference.html), [Vue 3](https://vuejs.org/guide/introduction.html), [FastAPI](https://fastapi.tiangolo.com/), and the [Gemini Generate Content API](https://ai.google.dev/api/generate-content).

The useful patterns were ZIP-first discovery, linked map/card selection, a fixed chat launcher, a compact desktop chat window, and an optional expanded view. The problematic patterns were treating nearby results as inside a ZIP, presenting demo prices as live facts, exposing an API key to Vue, and trusting arbitrary generated SQL. I therefore used explicit source labels, backend-only credentials, a table allowlist, a read-only connection, a row cap, and a query timeout.

Researched similar travel websites, annotated and used Expedia.

- [Search results, filters, and first property](docs/screenshots/research/expedia-times-square-search-results-2026-10-13.jpg)
- [Property cards, ratings, nightly price, and total](docs/screenshots/research/expedia-times-square-result-cards-2026-10-13.jpg)

## Early design and changes

The repository contains the early visual references [expediaFrontPage.png](docs/expediaFrontPage.png) and [expediaFlights.png](docs/expediaFlights.png). My first chatbot interface is also recorded in the [compact before-state](docs/screenshots/part2/04-current-chatbot-rag-gap.png) and [expanded before-state](docs/screenshots/part2/05-expanded-chatbot.png).

Changed that first interface by adding the active model, token usage, an SQL-backed versus support-only label, and expandable technical evidence. I also kept the widget compact by default on desktop and made expansion optional, but not the default state.

Little front end was developed (or needed to be developed, other than the chatbot window).

## Final interface evidence

- [Part 1 search and booking foundation](docs/screenshots/part2/01-foundation-overview.png)
- [Live search, map, and local controls](docs/screenshots/part2/02-live-search-local-controls.png)
- [Saved hotels and simulated nights](docs/screenshots/part2/03-saved-hotels-simulated-nights.png)
- [Final grounded answer](docs/screenshots/part2/08-final-rag-answer.png)
- [Final generated and checked SQL](docs/screenshots/part2/09-final-rag-sql-evidence.png)
- [Final retrieved SQLite records](docs/screenshots/part2/10-final-rag-records.png)

-[Final grounded answer](docs/screenshots/part2/08-final-rag-answer.png)
-[Final generated and checked SQL](docs/screenshots/part2/09-final-rag-sql-evidence.png)
-[Final retrieved records](docs/screenshots/part2/10-final-rag-records.png)

## Complete RAG checkpoint

User question: “What are the three cheapest available saved hotels near ZIP 16803 for October 11, 2026?”

Gemini generated a query of:

```sql
SELECT sh.name, sz.distance_miles, dn.stay_date,
       dn.nightly_rate_cents / 100.0 AS nightly_rate_usd,
       dn.rooms_available
FROM saved_hotels AS sh
JOIN saved_hotel_zips AS sz ON sz.hotel_id = sh.hotel_id
JOIN demo_hotel_nights AS dn ON dn.hotel_id = sh.hotel_id
WHERE sz.searched_postcode = '16803'
  AND dn.stay_date = '2026-10-11'
  AND dn.rooms_available > 0
ORDER BY dn.nightly_rate_cents ASC, sh.name ASC
LIMIT 3;
```

The first join connects saved hotels to the ZIP context. The second connects those hotels to dated demo rates and room counts. The backend checked the statement, ran it read-only, and returned fixed simulated records (default $100 per night).



The second Gemini request used only the question and checked rows. The displayed answer named the three hotels, date, rates, availability, and simulated-data limitation. This was not a regular Geoapify search; but a query generated by Gemini.


## Verification record

| Check | Expected | Observed |
| --- | --- | --- |
| Backend regression | Existing and RAG behavior passes | 65 tests passed in 60.087 seconds on October 13, 2026 |
| Frontend build | Vue production bundle builds | 26 modules transformed in 3.05 seconds |
| Live ZIP search | ZIP `16802` uses saved data first, then live fallback | On October 13, 2026, the empty saved subset fell through to 20 then-current Geoapify results in the first populated 5-mile radius |
| Successful RAG question | Two joins retrieve three available hotels and produce a grounded reply | The final browser check returned the three SQLite records and displayed the answer shown above |
| Empty result | The answer acknowledges insufficient saved data | Mocked empty-row and manual no-match checks returned an explicit no-match response without invented hotels |
| Unsafe SQL | A write, unapproved table, or multiple statements cannot run | Automated checks rejected `DELETE`, a `users` read, and a multi-statement query before any database change |
| Secret boundary | Frontend calls this application without a provider key | The browser request contained the message/history only; Gemini credentials remained in the backend |

I also manually checked the most applicable user-facing behavior: Add/Remove Local, saved-versus-live labels, synchronized list/map selection, simulated-data warnings, compact and expanded chatbot states, the model and usage display, the grounded answer, and the expandable SQL/record evidence. Live provider counts can change, and there is no automated Vue component suite.

## Screen-recorded demonstration

- Existing Part 1 recording: https://drive.google.com/file/d/1RE18yXONS_yBIjWmDBg6zdNJDlAgtJaS/view?usp=drive_link
- Final Part 2 RAG recording: https://drive.google.com/file/d/1-9DexVkkuqMScmwMfjHwGXm6_Sdx9NDg/view?usp=drive_link

The final recording still needs to show the checkpoint question, proposed SQL, checked query, retrieved rows, grounded answer, no-match case, and blocked unsafe query.

## AI disclosure and evidence log

- CODEX from openai was used (Sol model 5.6, from light to extra high effort). I used it to inspect the repository, suggest and apply focused code/documentation changes, run tests, and help verify the browser workflow.
- GEMINI FLASH LITE 3.5 was used for the chatbot/RAG (API).The application uses it to propose SQL and generate the grounded answer.
- GEMINI FLASH LITE 3.1 was used only as a fallback.


Selected prompt-to-change evidence:

- “Use the first LLM request to propose SQL ... send the original question and retrieved rows in a second LLM request” led to [chat.py](backend/app/controllers/chat.py), [database.py](backend/app/controllers/database.py), and the visible evidence in [ChatbotWidget.vue](frontend/src/components/ChatbotWidget.vue).
- “Use `prompts/hotel-assistant.md` and load it at backend startup” led to the versioned [assistant prompt](prompts/hotel-assistant.md) and startup load in [main.py](backend/app/main.py).
- “Add here: The model being used” led to the visible model and optional provider-reported usage in [ChatbotWidget.vue](frontend/src/components/ChatbotWidget.vue).
- My first approach was a general support chatbot that did not retrieve SQLite records. I revised it into the two-stage SQL workflow, added backend enforcement, and exposed the checked evidence instead of presenting an ungrounded comparison as complete.

## Remaining limitations

The project does not provide production authentication, payments, taxes/fees, live rates or room inventory, amenities, reviews, flights, cars, packages, or real booking. Gemini and Geoapify availability can vary.

Gemini has a possibility of throwing 502 errors (or similar); had to resolve by adding more credits/a billing plan, as well as a fallback model.
