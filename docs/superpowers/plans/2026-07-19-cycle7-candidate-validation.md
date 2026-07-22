# BandForge Cycle 7: Candidate Comparison and Validator Catalog

## Goal

Make the deterministic generator reviewable as a product workflow by comparing
multiple reproducible candidates and exposing a durable validator catalog with
machine-readable failure examples.

## Scope

- Generate a bounded set of candidates from the same approved source using
  distinct deterministic seeds and the implemented BEGINNER acoustic-pop
  controls.
- Compare candidates by stable identity, lineage, structural validity, and
  hard-finding counts without claiming musical quality or playability.
- Publish the validator rule catalog and representative failure fixtures for
  source locks, rights, schema, timing, range, and polyphony.
- Save a reproducible CLI demo/report and focused tests covering replay,
  comparison, catalog completeness, and failure evidence.

## Explicit exclusions

Playback, audio rendering, musician judgment, scoped regeneration, notation or
packet export, imports, model-assisted planning, learned generation,
evaluation-beta claims, production auth, deployment, and scale readiness remain
later roadmap work. Candidate scores must not be presented as playability or
quality ratings.

## Acceptance gates

1. TDD red tests precede comparison/catalog implementation.
2. Each candidate retains canonical source harmony, immutable version identity,
   rights/provenance lineage, and validator findings.
3. Focused/full pytest, Ruff, semantic OpenAPI validation, and the real Cycle 7
   CLI demo pass.
4. Evidence is saved under `reports/`; README, roadmap, task checklist, cycle
   gate, progress ledger, and parent SDLC log distinguish implementation from
   roadmap behavior.

## Review gates

Use disjoint implementation and verification scopes with a fresh implementer
and fresh reviewer. Any Critical or Important finding blocks the next playback
or regeneration slice until fixed and re-reviewed.
