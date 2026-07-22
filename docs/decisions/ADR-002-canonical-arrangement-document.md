# ADR-002: Canonical Versioned ArrangementDocument

## Status

Accepted.

## Context

MusicXML is optimized for notation exchange; MIDI is optimized for timed events.
Neither captures generation controls, locks, roles, player level, findings,
provenance, or candidate lineage.

## Decision

Use a versioned JSON `ArrangementDocument` with integer musical ticks as the
canonical state. Importers normalize into it. MusicXML, MIDI, PDF, SVG, and audio
are derived artifacts. Accepted versions are immutable and hash-addressed.

## Alternatives

- MusicXML as database model: rejected because editing/generation metadata would
  leak into extensions and every operation would manipulate verbose XML.
- MIDI as database model: rejected because notation and harmonic semantics are
  insufficient.

## Consequences

BandForge must maintain import/export adapters and schema migrations, but gains
one auditable contract for generation, playback, validation, and training.

