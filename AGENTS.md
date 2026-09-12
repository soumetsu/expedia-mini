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

## Backend

- Keep FastAPI code under `backend/app/`.
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
