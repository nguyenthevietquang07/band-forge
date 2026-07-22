# BandForge Cycle 6: Deterministic Generator Baseline

## Goal

Deliver the first executable arrangement-generation slice from an approved,
source-locked canonical ArrangementDocument. The baseline is deterministic,
seeded, validator-gated, and honest about what it does not prove.

## Scope

- Accept only a canonical source ArrangementDocument with source references,
  rights attestations, an approved source state, and a HARMONY lock.
- Generate deterministic beginner acoustic-pop drums, bass, guitar, and keys
  candidate tracks from the locked harmony using integer ticks.
- Record seed, engine version, style-pack version, validator version, input
  revision set, and provenance on the immutable candidate document.
- Reject source-lock, rights, schema, timing, written/sounding range, and
  polyphony violations as hard findings.
- Provide a reproducible CLI demo and focused domain tests for replay and
  failure paths.

## Explicit exclusions

Playback, audio rendering, playability claims, scoped regeneration, candidate
ranking, notation/MIDI/PDF export, imports, model-assisted or learned
generation, evaluation beta, authentication, deployment, and scale readiness
remain later roadmap work. Unsupported difficulty levels are rejected rather
than represented as implemented behavior.

## Acceptance gates

1. TDD red tests cover the source-only boundary, deterministic replay,
   immutable collision-safe candidate identity, complete lineage persistence,
   schema acceptance, hard validator findings, and unsupported controls.
2. Focused and full pytest, Ruff, and semantic OpenAPI validation pass.
3. `scripts/run_cycle6_demo.py` succeeds and saves evidence under `reports/`.
4. README, roadmap, task checklist, cycle gate, progress ledger, and parent
   SDLC stage log distinguish this implemented baseline from later roadmap work.

## Review gates

Use a fresh implementer followed by a fresh read-only reviewer. Any Critical or
Important finding requires a bounded fix and re-review before Cycle 6 closes.
