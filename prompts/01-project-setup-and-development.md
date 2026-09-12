# Project setup and development

Official prompt 1 for **Expedia-Mini**.

## Objective

Inspect the development environment and project organization without replacing
working tools or inventing evidence. FastAPI belongs under `backend/`, and the
Vue application, including `App.vue`, belongs under `frontend/`.

## Environment checkpoint

Confirm:

- which Python interpreter belongs to this project;
- whether FastAPI can be imported;
- the Node.js and npm versions;
- whether the frontend package environment is ready; and
- every file or directory created.

### Check

- Detect the operating system.
- Report every available Python executable, version, and path.
- Treat Python 3.10 or higher as compatible.

### Take action

- If compatible Python already exists, preserve it and do not reinstall it.
- If Python is missing or incompatible, identify the safest supported method
  from an official source.
- Explain the exact download or system change and whether administrator access
  is required, then stop for permission.
- After approval, perform only the approved Python installation when the
  computer permits it.
- Never use `sudo` automatically or bypass a managed-computer policy.

### Verify

- Report the installed Python version and executable path.
- State whether the Python compatibility checkpoint passed.

## Project checkpoint

Confirm that `backend/`, `frontend/`, `docs/`, `handoffs/`, and `prompts/`
exist. Check that:

- `README.md` accurately describes the current setup;
- `AGENTS.md` contains project-specific development and verification rules;
- `docs/design.md` explains frontend, FastAPI, backend, CSV, and future SQLite
  responsibilities;
- `handoffs/current.md` describes the current state and next task;
- the submission report is named exactly `report.md`;
- `report.md` contains the required Part 1 headings without invented evidence;
  and
- `.gitignore` excludes credentials, virtual environments, `node_modules`,
  build output, caches, and runtime database files.

## Allowed corrections

If an existing environment passes a checkpoint, preserve it and do not
reinstall or recreate it. Make only small, evidence-based documentation and
organization corrections: preserve useful content, ensure required context
files exist, correct inaccurate setup information, normalize `report.md`, and
add clearly required generated-file exclusions.

Do not guess the application name or invent setup commands, verification
results, repository URLs, screenshots, or commit hashes.
