# Prompt 06 — Demo Authentication and Per-User Search History

## Objective

Extend the SQLite/MVC application with a lightweight demo account flow. Users
can create an account with a unique username and password plus an optional
unique email, sign in, sign out, and view search history belonging only to the
current account. Existing hotel search and booking behavior must continue to
work.

## MVC contracts

- **Model:** Extend the User record with account fields and add a
  `search_history` record related to a user. Store password hashes, never
  plaintext passwords. Preserve the six seeded user IDs and booking references.
- **View:** Keep Vue pages and CSS under `frontend/src/`. Provide separate
  sign-in, create-account, and search-history pages with loading, empty, error,
  and success feedback. Guest search may remain available, but only signed-in
  searches are persisted.
- **Controller:** Keep SQLite access in `backend/app/controllers/database.py`.
  Use an authentication controller for process-local bearer sessions and thin
  FastAPI routes for register, login, session validation, logout, and
  per-user history. Never return password hashes.

## Validation and security boundaries

- Usernames are unique, case-insensitive, and limited to safe 3–32 character
  identifiers.
- Passwords are at least eight characters and are stored as salted PBKDF2
  hashes. Password uniqueness is not required; account identity is the unique
  username (and optional unique email).
- Optional emails may use made-up domains such as `example.test`, but malformed
  addresses and repeated emails are rejected.
- Search-history reads require the current bearer token and filter by its user
  ID. Process-local sessions are intentionally a demo, not production identity
  management.

## Verification

Run the backend unit suite and frontend production build. Verify account
creation, duplicate/invalid validation, login/logout, `/auth/me`, a signed-in
search appearing in `/search-history`, and isolation after switching accounts.
Do not install packages without explicit approval. Do not modify the supplied
CSV files or commit generated databases.
