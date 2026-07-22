# Reference Implementation Profile

This document removes ordinary scaffold ambiguity. Exact package patch versions
must be pinned from current stable releases when implementation starts; major
architecture changes require an ADR.

## 1. Runtime and Package Baseline

```text
Web:       Node.js active LTS, pnpm, Next.js App Router, React, TypeScript
API:       Python 3.12+, uv, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic
Worker:    Celery 5.6+, Redis broker, same Python domain/application packages
Database:  PostgreSQL current supported major
Storage:   S3-compatible API; MinIO-compatible local container
Music:     music21, pretty_midi and/or Mido, optional OR-Tools
Browser:   OpenSheetMusicDisplay, Tone.js
Testing:   pytest, property-based tests, API integration tests, Playwright
```

Use a workspace package manager for TypeScript and one Python workspace/lockfile
for API, worker, and domain packages. Do not publish the domain package until a
real external consumer exists.

## 2. Expected Commands

These are contract names for the future scaffold; implementation should make
them real through a root task runner or scripts.

```bash
pnpm install --frozen-lockfile
uv sync --frozen
docker compose up -d postgres redis object-store
pnpm dev
uv run fastapi dev apps/api/bandforge_api/main.py
uv run celery -A workers.music_worker.app worker --loglevel=INFO

pnpm lint
pnpm typecheck
uv run ruff check .
uv run mypy apps packages workers
uv run pytest
pnpm test:e2e
pnpm build
```

CI should call stable root aliases (`make verify` or `task verify`) instead of
duplicating command lists in workflows.

## 3. Same-Origin and Authentication Design

Deploy web and API behind one public origin. Route `/v1/*` and upload completion
to the API; serve the web elsewhere on the same host. This avoids broad CORS and
simplifies secure cookies/SSE.

Authentication flow for beta:

1. Use a standards-based managed OIDC provider; do not build password storage.
2. API initiates Authorization Code + PKCE and handles the callback.
3. API creates a random opaque session token, stores only its hash and metadata,
   and sends the raw token in an `HttpOnly; Secure; SameSite=Lax` cookie.
4. Session records have absolute and idle expiry, rotation, revocation, user ID,
   and last-seen timestamp. Redis may cache them; PostgreSQL is durable.
5. State-changing requests require same-origin checks and CSRF protection where
   browser semantics demand it.
6. Local development includes a clearly marked dev identity adapter disabled in
   production by startup validation.

Provider selection is a deployment configuration choice. The application sees
only normalized OIDC claims and internal user/membership IDs.

## 4. Database Constraints and Indexes

Every tenant-owned table contains `workspace_id NOT NULL`. Use foreign keys,
database uniqueness, and transactions in addition to application checks.

Minimum constraints/indexes:

```text
memberships: UNIQUE(workspace_id, user_id)
songs: INDEX(workspace_id, updated_at DESC, id)
source_revisions: UNIQUE(source_id, revision_number)
arrangement_versions: UNIQUE(arrangement_id, version_number)
arrangement_versions: UNIQUE(workspace_id, content_hash) only if dedup policy permits
generation_jobs: UNIQUE(workspace_id, job_type, idempotency_key)
jobs: INDEX(status, queue_name, available_at) for reconciliation
findings: INDEX(validation_run_id, severity, track_id, measure_id)
artifacts: UNIQUE(workspace_id, content_hash, artifact_type) where immutable
setlist_items: UNIQUE(setlist_id, ordinal)
sessions: UNIQUE(token_hash); INDEX(expires_at)
```

Do not use global uniqueness that reveals whether another workspace owns the
same song/hash. Foreign keys do not cascade-delete object storage; an outbox or
cleanup task handles external deletion.

## 5. Transaction Boundaries

- Source approval: verify parse/review state, create approved revision, update
  source pointer, append audit event in one transaction.
- Draft edit: check base version, create immutable child version, update draft
  pointer in one transaction.
- Job submission: verify permissions/quota/base hashes, create job and outbox
  record, reserve budget in one transaction. A dispatcher publishes the outbox.
- Job completion: verify lease, insert candidates/manifests/artifact rows, update
  job terminal state, release/resettle budget in one transaction.
- Acceptance: require hard-valid current draft, set immutable accepted status and
  arrangement pointer, append audit event in one transaction.

Use an outbox so a database commit cannot lose the queue publish. Do not hold a
database transaction during model inference or object upload.

## 6. Queue Definitions

```text
bf.import.short     chord/text/MusicXML normalization
bf.import.sandbox   PDF/image/MIDI and optional OMR parsers
bf.generate.cpu     rules/retrieval generation
bf.generate.gpu     optional learned model
bf.validate         validators and bounded repair
bf.render           MusicXML/MIDI/PDF/audio preview
bf.export           packet assembly and hashing
bf.maintenance      stale leases, outbox, retention, orphan cleanup
```

Set per-task hard/soft timeouts and queue concurrency. A job orchestration task
may schedule subtasks, but durable phase state remains in PostgreSQL. Dead-letter
or permanently failed jobs retain a safe failure code and attempt history.

## 7. Style Pack Contract

Style packs are versioned, reviewed data with no executable code:

```yaml
id: pop-rock
version: 1.0.0
supportedMeters: [4/4]
tempoRange: { minimum: 80, maximum: 160 }
roles:
  drums:
    chorus:
      patterns: [drums.pop-rock.chorus.01, drums.pop-rock.chorus.02]
      fillWindows: [LAST_BEAT, LAST_HALF_BAR]
  bass:
    chorus:
      allowedSubdivisions: [QUARTER, EIGHTH]
      chordToneStrongBeatMinimum: 0.8
      approachTonePolicy: DIATONIC_OR_CHROMATIC_LAST_EIGHTH
  guitar:
    chorus: { role: COMP, register: MID, density: 3 }
  keys:
    chorus: { role: PAD, register: MID_HIGH, density: 2 }
coordination:
  maxCompingOnsetOverlap: 0.45
  reserveMelodyRegister: true
difficultyTransforms:
  BEGINNER: [REDUCE_SYNCOPATION, LIMIT_CHORD_SIZE_3, REMOVE_LARGE_LEAPS]
license:
  origin: BANDFORGE_AUTHORED
  attribution: null
```

Load through a strict schema. Pattern IDs resolve to authored/licensed pattern
records with provenance. A style pack cannot loosen universal hard constraints.

## 8. Validator Rule Catalog

Rule IDs are stable and grouped:

```text
BF-SCH-* schema/contract
BF-STR-* form/measure/timing
BF-HAR-* harmony/melody
BF-RHY-* rhythm/groove
BF-INS-* instrument feasibility
BF-PLY-* difficulty/playability
BF-ARR-* cross-track arrangement
BF-LCK-* source and scope locks
BF-EXP-* export/artifact
BF-SEC-* security/import safety
```

Each rule definition specifies version, default severity, applicable styles and
instruments, inputs, deterministic algorithm, repair policy, examples, and tests.
Changing semantics increments the rule version; changing a warning to an error
requires release-note and fixture review.

## 9. Object Storage Layout

Object keys are generated IDs and content hashes, not user filenames:

```text
quarantine/{workspaceId}/{uploadId}/original
sources/{workspaceId}/{sourceRevisionId}/{contentHash}
arrangements/{workspaceId}/{versionId}/document.json
artifacts/{workspaceId}/{versionId}/{artifactType}/{contentHash}.{ext}
temporary/{workspaceId}/{jobId}/{attempt}/{step}/{name}
```

Lifecycle rules remove temporary objects after 24 hours and quarantine objects
after the configured review/failure period. Durable objects follow workspace
retention and legal-hold policy.

## 10. Configuration Contract

Validate configuration at startup. Expected categories:

```text
APP_ENV, PUBLIC_BASE_URL
DATABASE_URL, REDIS_URL, CELERY_BROKER_URL
OBJECT_STORE_ENDPOINT, OBJECT_STORE_BUCKET, OBJECT_STORE_REGION
OBJECT_STORE_ACCESS_KEY, OBJECT_STORE_SECRET_KEY
OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, SESSION_SIGNING_KEY
MODEL_PROVIDER, MODEL_API_KEY, MODEL_BUDGET_USD_DAILY
UPLOAD_MAX_BYTES, IMPORT_MAX_UNCOMPRESSED_BYTES
JOB_*_TIMEOUT_SECONDS, JOB_MAX_ATTEMPTS
OTEL_EXPORTER_OTLP_ENDPOINT, LOG_LEVEL
```

Secret fields must be absent from logs and error responses. Production startup
fails if dev auth, public buckets, wildcard CORS, or placeholder secrets are
enabled.

## 11. Local Demo Fixture

The first golden demo is an original/public-domain-safe 16-bar song:

```text
Form: Verse 8 bars -> Chorus 8 bars
Key: G major; Meter: 4/4; Tempo: 104
Band: drums, bass, guitar, keys
Levels: intermediate, intermediate, beginner, intermediate
Style: acoustic-pop@1.0.0
Candidates: 2, mode FRESH, fixed seeds 1001 and 1002
```

The fixture must include expected structure, harmony, locks, validator summary,
MIDI, MusicXML, PDFs, screenshots, and playback smoke report. It becomes the
first end-to-end release artifact and recruiter-facing demonstration.

