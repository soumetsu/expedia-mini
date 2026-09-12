# Expedia-Mini

Expedia-Mini is a small full-stack travel application for searching the
supplied hotel trips and, in later iterations, managing bookings. The project
uses a FastAPI backend, a Vue frontend, and the fictional classroom data in
`expedia-lite-data/`.

## Project layout

```text
.
|-- backend/              FastAPI application
|   |-- app/
|   |   |-- csv_data.py
|   |   |-- main.py
|   |   |-- models.py
|   |   |-- routes.py
|   |   `-- search.py
|   |-- tests/            Backend unittest suite
|   `-- requirements.txt
|-- frontend/             Vue 3 application powered by Vite
|   |-- src/
|   |   |-- components/
|   |   |   |-- HotelResultsTable.vue
|   |   |   `-- HotelSearchForm.vue
|   |   |-- services/
|   |   |   `-- api.js
|   |   |-- App.vue
|   |   |-- main.js
|   |   `-- style.css
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js
|-- docs/
|   |-- screenshots/part1/ Part 1 browser evidence
|   |-- design.md
|   `-- verification.md
|-- prompts/
|   |-- 01-project-setup-and-development.md
|   |-- 02-complete-project-local-environments.md
|   |-- 03-part-1-backend-csv-search.md
|   `-- 04-part-1-frontend-csv-search.md
|-- handoffs/
|   |-- create-handoff.md
|   `-- current.md
|-- expedia-lite-data/    Supplied fictional CSV data
|-- AGENTS.md             Project working rules
`-- report.md             Part 1 submission report
```

`handoffs/current.md` is the maintained continuation snapshot for a new task.

## Verified local environment

- Python 3.13.15 in `backend/.venv/`
- FastAPI 0.141.1 and Uvicorn 0.52.4
- Node.js v24.20.0 and npm 11.19.0
- Vue 3.5.42, Vite 7.3.6, and `@vitejs/plugin-vue` 6.0.8 in
  `frontend/node_modules/`

Do not reinstall a working environment. Agents must obtain explicit approval
before every download or installation; see `AGENTS.md`.

## Run the backend

From the project root:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The project-local environment and requirements are already installed in this
workspace.

## Run and build the frontend

In a second terminal:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Build the production bundle with:

```powershell
cd frontend
npm run build
```

The verified Windows shell does not currently discover `npm` through normal
command lookup. On that machine, use the already-installed executable directly:

```powershell
& 'C:\Users\henry\AppData\Local\Programs\node-v24.20.0-win-x64\npm.cmd' run dev -- --host 127.0.0.1 --port 5173
```

The frontend uses the same-origin `/api` path. During development, Vite proxies
it to `http://127.0.0.1:8000`, so no frontend environment variable is required
for the verified local setup.

## Part 1 behavior

The backend reads the unchanged `hotels.csv` and `trips.csv`, validates their
relationship, and provides:

- `GET /api/health`
- `GET /api/hotels/search?name=<full or partial hotel name>`

Search trims whitespace, ignores capitalization, supports partial hotel-name
matching, and returns one joined row per available stay with dates, calculated
nights, and estimated price. Blank input is rejected by the API.

The Vue interface submits the hotel name, replaces earlier results after each
search, and shows distinct loading, success, empty, validation, and API-error
feedback. It displays hotel name, city/state, stay ID and name, check-in and
check-out dates, nights, nightly rate, and estimated price in a semantic table.
The styling is intentionally minimal for a later design prompt.

`App.vue` owns page state, `HotelSearchForm.vue` owns accessible form behavior,
`HotelResultsTable.vue` owns table presentation, and `services/api.js` owns the
HTTP request and response checks.

## Verification

Run the backend suite from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Run the configured frontend production build from `frontend/`:

```powershell
npm run build
```

No frontend lint or test script is currently configured. Follow
`docs/verification.md` for the integrated API and browser procedure.

## Local URLs

- Frontend: `http://127.0.0.1:5173/`
- Backend health: `http://127.0.0.1:8000/api/health`
- Backend documentation: `http://127.0.0.1:8000/docs`
- Example search:
  `http://127.0.0.1:8000/api/hotels/search?name=hArBoR%20lAnTeRn`

## Current boundary

Official Prompts 01–04 cover setup, project-local environments, the Part 1 CSV
API, and the barebones Vue integration. Booking management, SQLite persistence,
final visual design, authentication, payments, flights, taxes, and live
availability remain outside the implemented Part 1 scope. See
`expedia-lite-data/README.md` for the authoritative data dictionary.

## Working across tasks

Use the numbered files in `prompts/` as the official task record. Before
continuing in another task, verify and refresh `handoffs/current.md` with the
current objective, completed work, evidence, blockers, and one exact next
action. Keep durable decisions in `README.md`, `report.md`, `AGENTS.md`, or
`docs/`, not only in a handoff.
