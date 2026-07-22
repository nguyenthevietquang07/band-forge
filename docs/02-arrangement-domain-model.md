# Arrangement Domain Model

## 1. Canonical Contract

`ArrangementDocument` is the canonical, versioned representation of an
arrangement. It is purpose-built for generation, editing, validation, and
provenance. MusicXML and MIDI are import/export formats because neither alone
captures BandForge controls, locks, findings, generation lineage, player level,
or role assignments.

The machine-readable minimum contract is in
`contracts/arrangement-document.schema.json`. Application code should generate
types from the schema or maintain contract tests proving equivalence.

## 2. Core Aggregate

```text
ArrangementDocument
  identity and schema version
  source references and rights attestation
  global musical settings
  ordered section instances
  canonical measure grid
  harmonic timeline
  track definitions
  note/chord/rest/drum/control events
  arrangement controls and locks
  generation manifest
  validation summary
```

An arrangement is valid only when every section instance resolves to a
contiguous measure range and every track event lies on the same global grid.

## 3. Musical Time

Floating-point seconds are never canonical musical time. Use integer ticks with
`ticksPerQuarter = 960` in the first schema version. Each event has integer
`startTick` and `durationTicks`; each measure records exact start/end ticks.

Reasons:

- 960 divides common binary and triplet subdivisions used by the first styles;
- integer constraints work with deterministic validators and CP-SAT;
- tempo can change without rewriting musical positions;
- MIDI and MusicXML conversions remain explicit.

Humanized playback offsets are separate `performanceOffsetTicks` and
`performanceDurationDeltaTicks` fields. They must never change notation timing
or measure completeness.

## 4. Sections and Form

`sectionDefinitions` describe reusable musical intent (`VERSE`, `CHORUS`,
`BRIDGE`). `sectionInstances` describe ordered appearances (`verse-1`,
`verse-2`) and may override energy, density, endings, and fill policy.

Repeats are expanded in the canonical grid for generation and playback. Export
may compress them back to repeat notation only when the result is unambiguous.
This prevents disagreement between a visual repeat and an actual playback path.

## 5. Harmony

Harmony events contain:

- onset and duration;
- canonical root pitch class and optional bass pitch class;
- quality and extensions in a controlled vocabulary;
- original display symbol;
- optional Roman numeral/function in the current key;
- source confidence and provenance;
- whether the event is locked;
- reharmonization relationship to the source chord.

The display symbol is never parsed repeatedly inside the engine. Importers parse
once into structured harmony and preserve the original string for round trips.
Unknown symbols enter review instead of being silently approximated.

## 6. Tracks and Roles

Each `Track` declares instrument family, transposition, written/sounding range,
maximum practical polyphony, notation preferences, player level, and MIDI
program/channel hints. A `TrackRoleAssignment` applies per section instance.

Supported first-version roles:

- `FOUNDATION`: roots, guide tones, bass motion;
- `PULSE`: timekeeping and groove articulation;
- `COMP`: rhythmic/harmonic comping;
- `PAD`: sustained harmonic bed;
- `MELODY_SUPPORT`: doubles or answers supplied melody;
- `COUNTERLINE`: subordinate melodic motion;
- `FILL`: phrase-ending activity;
- `REST`: deliberate space.

Role is a coordination primitive. For example, two comping instruments can be
allowed only when their register and rhythmic density constraints do not collide.

## 7. Event Variants

Events use a discriminated union:

- `NOTE`: written and sounding pitch, duration, velocity, articulation, tie;
- `CHORD`: ordered voiced pitches plus articulation and guitar/keyboard hint;
- `DRUM_HIT`: normalized kit piece, duration, velocity, optional technique;
- `REST`: explicit structural rest when meaningful for notation/locks;
- `DIRECTION`: dynamics, rehearsal marks, text cues, pedal, style instructions;
- `AUTOMATION`: playback-only volume/pan changes, never printed by default.

Every event has a stable ID. Regeneration outside the selected scope preserves
both content and IDs so the UI can prove what changed.

## 8. Controls and Locks

Controls are captured in the document because they explain output:

- style pack and version;
- tempo, feel, swing ratio;
- global and per-track density;
- section energy curve;
- harmonic adventurousness;
- fill/solo policy;
- player-level profile;
- variation mode and target distance;
- requested candidate count.

Locks can target source harmony, melody, section order, track, section-track
pair, measure range, or event IDs. A lock is a hard constraint. If a requested
operation conflicts with a lock, the API rejects it before scheduling.

## 9. Version and Provenance Model

Every document records:

- `schemaVersion`;
- `arrangementId` and immutable `versionId`;
- `parentVersionId` and optional `derivedFromCandidateId`;
- source revision IDs and SHA-256 hashes;
- creation actor (`USER`, `IMPORTER`, `GENERATOR`, `REPAIRER`);
- generation manifest if generated;
- validation manifest;
- creation timestamp and acceptance status.

The generation manifest contains seed, engine version, model provider/model ID,
prompt/template version, sampler parameters, style-pack version, retrieval item
IDs, requested scope, and fallback path. Secrets and raw provider prompts with
user content are not placed in analytics logs.

## 10. Persistence Model

Recommended relational tables:

| Table | Purpose |
|---|---|
| `workspaces` / `memberships` | tenant and authorization boundary |
| `songs` | stable catalog identity and user metadata |
| `song_sources` | original source objects and rights attestation |
| `source_revisions` | immutable parse/normalization outputs |
| `arrangements` | stable arrangement identity and current pointers |
| `arrangement_versions` | immutable document, hash, status, lineage |
| `generation_jobs` | durable job lifecycle and idempotency |
| `generation_candidates` | rank, score, document/artifact pointers |
| `validation_runs` / `findings` | rules, severities, locations, manifests |
| `artifacts` | object key, hash, size, media type, derivation |
| `setlists` / `setlist_items` | ordered performance packet |
| `audit_events` | security and material workflow events |

Use normalized columns for identifiers, tenant keys, statuses, timestamps, and
query-critical attributes. Store the immutable musical snapshot as `jsonb` plus
a canonical hash. Do not update nested measures in place; create a new version.

## 11. Canonicalization and Hashing

To hash a document:

1. remove transport-only fields and signatures;
2. sort object keys lexicographically;
3. preserve event arrays in musical order;
4. serialize integers without exponent notation and UTF-8 text consistently;
5. hash canonical bytes with SHA-256.

Semantic reproducibility tests compare canonical documents after stripping IDs
and timestamps that are explicitly non-deterministic.

## 12. Schema Evolution

- Additive optional fields are backward compatible.
- Readers reject unknown major schema versions and preserve unknown optional
  extension objects when round-tripping.
- A migration function upgrades old snapshots to the current in-memory model;
  the original object remains immutable.
- A breaking change increments the major schema version and requires an ADR,
  migration fixtures, and export compatibility tests.

