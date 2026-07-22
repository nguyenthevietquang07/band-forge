# BandForge Cycle 4: Source-to-Draft Integrity and Structured Editor

## Goal

Make the currently executable structured-source workflow a truthful, replay-safe
contract surface, then put a small usable editor in front of it. The editor
accepts only user-supplied or licensed structured harmony, shows unsupported
bars as findings, lets the user correct them by creating a new immutable source
revision, and exposes explicit approval plus source-harmony locking in the
resulting draft.

## Global constraints

- A song title or metadata lookup never supplies chords or notes.
- Source revisions and arrangement versions are immutable; correction creates a
  new revision and approval is a deliberate transition.
- Canonical musical time remains integer ticks with `ticksPerQuarter = 960`.
- Unsupported chord symbols remain visible as findings and block approval; no
  approximation is allowed.
- The editor scope is one chord per fixed 4/4 bar, `A-G` major/minor key, and a
  user-authored rights attestation. Sections, imports, playback, generation,
  notation, PDF/MIDI export, authentication, and deployment remain excluded.
- Every public mutation used by the editor accepts an idempotency key and
  repeated identical requests return the original result.

## Task 1: Source-to-draft integrity contract

**Scope:** `contracts/openapi.yaml`, `src/bandforge_api/**`,
`src/bandforge_domain/arrangements.py`, `tests/api/**`, `tests/contracts/**`.

Add failing tests first for response-schema conformance, idempotent source
creation/approval/arrangement creation, conflicting-key rejection, stable
document/persisted version IDs, source/song mismatch rollback with no orphan
version, and source read/list data sufficient to rehydrate the editor. Keep
legacy foundation aliases only if existing tests require them; the public
`/v1` editor routes must use the aligned response shapes and common error
envelope. Persist arrangement and initial version atomically and generate their
IDs before constructing the canonical document.

**Acceptance:** focused tests fail before implementation, then full pytest,
Ruff, and semantic OpenAPI validation pass; every executable public response
validates against its committed schema. Do not implement imports, generation,
workers, playback, or exports.

## Task 2: Standalone structured-source editor

**Scope:** new `web/**` only, including frontend-local tests/configuration.

Create a dependency-light desktop-first browser surface with labeled title/key,
one-chord-per-bar inputs, add/remove bar controls, rights attestation, save,
findings tied to bar ordinals, resolve-and-resubmit, approval, and a locked
approved-source summary. Use the public API only; do not duplicate parser or
approval logic in the browser. Show the metadata-only boundary in the UI.

The first-screen demo fixture is an authored `Am | F | Cmaj9#11 | G` chart. The
user sees the third-bar finding, focus moves to that bar, changing it to `C`
creates a new revision, approval succeeds, and the resulting arrangement seed
shows locked source harmony. Include keyboard labels/live status and ensure
finding state is not conveyed by color alone.

**Acceptance:** frontend-local checks plus a real browser/HTTP demo cover the
invalid-to-approved path. The UI must not claim generated parts, notation,
playback, exports, or song-title chord lookup.

## Task 3: Cycle evidence and SDLC closure

**Scope:** new `scripts/**` and `reports/**`; updates only to
`README.md`, `docs/12-foundation-sdlc.md`, `docs/13-cycle-demo-gate.md`,
`docs/09-implementation-roadmap.md`, `tasks/todo.md`,
`.superpowers/sdd/progress.md`, and `portfolio_projects/SDLC_STAGE_LOG.md`.

Add a reproducible live demo runner and machine-readable report using the
authored invalid-then-corrected chart, with request IDs, response statuses,
revision immutability, approval, lock evidence, and idempotent replay checks.
Record exact commands and outcomes, correct stale test counts, mark only this
slice implemented, and leave all later roadmap behavior explicitly pending.

## Review gates

Each task gets a fresh implementer, then a task reviewer with the task brief,
implementer report, and diff package. Critical/Important findings require a
fix and re-review. A broad whole-branch review runs after all three tasks.
