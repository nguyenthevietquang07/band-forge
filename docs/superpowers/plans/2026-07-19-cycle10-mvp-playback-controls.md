# BandForge Cycle 10: MVP MIDI Playback Controls

## Goal

Complete the MVP playback review surface for an accepted canonical candidate:
deterministically build a filtered playback plan and expose a usable local
preview with mute/solo, loop, metronome, count-in, and tempo override controls.

## Scope

- Add a domain playback-plan contract that validates an accepted candidate,
  applies mute/solo and inclusive measure-loop filters, adds metronome/count-in
  click events, and applies a bounded tempo override without changing the
  canonical document.
- Add accessible controls to the existing first screen for local preview:
  play/stop, per-track mute/solo, loop measure range, metronome, count-in, and
  tempo override.
- Use the browser Web Audio API only to preview the already-built deterministic
  plan; keep the canonical MIDI artifact/export as the traceable source.
- Add static UI tests, domain tests, and a reproducible demo/evidence report
  showing the plan transformations and control state.

## Explicit exclusions

Hosted audio, private beta, auth/deployment, job cancellation/reconnect,
real-time collaboration, player-specific engraving, imports, models, learned
generation, evaluation beta, and scale readiness remain out of scope. Browser
automation is attempted if available; static/HTTP evidence must state its
availability honestly.

## Acceptance gates

1. TDD red tests cover accepted/schema/rights gates, mute/solo precedence,
   loop boundaries, tempo bounds, metronome/count-in events, and immutable
   source input. Static UI tests cover every required control and no metadata
   music lookup.
2. Focused/full pytest, Ruff, semantic OpenAPI validation, and a real local
   demo pass. Evidence records controls and plan counts; it does not claim
   browser automation if unavailable.
3. README, roadmap, cycle gate, task checklist, progress ledger, and parent
   SDLC log close only the MVP playback-control slice and list later work.

## Review gates

Fresh implementation and task review precede a final broad MVP review.

## Post-closure defect checklist (2026-07-22)

- [x] Rendered controls send canonical underscore track IDs.
- [x] Each generated role uses a distinct bounded preview voice and velocity.
- [x] Mute/solo changes while already playing automatically apply through a
  fresh canonical playback plan.
- [x] Isolated Chrome observes each role together/solo/muted and actual
  oscillator starts with no source-guide events or console problems.
- [x] Focused/full tests, lint, contract validation, syntax, saved evidence,
  and fresh CLEAN review pass.

## Post-closure acoustic/overlap checklist (2026-07-22)

- [x] Reproduce stale playback requests and incomplete recursive-timer cleanup.
- [x] Reject stale sessions, abort in-flight plans, clear all timers, and cancel
  every scheduled sample envelope on Stop/replay.
- [x] Replace generated-role oscillators with pinned local CC BY 3.0 FluidR3
  acoustic samples using the MIT `webaudiofontplayer@1.0.3` runtime.
- [x] Expand deterministic drums with open hat, crash, and tom-fill events plus
  General MIDI playback mappings.
- [x] Verify all-together, every mute/solo, Stop cancellation, exact non-stacked
  rapid replay, sample starts, and a clean console in isolated Chrome.
- [x] Save evidence and retain explicit no-professional-quality/no-model claim
  boundaries.
