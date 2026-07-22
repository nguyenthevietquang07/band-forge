# BandForge Cycle 9: MusicXML and Player-Packet Integrity

## Goal

Add a deterministic notation artifact and a traceable player-packet ZIP from an
accepted canonical candidate, with dependency-free XML/ZIP smoke validation.

## Scope

- Export a bounded MusicXML 4.0 `score-partwise` document from the canonical
  measures, locked harmony, and generated tracks.
- Preserve source revision IDs, accepted version ID, rights attestation, and
  generation lineage in a machine-readable artifact manifest.
- Validate XML structure, divisions/ticks, part/measure identity, non-empty
  content, and no overflow against the canonical document.
- Build a deterministic ZIP packet containing MusicXML and manifest files;
  validate names, hashes, traceability, and safe source rights.
- Save a real CLI demo and evidence report.

## Explicit exclusions

OpenSheetMusicDisplay/browser rendering, visual regression, PDF generation,
transposition/player-specific engraving, signed downloads, imports, model
planning, evaluation beta, deployment, and scale readiness remain later work.
The artifact and XML smoke checks do not claim readable engraving or
playability.

## Acceptance gates

1. TDD red tests cover accepted/schema/rights gates, deterministic XML/ZIP
   bytes, divisions and measure boundaries, malformed XML/packet rejection,
   manifest hashes, and immutable source/version traceability.
2. Focused/full pytest, Ruff, semantic OpenAPI validation, and a real CLI demo
   pass; evidence includes XML/ZIP artifacts and manifest.
3. README, roadmap, cycle gate, task checklist, progress ledger, and parent
   SDLC log distinguish this artifact/interoperability slice from browser
   rendering, PDF, signed downloads, and later packet claims.

## Review gates

Use a fresh implementer and fresh task reviewer. Any Critical or Important
finding blocks import-adapter work until fixed and re-reviewed.
