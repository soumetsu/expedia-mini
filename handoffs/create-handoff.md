# Create a Cross-Thread Handoff

Use this template only when unfinished work needs to continue in another
thread. Save the completed copy as `handoffs/current.md`. Keep it concise,
specific, and verifiable; never include secrets or credentials. While the file
is active, refresh it after every relevant prompt, major change, or material
verification result and before unfinished work moves to another thread.

---

# Current Handoff

## Handoff status

- Last updated: `[YYYY-MM-DD HH:MM timezone]`
- Claims last verified: `[YYYY-MM-DD HH:MM timezone]`
- Update trigger: `[relevant prompt, major change, verification, or transfer]`

## Objective

State the requested outcome and the boundary of the task.

## Current state

Summarize what works now and what remains unfinished. Distinguish verified facts
from assumptions.

## Files changed

List relevant paths and briefly state why each changed. Note unrelated existing
changes that must be preserved.

## Verification

List each command or manual check already run and its result. Record checks that
could not run and why.

## Decisions and constraints

Capture decisions that affect the next thread, explicit user constraints, and
links to relevant durable documentation. Include download, installation,
elevation, and approval restrictions that affect the next action.

## Blockers or risks

Describe unresolved errors, missing access, required user choices, or risky
areas. Write `None` when there are none.

## Exact next action

Give one concrete first action for the next thread, followed by any remaining
steps in priority order.

---

After the new thread incorporates the handoff, move durable information into
`README.md`, `report.md`, `docs/`, or `AGENTS.md`, then remove
`handoffs/current.md`.
