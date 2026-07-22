# BandForge Contract Alignment and Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the working structured-source workflow through the documented `/v1` resource paths, make mutating requests safely replayable, and save a live API demonstration as Cycle 2 evidence.

**Architecture:** Keep the existing modular-monolith service and SQLite development adapter. Add a narrow HTTP translation layer from the public source contract to the existing `StructuredChartInput`, while retaining legacy foundation routes only as compatibility aliases during this local stage. Store idempotency records beside the local workflow records so a repeated key and identical request returns its original response; a reused key with different content returns a clear conflict.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite, PyYAML, `openapi-spec-validator`, pytest, Ruff, Uvicorn.

## Global Constraints

- Only user-supplied/licensed material may be a harmonic source; metadata never supplies chords.
- Public API uses `/v1` resource paths, `Idempotency-Key` for mutations, `X-Request-Id`, and the common error envelope.
- The first structured source supports only `sourceType: STRUCTURED`, a `key` of `A-G_(MAJOR|MINOR)`, and one supported chord symbol per 4/4 bar.
- Unsupported symbols yield review findings; they must never be approximated.
- An approval request repeats `rightsAttested: true`; source approval remains an explicit immutable transition.
- Tests are written and observed failing before production behavior is added.
- Every implementation cycle ends with a live demo, fresh automated checks, a recorded result, and explicit exclusions.
- No generation, playback, file/OCR import, authentication, queue, or production deployment is in this cycle.

---

### Task 1: Add Contract-Aligned Source Routes

**Files:**
- Modify: `src/bandforge_api/main.py`
- Modify: `src/bandforge_api/services.py`
- Modify: `tests/api/test_source_workflow.py`

**Interfaces:**
- Consumes: `SourceWorkflowService.create_source_revision(song_id, rights_attested, key, bars)`.
- Produces `POST /v1/songs/{song_id}/sources` with `{sourceType, rightsAttested, content:{key,bars}}` and `POST /v1/source-revisions/{source_revision_id}/approval` with `{rightsAttested:true}`.
- Produces `POST /v1/songs/{song_id}/arrangements` with `{sourceRevisionId,title}` and an `Arrangement` response with `id`, `songId`, and `currentDraftVersionId`.

- [ ] **Step 1: Write failing public-route tests**

```python
def test_public_source_routes_create_an_arrangement(tmp_path) -> None:
    with _client(tmp_path) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}, headers=KEY).json()
        source = client.post(
            f"/v1/songs/{song['id']}/sources", headers=KEY2,
            json={"sourceType": "STRUCTURED", "rightsAttested": True,
                  "content": {"key": "A_MINOR", "bars": ["Am", "F", "C", "G"]}},
        ).json()
        assert client.post(f"/v1/source-revisions/{source['id']}/approval", headers=KEY3,
                           json={"rightsAttested": True}).status_code == 200
        response = client.post(f"/v1/songs/{song['id']}/arrangements", headers=KEY4,
                               json={"sourceRevisionId": source["id"], "title": "Late Set"})
    assert response.status_code == 201
    assert response.json()["currentDraftVersionId"]
```

- [ ] **Step 2: Run the route test to verify it fails**

Run: `python -m pytest tests/api/test_source_workflow.py::test_public_source_routes_create_an_arrangement -q`

Expected: FAIL with `404` because the public routes do not exist.

- [ ] **Step 3: Implement Pydantic public request models and route adapters**

```python
class StructuredSourceContent(BaseModel):
    key: Annotated[str, Field(pattern=r"^[A-G]_(MAJOR|MINOR)$")]
    bars: Annotated[list[str], Field(min_length=1, max_length=256)]

class CreateSourceRequest(BaseModel):
    source_type: Literal["STRUCTURED"] = Field(alias="sourceType")
    rights_attested: Literal[True] = Field(alias="rightsAttested")
    content: StructuredSourceContent

@app.post("/v1/songs/{song_id}/sources", status_code=201)
def create_source(song_id: str, payload: CreateSourceRequest, ...):
    return service.create_source_revision(song_id, True, payload.content.key, payload.content.bars)
```

- [ ] **Step 4: Run the focused test and the legacy API tests**

Run: `python -m pytest tests/api/test_source_workflow.py -q`

Expected: PASS; legacy foundation aliases remain covered while public routes are verified.

### Task 2: Add Idempotency and Validate the Focused OpenAPI Surface

**Files:**
- Modify: `src/bandforge_api/repository.py`
- Modify: `src/bandforge_api/main.py`
- Modify: `contracts/openapi.yaml`
- Create: `tests/api/test_idempotency.py`
- Create: `tests/contracts/test_openapi_contract.py`

**Interfaces:**
- Consumes: `Idempotency-Key` header and canonical request body bytes.
- Produces repeated `POST /v1/songs` responses with the original `201` body; returns `409 IDEMPOTENCY_KEY_REUSED` when the same key has a distinct request fingerprint.
- The OpenAPI source endpoints and arrangement creation endpoint match the public route paths, headers, and request schemas from Task 1.

- [ ] **Step 1: Write failing idempotency and contract tests**

```python
def test_same_idempotency_key_returns_original_song(tmp_path) -> None:
    with _client(tmp_path) as client:
        first = client.post("/v1/songs", headers={"Idempotency-Key": "song-create-001"}, json={"title": "Late Set"})
        second = client.post("/v1/songs", headers={"Idempotency-Key": "song-create-001"}, json={"title": "Late Set"})
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()

def test_openapi_public_source_path_matches_contract() -> None:
    document = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    assert "/songs/{songId}/sources" in document["paths"]
    assert "IdempotencyKey" in [item["$ref"].rsplit("/", 1)[-1] for item in document["paths"]["/songs/{songId}/sources"]["post"]["parameters"]]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/api/test_idempotency.py tests/contracts/test_openapi_contract.py -q`

Expected: FAIL because no idempotency store exists and the public contract does not contain the structured `content` schema.

- [ ] **Step 3: Persist a canonical request fingerprint and original response**

```python
class IdempotencyRow(Base):
    __tablename__ = "idempotency_records"
    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    status_code: Mapped[int] = mapped_column(nullable=False)
    response_json: Mapped[str] = mapped_column(Text, nullable=False)
```

Use a `POST` wrapper that hashes method, route template, and sorted JSON body;
return the stored response for an exact replay and raise `IDEMPOTENCY_KEY_REUSED`
for a fingerprint mismatch.

- [ ] **Step 4: Update the OpenAPI source schemas and run semantic validation**

```python
from openapi_spec_validator import validate

def test_openapi_document_is_semantically_valid() -> None:
    validate(yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8")))
```

Run: `python -m pytest tests/api/test_idempotency.py tests/contracts/test_openapi_contract.py -q`

Expected: PASS.

### Task 3: Make the Demo Gate Reproducible and Record the Cycle

**Files:**
- Create: `scripts/run_source_workflow_demo.py`
- Create: `reports/cycle-2-contract-demo.json`
- Create: `docs/13-cycle-demo-gate.md`
- Modify: `docs/12-foundation-sdlc.md`
- Modify: `portfolio_projects/SDLC_STAGE_LOG.md`

**Interfaces:**
- Consumes: a running API base URL from `BANDFORGE_API_URL` or `http://127.0.0.1:8012`.
- Produces an exit code of zero only when source creation, approval, arrangement creation, exact idempotent replay, and a request ID all succeed; writes a sanitized JSON report with IDs, HTTP statuses, and checks.

- [ ] **Step 1: Write a failing subprocess-level demo test**

```python
def test_demo_script_reports_all_required_checks(tmp_path) -> None:
    report = run_demo_against_test_server(tmp_path)
    assert report["checks"] == {"sourceCreated": True, "approved": True,
                                "arrangementCreated": True, "idempotentReplay": True,
                                "requestIdObserved": True}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/api/test_demo_script.py -q`

Expected: FAIL because the demo script does not exist.

- [ ] **Step 3: Implement the real HTTP demo and write the evidence document**

```python
response = requests.post(f"{base_url}/v1/songs", json={"title": "BandForge Demo Original"}, headers=key("demo-song-001"), timeout=10)
assert_status(response, 201)
# Create source, approve it, create arrangement, replay the song request, then write report.
```

The demo uses `urllib.request` from the Python standard library rather than a
test-double client, so the published command exercises real HTTP.

- [ ] **Step 4: Run the complete release gate and live demo**

Run: `python -m pytest -q; python -m ruff check src tests; python scripts/run_source_workflow_demo.py`

Expected: all tests and lint pass; report contains five true checks and no user material beyond the authored demo chart.

## Self-Review

**Spec coverage:** The plan closes the documented source-route/OpenAPI gap, adds the contract-required idempotency behavior to the initial mutation, and establishes the requested per-cycle test/demo/evidence process.

**Deliberate gaps:** API-wide idempotency, authorization, pagination, production PostgreSQL, object storage, imports, editor UI, generation, playback, rendering, export, and asynchronous jobs remain future slices. The OpenAPI file will still describe target-only generation/export paths, which are not implemented and must not be advertised as working.

**Type consistency:** `StructuredSourceContent` feeds `create_source_revision`; source approval returns the same source revision; arrangement creation maps an approved revision to a seed version. The report only records values returned by live HTTP calls.

## Execution Note

The owner asked to continue implementation and requires a test/demo gate at the end of every cycle. Execute inline with `superpowers:executing-plans`, recording actual verification output rather than anticipated output.
