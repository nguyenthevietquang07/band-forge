# Architecture

## System shape

```text
Browser editor -> FastAPI boundary -> domain services -> SQLite repository
                                      |                  |
                                      v                  v
                           ArrangementDocument       immutable revisions
                                      |
                                      v
                 validator-gated candidate -> MIDI / MusicXML / packet / playback plan
```

The project is deliberately a modular monolith. The browser editor is a
dependency-free static application; the Python API is the boundary for
untrusted input; domain modules hold chart normalization, generation,
validation, playback planning, regeneration, and exports.

## Core decisions

- **Canonical state:** `ArrangementDocument` is the single source of truth;
  MIDI, MusicXML, printable HTML, and ZIP packets are derived artifacts.
- **Immutable workflow:** source revisions, arrangement versions, candidate
  identities, provenance, and generation lineage are preserved rather than
  overwritten.
- **Rights boundary:** only authored or licensed musical material supplies
  notes/chords. Title and streaming metadata are metadata only.
- **Deterministic baseline first:** seeded rules generate four coordinated
  tracks before any model-assisted approach is considered.
- **Hard gates before playback/export:** invalid schema, timing, source locks,
  rights, range, and polyphony block acceptance.
- **Scoped change safety:** `SAFE` regeneration creates a new version and
  preserves outside-scope content hashes and event IDs.

## Repository guide

| Path | Responsibility |
|---|---|
| `web/` | Editor and local Web Audio playback controls |
| `src/bandforge_api/` | FastAPI routes, persistence boundary, service orchestration |
| `src/bandforge_domain/` | Canonical document, generator, validators, playback, and exporters |
| `contracts/` | OpenAPI and ArrangementDocument schemas |
| `tests/` | API, contract, domain, and static-editor regression coverage |
| `scripts/` | Reproducible HTTP and domain demos |
