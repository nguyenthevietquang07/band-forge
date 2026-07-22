# ADR-006: Playback Is Required Symbolic Review

## Status

Accepted.

## Context

Musicians can detect collisions, density, awkward phrasing, and arrangement
shape faster by listening. High-fidelity audio generation would greatly expand
scope and would not improve the editable symbolic source.

## Decision

Provide synchronized MIDI/sample playback for full band and isolated tracks,
including loop, tempo override, count-in, metronome, mute/solo, and notation
cursor. Label it a preview mix. Keep symbolic timing authoritative.

## Alternatives

- Sheet only: rejected because it weakens review and demo value.
- Production audio engine: deferred because it does not serve the MVP's core
  gig-packet workflow.

## Consequences

MIDI/audio export and scheduler correctness require dedicated tests, but the
product avoids audio-model infrastructure and licensing in the critical path.

