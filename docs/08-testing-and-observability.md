# Testing and Observability

## 1. Test Strategy

BandForge requires conventional software tests and music-domain evaluation.
Passing unit tests does not establish musical quality; a listening study does not
establish tenant isolation or exact timing. Keep these evidence classes separate.

## 2. Test Pyramid

### Unit tests

- rational/integer musical time and measure math;
- chord parsing and canonicalization;
- key/transposition and written/sounding pitch;
- section expansion and repeat handling;
- lock/scope intersection;
- style-pattern realization under fixed seeds;
- instrument-range, polyphony, voicing, and difficulty rules;
- candidate distances, score components, and repair patches;
- canonical serialization and hashing.

Use table-driven tests and property-based tests for transposition, timing, and
round-trip invariants.

### Contract tests

- JSON Schema positive and negative fixtures;
- OpenAPI examples and generated client compatibility;
- common API error envelope;
- job/event schema compatibility;
- model gateway response validation;
- third-party metadata adapter shape validation.

### Integration tests

- API + PostgreSQL transaction/version behavior;
- API + Redis/Celery submission, duplicate delivery, lease recovery, and cancel;
- object upload quarantine, hash verification, signed download, and cleanup;
- MusicXML/MIDI import-normalize-export round trips;
- generation to validation to artifact pipeline;
- model timeout/fallback and provider circuit breaker.

Use real PostgreSQL/Redis/object-store containers in integration CI rather than
mocking persistence semantics.

### End-to-end tests

1. Create structured song, approve source, generate two candidates, play preview,
   accept one, export packet.
2. Upload malformed/ambiguous source, resolve findings, then generate.
3. Regenerate chorus guitar only and prove other event hashes/IDs are unchanged.
4. Reject impossible beginner guitar voicing and show actionable finding.
5. Refresh during generation and reconnect to progress/result.
6. Attempt cross-workspace source/artifact access and receive denial.
7. Cancel a running job and verify no published candidate or orphan reference.

### Visual and audio smoke tests

- screenshot score/chord/player layouts at desktop, tablet, and mobile sizes;
- detect blank/overflowing notation and overlapping controls;
- compare selected stable PDF pages to approved visual baselines;
- render MIDI preview and verify non-silent duration, track channels, peak bounds,
  and no hanging notes;
- manual playback review remains part of release evidence.

## 3. Fixture Design

Fixtures are authored or clearly licensed and stored with provenance. Include:

- 1, 4, 16, and 64-bar forms;
- supported meters, pickup measures, tempo changes where supported;
- simple triads through seventh/sus/slash chords;
- every first-release instrument and difficulty;
- dense/sparse texture, unison, rests, fills, melody locks;
- malformed XML/MIDI, oversized event counts, unknown chords, incomplete bars;
- exact expected validator findings by rule ID;
- export golden files with normalized comparison to avoid timestamp noise.

## 4. Determinism Tests

- Same immutable inputs + seed + engine/style/rule versions produce a semantic
  document match.
- Different seeds across a test set exceed minimum candidate distance in the
  requested mode.
- Regeneration preserves canonical hashes outside scope.
- Reordered JSON keys do not change canonical document hash.
- Queue redelivery does not create a second candidate/version/artifact set.

Hosted models may be nondeterministic despite a seed. Mark such adapters
`TRACEABLE_NONDETERMINISTIC`, save provider request IDs, and test invariants and
locks instead of byte identity.

## 5. Performance and Reliability Tests

Reference workloads:

- S: 16 bars, 4 tracks, rules only;
- M: 64 bars, 5 tracks, 3 candidates;
- L: 160 bars, 8 tracks, import + render, outside MVP but used as a guardrail.

Measure P50/P95 job time by phase, peak resident memory, document/artifact size,
DB queries, queue wait, model tokens/cost, and render time. Save machine and
dependency metadata. Load tests cover ordinary API traffic and bounded job
submission separately.

Failure injection covers worker termination, Redis restart, DB timeout, object
store timeout, duplicate messages, provider 429/5xx, malformed model output, and
SSE disconnect.

## 6. Observability Model

### Structured logs

Every log includes timestamp, level, service, environment, request/job ID,
workspace ID hash, operation, outcome, duration, and safe error code. Never log
raw charts, lyrics, prompts, signed URLs, tokens, or object bodies.

### Metrics

API:

- request count, latency, error by route/status;
- auth/authorization denials;
- upload bytes and rejects.

Jobs:

- queue depth/wait, running count, duration by phase/type;
- retries, stale leases, cancellations, terminal failures;
- provider calls, latency, tokens/cost, fallback rate.

Music/product:

- hard-valid candidate rate and error rules;
- repair attempts/success;
- candidate diversity band pass;
- warning and override rates;
- generation-to-acceptance and export completion;
- playability summaries by supported anonymous category.

### Traces

Trace request -> job creation -> broker -> worker phases -> provider -> object
storage -> DB commit. Pass trace context in the job envelope. Add spans per
candidate and exporter without placing musical payloads in attributes.

## 7. Alerts and SLOs

Initial beta targets, activated only after enough traffic:

- API availability 99.5% monthly;
- P95 ordinary API latency < 400 ms;
- generation job terminal success > 97%, separating valid `NO_VALID_CANDIDATE`
  from infrastructure failure;
- queue wait P95 < 30 seconds under planned load;
- export job success > 99%;
- cross-tenant authorization anomaly: alert immediately;
- provider cost and error budget alerts.

Targets become claims only with dated saved reports.

## 8. CI Gates

For every pull request:

- formatting, lint, type checks;
- unit and contract tests;
- migration validation;
- dependency/secret scan;
- build web/API/worker images;
- deterministic music fixture subset.

For main/nightly:

- containerized integration and browser E2E;
- full music fixture/evaluation suite;
- MusicXML XSD and renderer compatibility;
- PDF visual and MIDI/audio smoke tests;
- performance smoke against stored thresholds;
- license/SBOM reports.

Release requires green CI, fresh end-to-end demo artifacts, migration/rollback
test, security checklist, known-limitations update, and human verification.

