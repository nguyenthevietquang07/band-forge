# API and Job Contracts

## 1. API Style

Use a versioned REST API under `/v1` with JSON request/response bodies and an
OpenAPI document committed beside the code. Resources use plural nouns. Long
operations return `202 Accepted` with a durable job resource. Server-Sent Events
provide one-way progress updates; clients must also support polling because SSE
is advisory and reconnectable.

The API is tenant scoped through authorization, not a client-provided trusted
workspace claim. Every query includes the authorized workspace boundary.

## 2. Common Conventions

- IDs are opaque UUIDv7/ULID-style strings; clients do not parse them.
- Timestamps are UTC RFC 3339 strings.
- Enum values use `UPPER_SNAKE_CASE`.
- List endpoints use cursor pagination: `pageSize` and `pageToken`.
- Mutating creation/job requests accept an `Idempotency-Key` header.
- Draft updates require `If-Match: "<versionId>"`.
- Correlation uses `X-Request-Id`; the server creates one when absent.
- Content hashes are lowercase `sha256:<hex>`.

## 3. Error Envelope

Every non-2xx JSON error has one shape:

```json
{
  "error": {
    "code": "SOURCE_NOT_READY",
    "message": "Approve the harmonic timeline before generating.",
    "requestId": "req_01...",
    "details": {
      "sourceRevisionId": "srcv_01...",
      "unresolvedFields": ["harmony.measure-8"]
    }
  }
}
```

Status mapping:

| Status | Meaning |
|---|---|
| `400` | malformed request syntax/header |
| `401` | not authenticated |
| `403` | authenticated but unauthorized |
| `404` | resource absent inside authorized scope |
| `409` | version/idempotency/state conflict |
| `413` | upload/request too large |
| `415` | unsupported media type |
| `422` | typed input is semantically invalid |
| `429` | quota/rate limit; include `Retry-After` |
| `500` | internal failure with no implementation detail |
| `503` | dependency unavailable; retry guidance where safe |

## 4. Core Resources

### Songs and sources

```text
GET    /v1/songs
POST   /v1/songs
GET    /v1/songs/{songId}
PATCH  /v1/songs/{songId}

POST   /v1/songs/{songId}/sources
GET    /v1/songs/{songId}/sources
POST   /v1/source-revisions/{sourceRevisionId}/approval
```

`POST sources` creates an upload/import resource. Binary uploads use a two-step
flow: request a signed upload target, upload directly to object storage, then
complete the source with object hash and size. Small chord/structured text may be
sent inline.

### Arrangements and versions

```text
POST   /v1/songs/{songId}/arrangements
GET    /v1/arrangements/{arrangementId}
GET    /v1/arrangements/{arrangementId}/versions
GET    /v1/arrangement-versions/{versionId}
PATCH  /v1/arrangement-versions/{versionId}
POST   /v1/arrangement-versions/{versionId}/acceptance
```

`PATCH` applies a typed patch to a draft and returns a new immutable version. It
does not mutate the path resource in place. The response contains the new
`versionId` and parent lineage.

### Generation

```text
POST   /v1/arrangements/{arrangementId}/generation-jobs
GET    /v1/generation-jobs/{jobId}
GET    /v1/generation-jobs/{jobId}/events
POST   /v1/generation-jobs/{jobId}/cancellation
GET    /v1/generation-jobs/{jobId}/candidates
POST   /v1/generation-candidates/{candidateId}/selection
```

Example request:

```json
{
  "baseVersionId": "arv_01...",
  "sourceRevisionId": "srcv_01...",
  "candidateCount": 3,
  "seed": 774921,
  "mode": "FRESH",
  "scope": {
    "type": "SECTION_TRACKS",
    "sectionInstanceIds": ["chorus-1"],
    "trackIds": ["guitar", "keys"]
  },
  "controls": {
    "stylePackId": "pop-rock@1.0.0",
    "tempoBpm": 112,
    "feel": "STRAIGHT",
    "density": 3,
    "harmonicAdventurousness": 1
  }
}
```

The API rejects a scope that intersects a lock incompatibly. Candidate count is
capped by quota and engine policy.

### Validation and exports

```text
POST   /v1/arrangement-versions/{versionId}/validation-jobs
GET    /v1/validation-runs/{validationRunId}
GET    /v1/validation-runs/{validationRunId}/findings

POST   /v1/arrangement-versions/{versionId}/export-jobs
GET    /v1/export-jobs/{jobId}
GET    /v1/artifacts/{artifactId}
POST   /v1/artifacts/{artifactId}/download-tokens
```

Artifact metadata is returned through the API; file bodies use short-lived
signed URLs. A download token is bound to user, artifact, expiry, and disposition.

## 5. Job Representation

```json
{
  "id": "job_01...",
  "type": "GENERATION",
  "status": "RUNNING",
  "progress": {
    "phase": "VALIDATING_CANDIDATES",
    "completedUnits": 2,
    "totalUnits": 3,
    "percent": 73
  },
  "attempt": 1,
  "createdAt": "2026-07-19T08:00:00Z",
  "startedAt": "2026-07-19T08:00:01Z",
  "finishedAt": null,
  "result": null,
  "failure": null,
  "links": {
    "self": "/v1/generation-jobs/job_01...",
    "events": "/v1/generation-jobs/job_01.../events"
  }
}
```

Progress percent never determines state. A job may remain at the same percent
during model inference. The final result includes candidate IDs, rejection
summaries, manifests, and any fallback used.

## 6. SSE Events

The event stream uses `text/event-stream`. Event IDs are monotonically
increasing per job and support `Last-Event-ID` replay from a bounded durable
event log.

```text
event: phase_changed
id: 18
data: {"jobId":"job_01...","phase":"RENDERING_PREVIEWS"}

event: candidate_ready
id: 19
data: {"candidateId":"cand_01...","rank":1,"warningCount":2}

event: job_terminal
id: 20
data: {"status":"SUCCEEDED"}
```

Do not stream private musical content or provider prompts through progress
events. Authorization is checked when opening and during replay.

## 7. Idempotency

For a mutating request with `Idempotency-Key`:

1. hash authenticated principal, method, canonical path, and request body;
2. insert idempotency record transactionally;
3. same key and same hash returns the original status/body/resource;
4. same key and different hash returns `409 IDEMPOTENCY_KEY_REUSED`;
5. retain records at least 24 hours for ordinary writes and 7 days for paid or
   expensive generation jobs.

Worker idempotency is separate. Each job stores output manifest/hash; retries
reuse or verify completed step artifacts before proceeding.

## 8. Rate and Quota Policy

Apply limits by workspace and principal:

- ordinary reads/writes;
- upload bytes/day and concurrent uploads;
- concurrent generation/render jobs;
- candidate count/day;
- optional provider cost budget.

Return remaining quota metadata where useful, but do not expose shared
infrastructure capacity. Metadata adapters respect provider-specific limits;
MusicBrainz currently requires a meaningful User-Agent and averages one request
per second per source IP unless otherwise agreed.

## 9. Internal Ports

Key application contracts:

```python
class ArrangementRepository(Protocol):
    def get_version(self, version_id: VersionId) -> ArrangementDocument: ...
    def append_version(self, document: ArrangementDocument) -> VersionRecord: ...

class ArtifactStore(Protocol):
    def put_immutable(self, content: BinaryIO, media_type: str) -> ArtifactRef: ...
    def issue_download(self, artifact: ArtifactRef, subject: UserId) -> SignedDownload: ...

class JobScheduler(Protocol):
    def enqueue(self, job_id: JobId, queue: QueueName) -> None: ...

class MetadataProvider(Protocol):
    def search(self, query: MetadataQuery) -> list[SongMetadataMatch]: ...
```

Adapters validate all third-party response shapes. Metadata matches contain no
chord, lyric, or note fields.

## 10. Contract Verification

- Generate client/server types from OpenAPI where practical.
- Run schema examples and negative examples in CI.
- Verify every route returns the common error envelope.
- Fuzz patch, harmony, and scope payloads at API boundaries.
- Run consumer contract tests between API and web client.
- Preserve older response fields additively; breaking changes require `/v2` or a
  compatible migration window.

