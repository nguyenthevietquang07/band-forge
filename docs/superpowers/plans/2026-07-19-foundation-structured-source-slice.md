# BandForge Foundation and Structured Source Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a locally runnable API that converts a user-supplied structured chord chart into an immutable, schema-valid `ArrangementDocument` seed after explicit source approval.

**Architecture:** A Python modular monolith holds the API, source workflow, and canonical music-domain code in separately importable packages. SQLite is a deterministic local-development adapter; its repository port is designed for a PostgreSQL adapter later. The API accepts only supplied harmonic material, normalizes it once into integer-tick events, persists immutable revisions, and produces an arrangement seed with a non-performing `Source Guide` track that validates against the committed JSON Schema.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite, `jsonschema`, pytest, Ruff, Uvicorn, Docker Compose for future local dependencies.

## Global Constraints

- Only user-supplied/licensed musical material may enter the source workflow; song metadata is never harmonic input.
- `ArrangementDocument` remains the canonical musical snapshot; MusicXML and MIDI remain interchange formats.
- Canonical time uses integer ticks and `ticksPerQuarter = 960`; never persist floating-point seconds as musical time.
- Source revisions and arrangement versions are immutable; approval is an explicit state transition.
- Production code is written only after a test has failed for the intended behavior.
- This slice supports `4/4`, one chord per bar, `MAJOR` or `MINOR` keys, `MAJOR`, `MINOR`, `DOMINANT`, `SUS2`, `SUS4`, and `POWER` chord qualities, plus optional `6`, `7`, `MAJ7`, `9`, and `ADD9` extensions.
- Unsupported chord tokens must produce review findings; they must never be silently approximated.
- Every API error uses the documented `{ "error": { "code", "message", "details", "requestId" } }` envelope.
- No generative model, upload/OCR, playback, export, authentication, queue, or third-party song lookup is part of this slice.

---

## File Structure

| Path | Responsibility |
|---|---|
| `pyproject.toml` | Package metadata, pinned development commands, dependency groups, Ruff/Pytest configuration. |
| `src/bandforge_domain/chords.py` | Parses supported display symbols into structured harmony or findings. |
| `src/bandforge_domain/chart.py` | Validates structured input and derives a canonical measure/harmony timeline. |
| `src/bandforge_domain/arrangements.py` | Builds a schema-valid `ArrangementDocument` seed with a non-performing `Source Guide` track and validates it against the committed schema. |
| `src/bandforge_api/main.py` | FastAPI application, request ID middleware, health endpoint, source workflow routes, error mapping. |
| `src/bandforge_api/repository.py` | SQLAlchemy repository port and SQLite local adapter for songs, source revisions, and arrangement versions. |
| `src/bandforge_api/services.py` | Transactional use cases for source creation, approval, and arrangement seed creation. |
| `tests/domain/test_chords.py` | Chord-parser behavior and unsupported-token findings. |
| `tests/domain/test_chart.py` | Integer-tick grid and chart-validation behavior. |
| `tests/domain/test_arrangements.py` | Schema-valid arrangement seed behavior. |
| `tests/api/test_source_workflow.py` | HTTP happy and failure paths through a temporary SQLite database. |
| `docs/12-foundation-sdlc.md` | Scope, acceptance criteria, commands, evidence, known exclusions, and next-slice handoff. |
| `tasks/todo.md` | Living status of the approved implementation plan. |

### Task 1: Establish the Runnable Python Workspace

**Files:**
- Create: `portfolio_projects/bandforge/pyproject.toml`
- Create: `portfolio_projects/bandforge/.gitignore`
- Create: `portfolio_projects/bandforge/src/bandforge_domain/__init__.py`
- Create: `portfolio_projects/bandforge/src/bandforge_api/__init__.py`
- Create: `portfolio_projects/bandforge/tests/conftest.py`
- Create: `portfolio_projects/bandforge/tasks/todo.md`
- Modify: `portfolio_projects/bandforge/README.md`

**Interfaces:**
- Produces: `bandforge_domain` and `bandforge_api` import packages and `pytest`, `ruff`, `uvicorn` commands for later tasks.

- [ ] **Step 1: Write a failing import smoke test**

```python
def test_domain_package_is_importable() -> None:
    import bandforge_domain

    assert bandforge_domain.__name__ == "bandforge_domain"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/conftest.py -q`

Expected: FAIL because the package and test configuration do not exist.

- [ ] **Step 3: Add the minimal project configuration and package markers**

```toml
[project]
name = "bandforge"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["fastapi>=0.115,<1", "jsonschema>=4.23,<5", "pydantic>=2.10,<3", "sqlalchemy>=2.0,<3", "uvicorn[standard]>=0.30,<1"]

[project.optional-dependencies]
dev = ["httpx>=0.28,<1", "pytest>=8.3,<9", "ruff>=0.8,<1"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **Step 4: Run the smoke test and quality discovery commands**

Run: `python -m pytest tests/conftest.py -q; python -m ruff check src tests`

Expected: PASS; Ruff exits `0`.

- [ ] **Step 5: Record the initial task status**

```markdown
# BandForge Foundation Slice Tasks

- [x] Task 1: Runnable Python workspace
- [ ] Task 2: Chord parser and chart timeline
- [ ] Task 3: Arrangement seed and schema validation
- [ ] Task 4: Source workflow API and persistence
- [ ] Task 5: SDLC evidence and end-to-end verification
```

- [ ] **Step 6: Commit**

```bash
git add portfolio_projects/bandforge
git commit -m "chore(bandforge): scaffold foundation workspace"
```

### Task 2: Parse Supported Chords and Build a Canonical Bar Grid

**Files:**
- Create: `portfolio_projects/bandforge/src/bandforge_domain/chords.py`
- Create: `portfolio_projects/bandforge/src/bandforge_domain/chart.py`
- Create: `portfolio_projects/bandforge/tests/domain/test_chords.py`
- Create: `portfolio_projects/bandforge/tests/domain/test_chart.py`
- Modify: `portfolio_projects/bandforge/tasks/todo.md`

**Interfaces:**
- Consumes: importable workspace from Task 1.
- Produces: `parse_chord(symbol: str) -> ParsedChord | ParseFinding` and `normalize_chart(request: StructuredChartInput) -> NormalizedChart`.
- `NormalizedChart` contains `measures: list[Measure]`, `harmony: list[HarmonyEvent]`, and `findings: list[ParseFinding]`.

- [ ] **Step 1: Write failing parser and grid tests**

```python
def test_parse_chord_preserves_display_symbol_and_root() -> None:
    parsed = parse_chord("F#m7")
    assert parsed.display_symbol == "F#m7"
    assert parsed.root_pitch_class == 6
    assert parsed.quality == "MINOR"
    assert parsed.extensions == ["7"]


def test_normalize_chart_creates_contiguous_four_four_bars() -> None:
    chart = normalize_chart(
        StructuredChartInput(title="Late Set", key="A_MINOR", bars=["Am", "F", "C", "G"])
    )
    assert [measure.start_tick for measure in chart.measures] == [0, 3840, 7680, 11520]
    assert [event.duration_ticks for event in chart.harmony] == [3840, 3840, 3840, 3840]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/domain/test_chords.py tests/domain/test_chart.py -q`

Expected: FAIL because `parse_chord` and `normalize_chart` are not defined.

- [ ] **Step 3: Implement the smallest supported grammar and timeline**

```python
ROOT_PITCH_CLASSES = {"C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3, "E": 4,
                      "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8, "AB": 8, "A": 9,
                      "A#": 10, "BB": 10, "B": 11}
TICKS_PER_QUARTER = 960
FOUR_FOUR_BAR_TICKS = TICKS_PER_QUARTER * 4

def parse_chord(symbol: str) -> ParsedChord | ParseFinding:
    # Match root, optional accidental, suffix, and optional slash bass once.
    ...

def normalize_chart(request: StructuredChartInput) -> NormalizedChart:
    # Each supplied bar is one locked harmony event spanning a 4/4 measure.
    ...
```

- [ ] **Step 4: Add explicit unsupported-token coverage**

```python
def test_normalize_chart_returns_finding_instead_of_guessing_unknown_chord() -> None:
    chart = normalize_chart(
        StructuredChartInput(title="Late Set", key="A_MINOR", bars=["Am", "Cmaj9#11"])
    )
    assert chart.harmony[1] is None
    assert chart.findings[0].code == "UNSUPPORTED_CHORD_SYMBOL"
    assert chart.findings[0].bar_ordinal == 2
```

- [ ] **Step 5: Run focused tests and mark the task complete**

Run: `python -m pytest tests/domain/test_chords.py tests/domain/test_chart.py -q; python -m ruff check src tests`

Expected: PASS; unsupported syntax is surfaced as a finding.

- [ ] **Step 6: Commit**

```bash
git add portfolio_projects/bandforge/src/bandforge_domain portfolio_projects/bandforge/tests/domain portfolio_projects/bandforge/tasks/todo.md
git commit -m "feat(bandforge): normalize structured chord charts"
```

### Task 3: Create and Validate an Immutable Arrangement Seed

**Files:**
- Create: `portfolio_projects/bandforge/src/bandforge_domain/arrangements.py`
- Create: `portfolio_projects/bandforge/tests/domain/test_arrangements.py`
- Modify: `portfolio_projects/bandforge/tasks/todo.md`

**Interfaces:**
- Consumes: `NormalizedChart` from `normalize_chart`.
- Produces: `build_arrangement_seed(chart: NormalizedChart, source_revision_id: str, source_hash: str, now: datetime) -> dict[str, Any]` and `validate_arrangement_document(document: Mapping[str, Any]) -> None`.
- Rejects any chart that has findings or missing harmony before document construction.

- [ ] **Step 1: Write a failing schema-valid seed test**

```python
def test_build_arrangement_seed_matches_committed_schema() -> None:
    chart = normalize_chart(StructuredChartInput(title="Late Set", key="A_MINOR", bars=["Am", "F"]))
    document = build_arrangement_seed(
        chart, source_revision_id="src_rev_0001", source_hash="sha256:" + "a" * 64,
        now=datetime(2026, 7, 19, tzinfo=timezone.utc),
    )
    validate_arrangement_document(document)
    assert document["global"]["ticksPerQuarter"] == 960
    assert document["harmony"][0]["isLocked"] is True
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/domain/test_arrangements.py -q`

Expected: FAIL because the seed builder does not exist.

- [ ] **Step 3: Implement deterministic IDs, provenance, and JSON Schema validation**

```python
def build_arrangement_seed(chart, source_revision_id, source_hash, now):
    if chart.findings or any(event is None for event in chart.harmony):
        raise SourceNotReadyError("Resolve every source finding before approval.")
    document = {"schemaVersion": "1.0.0", "status": "DRAFT", "global": ..., "tracks": [source_guide_track], ...}
    validate_arrangement_document(document)
    return document

def validate_arrangement_document(document: Mapping[str, Any]) -> None:
    validator = Draft202012Validator(load_committed_schema())
    validator.validate(document)
```

- [ ] **Step 4: Write and run the invalid-source failure test**

```python
def test_build_arrangement_seed_rejects_unresolved_source_findings() -> None:
    chart = normalize_chart(StructuredChartInput(title="Late Set", key="A_MINOR", bars=["Cmaj9#11"]))
    with pytest.raises(SourceNotReadyError):
        build_arrangement_seed(chart, "src_rev_0001", "sha256:" + "a" * 64, FIXED_NOW)
```

Run: `python -m pytest tests/domain/test_arrangements.py -q`

Expected: PASS.

- [ ] **Step 5: Run the complete domain suite and mark the task complete**

Run: `python -m pytest tests/domain -q; python -m ruff check src tests`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add portfolio_projects/bandforge/src/bandforge_domain/arrangements.py portfolio_projects/bandforge/tests/domain/test_arrangements.py portfolio_projects/bandforge/tasks/todo.md
git commit -m "feat(bandforge): create validated arrangement seeds"
```

### Task 4: Persist and Expose the Explicit Source Approval Workflow

**Files:**
- Create: `portfolio_projects/bandforge/src/bandforge_api/repository.py`
- Create: `portfolio_projects/bandforge/src/bandforge_api/services.py`
- Create: `portfolio_projects/bandforge/src/bandforge_api/main.py`
- Create: `portfolio_projects/bandforge/tests/api/test_source_workflow.py`
- Modify: `portfolio_projects/bandforge/tasks/todo.md`

**Interfaces:**
- Consumes: `normalize_chart`, `build_arrangement_seed`, and `SourceNotReadyError` from Tasks 2-3.
- Produces routes: `GET /health`, `POST /v1/songs`, `POST /v1/songs/{song_id}/source-revisions`, `POST /v1/source-revisions/{source_revision_id}/approve`, and `POST /v1/source-revisions/{source_revision_id}/arrangement-seeds`.
- Successful source creation returns `201` with immutable source revision ID, normalized bars, and findings; approval returns `409 SOURCE_NOT_READY` if unresolved findings exist; arrangement seed creation requires approval.

- [ ] **Step 1: Write a failing API happy-path test**

```python
def test_approved_chart_creates_schema_valid_arrangement_seed(client: TestClient) -> None:
    song = client.post("/v1/songs", json={"title": "Late Set"}).json()
    revision = client.post(
        f"/v1/songs/{song['id']}/source-revisions",
        json={"rightsAttested": True, "key": "A_MINOR", "bars": ["Am", "F", "C", "G"]},
    ).json()
    assert client.post(f"/v1/source-revisions/{revision['id']}/approve").status_code == 200
    response = client.post(f"/v1/source-revisions/{revision['id']}/arrangement-seeds")
    assert response.status_code == 201
    assert response.json()["document"]["sourceRefs"][0]["sourceRevisionId"] == revision["id"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/api/test_source_workflow.py::test_approved_chart_creates_schema_valid_arrangement_seed -q`

Expected: FAIL because the FastAPI application and routes do not exist.

- [ ] **Step 3: Implement repository, service, and API routes**

```python
@app.post("/v1/songs", status_code=status.HTTP_201_CREATED)
def create_song(payload: CreateSongRequest, service: SourceWorkflowService = Depends(get_service)) -> SongResponse:
    return service.create_song(payload.title)

@app.post("/v1/source-revisions/{source_revision_id}/approve")
def approve_source_revision(source_revision_id: str, service: SourceWorkflowService = Depends(get_service)) -> SourceRevisionResponse:
    return service.approve_source_revision(source_revision_id)
```

- [ ] **Step 4: Write and run mandatory failure-path tests**

```python
def test_unresolved_chord_cannot_be_approved(client: TestClient) -> None:
    song = client.post("/v1/songs", json={"title": "Late Set"}).json()
    revision = client.post(
        f"/v1/songs/{song['id']}/source-revisions",
        json={"rightsAttested": True, "key": "A_MINOR", "bars": ["Cmaj9#11"]},
    ).json()
    response = client.post(f"/v1/source-revisions/{revision['id']}/approve")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SOURCE_NOT_READY"


def test_source_without_rights_attestation_is_rejected(client: TestClient) -> None:
    song = client.post("/v1/songs", json={"title": "Late Set"}).json()
    response = client.post(
        f"/v1/songs/{song['id']}/source-revisions",
        json={"rightsAttested": False, "key": "A_MINOR", "bars": ["Am"]},
    )
    assert response.status_code == 422
```

Run: `python -m pytest tests/api/test_source_workflow.py -q`

Expected: PASS; all failures use the common error envelope except FastAPI request-shape rejection, which is mapped to `INVALID_REQUEST` too.

- [ ] **Step 5: Add request ID and health endpoint coverage**

```python
def test_health_returns_request_id(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-Id": "req_test_001"})
    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == "req_test_001"
    assert response.json()["status"] == "ok"
```

- [ ] **Step 6: Run API and full test suites, then mark the task complete**

Run: `python -m pytest -q; python -m ruff check src tests`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add portfolio_projects/bandforge/src/bandforge_api portfolio_projects/bandforge/tests/api portfolio_projects/bandforge/tasks/todo.md
git commit -m "feat(bandforge): add source approval workflow API"
```

### Task 5: Document the Slice and Produce Reproducible Evidence

**Files:**
- Create: `portfolio_projects/bandforge/docs/12-foundation-sdlc.md`
- Modify: `portfolio_projects/bandforge/README.md`
- Modify: `portfolio_projects/SDLC_STAGE_LOG.md`
- Modify: `portfolio_projects/bandforge/tasks/todo.md`

**Interfaces:**
- Consumes: runnable API and tests from Tasks 1-4.
- Produces: documented acceptance evidence, exact local run commands, a current completion boundary, and a next-slice decision record.

- [ ] **Step 1: Write the evidence checklist before final verification**

```markdown
## Acceptance Evidence

- [ ] Domain suite passes.
- [ ] API happy path persists a reviewed source and creates a schema-valid seed.
- [ ] API rejects missing rights attestation and unresolved chord tokens.
- [ ] Lint passes.
- [ ] API starts and `/health` responds with a request ID.
```

- [ ] **Step 2: Add exact local commands and boundaries**

```markdown
## Run Locally

```powershell
python -m pip install -e ".[dev]"
python -m uvicorn bandforge_api.main:app --app-dir src --reload
```

This slice does not generate parts, retrieve song notation, accept files, render score, or play audio.
```

- [ ] **Step 3: Run every quality gate and capture outcomes**

Run: `python -m pytest -q; python -m ruff check src tests; python -m uvicorn bandforge_api.main:app --app-dir src --host 127.0.0.1 --port 8011`

Expected: tests and Ruff pass; server starts and `GET http://127.0.0.1:8011/health` returns `200`.

- [ ] **Step 4: Update the SDLC stage log and task checklist**

```markdown
| Stage | Status | Evidence |
|---|---|---|
| Foundation structured-source slice | Complete | `bandforge/docs/12-foundation-sdlc.md` |
```

- [ ] **Step 5: Commit**

```bash
git add portfolio_projects/bandforge/docs portfolio_projects/bandforge/README.md portfolio_projects/SDLC_STAGE_LOG.md portfolio_projects/bandforge/tasks/todo.md
git commit -m "docs(bandforge): record foundation slice evidence"
```

## Self-Review

**Spec coverage:** This plan implements the first useful half of roadmap Milestone 1: user-controlled structured source, chord normalization, review findings, explicit approval, immutable source revision, and canonical measure/harmony data. It also starts Milestone 0 with a runnable API, request IDs, local persistence, test/lint commands, and evidence documentation.

**Deliberate gaps:** Authentication/workspace authorization, PostgreSQL/Redis/object storage, web editor, ChordPro/MusicXML/MIDI/imports, PDF/image uploads, playback/export, asynchronous jobs, generation, validators beyond schema and source readiness, model integration, and deployment are intentionally separate milestones. They cannot be represented honestly by this narrow slice.

**Placeholder scan:** No product code is described as a placeholder. The code snippets use ellipses only to prevent this plan from duplicating entire implementation files; the executing agent must write concrete implementations and tests, not preserve ellipses.

**Type consistency:** `StructuredChartInput -> NormalizedChart -> build_arrangement_seed -> ArrangementDocument` is the sole domain flow. The API never derives harmony from a song title and only calls `build_arrangement_seed` after `approve_source_revision` has persisted the approved state.

## Execution Note

The owner explicitly requested execution. Implement this plan inline with `superpowers:executing-plans`, retain the task checkboxes as evidence, and stop only for a real blocker such as unavailable dependencies or a failed quality gate that cannot be diagnosed.
