# BandForge Product Specification

Status: proposed for human review  
Date: 2026-07-19  
Owner: Quang Nguyen

## 1. Objective

BandForge reduces the time between "we want to play this" and "every musician
has a usable part." Its primary user is a casual bandleader preparing an open
mic, jam, rehearsal, church/community performance, or small gig without a
dedicated arranger.

The product converts incomplete but legitimate source material into a shared
arrangement and role-specific packet. It coordinates drums, bass, guitar,
keyboard, and an optional lead instrument around one bar grid, then helps the
human review, revise, hear, and export the result.

The central promise is:

> Bring the music you have. Leave with a band-ready plan everyone can play.

## 2. Decisions Already Accepted

- The gig-preparation product is the primary product; solo-improvisation
  practice is a possible later module.
- A song name is useful metadata but not enough musical input to generate a
  trustworthy arrangement.
- The system accepts chords, structured forms, ChordPro-like text, MusicXML,
  MIDI, PDF, and images at different confidence levels.
- Generated parts must support one another and respect instrument role,
  register, rhythmic space, harmony, and stated player difficulty.
- Regeneration must produce controlled variation, preserve requested anchors,
  and remain reproducible from a recorded seed.
- Per-instrument and full-band playback is required for review.
- Theory, structural, playability, and output validation are separate from the
  creative generator.

## 3. Assumptions to Review

These assumptions make the first release implementable. A change to one may
alter the architecture or roadmap.

1. The first client is a web application optimized for laptop/tablet use. Mobile
   supports capture, review, and playback, not dense score editing.
2. The first supported notation system is common Western notation with chord
   symbols. Microtonal and non-Western notation are outside the first release.
3. The first supported meters are 4/4, 3/4, and 6/8. Mixed/irregular meters are
   imported and exported later.
4. The first ensemble is drums, electric/acoustic bass, guitar, keyboard, and
   optional monophonic lead. Brass/strings and detailed orchestration come later.
5. The first style packs are acoustic pop, pop-rock, funk-lite, and jazz-lite.
   "Jazz-lite" means practical comping and walking/two-feel options, not an
   expert big-band or bebop arranger.
6. A user confirms they are entitled to upload and arrange the source material.
7. Generated content is private by default and is not used for model training by
   default.
8. English is the first UI language. Lyrics are preserved when supplied but are
   not generated.
9. A public beta may use managed infrastructure, but the local development path
   must run without paid APIs or a GPU.

## 4. User Roles

### Bandleader/arranger

Creates songs and setlists, resolves uncertain imports, sets arrangement intent,
generates candidates, accepts edits, and exports the packet.

### Musician

Views their transposed or concert part, plays it back, changes display settings,
and reports an issue. They cannot silently change the shared arrangement.

### Workspace owner

Manages members, retention, training-data consent, and billing when those
features are introduced.

The MVP may implement a single owner account while retaining these authorization
boundaries in the data model.

## 5. Primary Workflow

1. Create a song or select one in a setlist.
2. Choose the source type: chord text, structured chart, MusicXML/MIDI, or
   document/image upload.
3. Parse the source and show confidence, warnings, and unresolved fields.
4. Confirm title, key, meter, tempo, form, chords, melody availability, and
   source rights.
5. Select instruments, player levels, style, density, energy curve, and any
   locked bars or roles.
6. Generate two or three candidates using different seeds under the same
   controls.
7. Run hard validation, repair eligible failures, and rank valid candidates.
8. Review a candidate in synchronized score, chord chart, and playback views.
9. Regenerate or edit only the selected scope: bar, section, instrument, or
   voicing layer.
10. Accept an immutable arrangement version.
11. Export full score, individual parts, chord chart, MusicXML, and MIDI; package
    selected songs into a setlist PDF/ZIP.

## 6. Functional Requirements

### FR-1 Source intake

The system shall accept:

- typed/pasted chord grids and lyrics with inline chords;
- a structured section-and-bar editor;
- `.cho`/ChordPro-compatible text;
- MusicXML `.musicxml`, `.xml`, and compressed `.mxl`;
- Standard MIDI `.mid`/`.midi`;
- PDF, PNG, and JPEG as reference uploads.

Each import creates a source revision with provenance and confidence. Parsed
content never overwrites the original upload.

### FR-2 Source sufficiency

Generation requires an approved harmonic timeline and form. A melody is
optional. Song title, artist, album, ISRC, and streaming identifiers are
metadata and cannot satisfy this gate.

### FR-3 Arrangement controls

The user can set key, tempo, meter, style pack, feel, swing ratio, density,
energy curve, instrumentation, player level per instrument, solo/fill policy,
harmonic adventurousness, and variation mode. The user can lock source chords,
melody, rhythm, bars, or existing tracks.

### FR-4 Candidate generation

Each request generates one to three candidate versions. Every candidate records
its random seed and generation manifest. Re-running with the same manifest must
produce semantically equivalent symbolic output; a new seed must normally
produce a materially different arrangement without violating locks.

### FR-5 Coordinated parts

All parts share the same section, bar, beat, tempo, meter, and harmony timeline.
The engine assigns an explicit musical role to each track by section: foundation,
pulse, comping, pad, counterline, fill, melody support, or rest.

### FR-6 Validation

No candidate enters `READY` while it has a hard structural, range, duration,
polyphony, serialization, or source-lock failure. Warnings remain visible with
bar, track, rule, severity, explanation, and suggested action.

### FR-7 Scoped regeneration

The user can regenerate an instrument, section, or bar range while preserving
everything outside the scope. The request supports modes `SAFE`, `FRESH`,
`REHARMONIZE`, `SIMPLIFY`, and `SPICE_UP`.

### FR-8 Editing and history

Edits create a new draft revision through optimistic concurrency. Accepted and
exported revisions are immutable. The user can compare or restore prior
versions.

### FR-9 Playback

The review surface supports full-band and per-track playback, mute/solo, count
in, metronome, loop range, tempo override, and cursor-following notation. Tempo
override changes playback only until explicitly saved.

### FR-10 Export

Exports include MusicXML 4.0, MIDI type 1, full-score PDF, player PDF, chord
chart PDF, and a setlist ZIP manifest. Export jobs validate their artifacts and
record hashes.

## 7. Non-Functional Requirements

- Availability target for beta API: 99.5% monthly, excluding announced
  maintenance. This is a target, not a claim until measured.
- P95 ordinary API latency below 400 ms, excluding upload and asynchronous jobs.
- A 64-bar, five-part rules-based draft should reach preview in under 20 seconds
  on the reference worker; learned-model targets are measured separately.
- Job progress must survive a page refresh. Queue redelivery must not create a
  duplicate arrangement version or charge.
- A user can delete a workspace and its uploads/derived artifacts under the
  retention policy.
- Every generated result is traceable to input revision, controls, seed, engine,
  style pack, model, and validator versions.
- Core generation and validation run locally on CPU using fixtures; optional
  trained-model inference may use a GPU service.
- The UI meets WCAG 2.2 AA for navigation, forms, contrast, focus, and status
  communication. Musical notation itself requires text alternatives and table
  summaries for critical settings and warnings.

## 8. MVP Scope

The first public demo is complete when it can:

- create a song from a structured chord/form input;
- configure a four-piece band (drums, bass, guitar, keys);
- generate at least two controlled, reproducible arrangements from style rules;
- validate timing, ranges, chord fit, role collisions, and basic playability;
- show a chord chart and basic notation;
- play the full band and isolated tracks;
- regenerate one track or section while preserving locks;
- export valid MusicXML, MIDI, and PDF artifacts;
- demonstrate one successful and one rejected/repair workflow end to end.

## 9. Explicit Non-Goals for MVP

- Fetching official chords, lyrics, melody, or notation from a song title.
- Scraping chord/tab sites or ingesting Spotify content into an AI model.
- Automatic transcription of commercial recordings.
- Reliable handwritten optical music recognition.
- DAW-quality audio production or human-sounding vocals.
- Expert-level orchestration, improvisation coaching, or big-band voicing.
- Real-time multi-user score editing.
- A claim that validation proves artistic quality or universal playability.
- Training a foundation model from scratch.

## 10. Success Metrics

Product metrics for an instrumented beta:

- median time from approved source to first playable candidate;
- percentage of generation jobs yielding at least one hard-valid candidate;
- candidate acceptance rate without regeneration;
- scoped-regeneration success and preservation rate;
- export completion rate;
- validator override rate by rule;
- user-rated usefulness and playability by instrument;
- percentage of first rehearsals requiring major structural correction.

Model metrics do not replace musician review. A launch decision requires both
offline evaluation and structured listening/playability studies.

## 11. Boundaries for Implementers

Always validate source files, preserve provenance, use versioned contracts, run
hard validators, and maintain immutable accepted revisions.

Ask the owner before changing the canonical schema incompatibly, adding a paid
model/API, enabling user data for training, adding a dataset, changing retention,
or launching a public song-library integration.

Never commit secrets, scrape unlicensed charts, train on Spotify content, hide
validator failures, overwrite accepted music, or claim guarantees unsupported
by measured evidence.

## 12. Acceptance Gate

Implementation planning starts after the owner accepts the assumptions, MVP
boundary, and product promise in this document. Changes after acceptance require
an updated spec and, for expensive decisions, an ADR.

