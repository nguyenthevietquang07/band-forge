# BandForge Cycle 8: MIDI Artifact and Scoped-Regeneration Integrity

## Goal

Add the first artifact-level slice of the playback/regeneration milestone:
export a validated dependency-free MIDI type-1 file from a canonical candidate
and create an immutable scoped regeneration that changes only the selected
track/measure events.

## Scope

- Export canonical candidate tempo, harmony, and generated note/drum events to
  a deterministic Standard MIDI File type 1 with a format/header validator.
- Reject non-accepted or schema-invalid candidates and preserve source rights
  and provenance in an artifact manifest.
- Regenerate a bounded `trackIds` + `measureIds` scope using deterministic seed
  and explicit mode (`SAFE` only in this slice), preserving all IDs/hashes and
  event content outside the scope.
- Produce a diff/manifest with parent version, new immutable version, scope,
  seed, mode, and exact preservation proof.
- Save a real CLI demo and evidence report.

## Explicit exclusions

Browser audio playback, mute/solo controls, loop/metronome/count-in UI, job
cancellation/reconnect, FRESH/SIMPLIFY/SPICE_UP modes, MusicXML/notation/PDF
packets, imports, model planning, learned generation, evaluation beta,
deployment, and scale readiness remain later roadmap work. A MIDI file and
parser validation do not claim that musicians find an arrangement playable.

## Acceptance gates

1. TDD red tests cover MIDI header/event validation, source/rights/schema gates,
   deterministic bytes, scoped replacement, immutable IDs, and outside-scope
   preservation.
2. Focused/full pytest, Ruff, semantic OpenAPI validation, and a real CLI demo
   pass; the demo writes a `.mid` artifact, manifest, and report.
3. README, roadmap, cycle gate, task checklist, progress ledger, and parent
   SDLC log distinguish this artifact/integrity slice from browser playback and
   later modes.

## Review gates

Use a fresh implementer and fresh task reviewer. Any Critical or Important
finding blocks the next notation/packet slice until fixed and re-reviewed.
