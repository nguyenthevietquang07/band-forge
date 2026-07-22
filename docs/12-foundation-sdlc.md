# Foundation Structured-Source Slice

## Status

Implemented and locally verified on 2026-07-19. This is the first runnable
BandForge vertical slice, not a claim that the complete product exists.

## Goal and Acceptance Criteria

The slice accepts a user-authored, structured 4/4 chord chart, records an
immutable source revision, surfaces unsupported chords as review findings,
requires explicit source approval, and creates a schema-valid,
source-locked `ArrangementDocument` seed.

Acceptance evidence:

- The original foundation checkpoint recorded `11 passed` from
  `python -m pytest -q`; the current repository-wide verification is recorded
  in the latest cycle gate below.
- `python -m ruff check src tests` exits successfully.
- API tests cover the source-to-seed happy path, unsupported chord rejection,
  rights-attestation rejection, and request ID propagation.
- Domain tests validate the created document against the committed Draft
  2020-12 ArrangementDocument schema.

## Implemented Workflow

1. `POST /v1/songs` creates a local song record with user metadata only.
2. `POST /v1/songs/{songId}/source-revisions` accepts an attested `key` and
   ordered chord `bars`; it calculates a SHA-256 content hash and normalizes
   each bar using 960 ticks per quarter note.
3. Unsupported symbols return a source revision with an
   `UNSUPPORTED_CHORD_SYMBOL` finding. No chord is silently guessed.
4. `POST /v1/source-revisions/{sourceRevisionId}/approve` rejects unresolved
   findings with `409 SOURCE_NOT_READY`; otherwise it persists `APPROVED`.
5. `POST /v1/source-revisions/{sourceRevisionId}/arrangement-seeds` creates a
   `DRAFT` arrangement version with harmony locks and a non-performing
   `Source Guide` track. This is a canonical starting document, not a generated
   player part.

All domain errors use the documented error envelope and API responses carry an
`X-Request-Id` value.

## Run Locally

```powershell
cd portfolio_projects/bandforge
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check src tests
python -m uvicorn bandforge_api.main:app --app-dir src --host 127.0.0.1 --port 8011
```

Then call `http://127.0.0.1:8011/health`.

## Technical Decisions

- The API uses FastAPI `TestClient` with normal pytest tests, following the
  documented testing approach: <https://fastapi.tiangolo.com/tutorial/testing/>.
- Request and domain error handling uses registered FastAPI exception handlers:
  <https://fastapi.tiangolo.com/tutorial/handling-errors/>.
- Local persistence uses SQLAlchemy 2 and SQLite only as a development adapter;
  the production architecture remains PostgreSQL. SQLite transaction behavior
  and limitations are documented by SQLAlchemy at
  <https://docs.sqlalchemy.org/en/20/dialects/sqlite.html>.
- The contract validator uses `Draft202012Validator` against the committed
  JSON Schema: <https://python-jsonschema.readthedocs.io/en/stable/validate/>.

## Exclusions and Next Slice

This slice does not retrieve a song's notation from a title, accept files,
perform OCR, generate instrument parts, queue background work, play audio,
render notation, export PDFs/MIDI/MusicXML, authenticate users, or deploy a
production service.

The committed OpenAPI document remains the broader target contract. Before a
web client or generated SDK is introduced, its source-revision route shapes
must be synchronized with this implemented foundation API and validated with a
semantic OpenAPI linter. This slice intentionally proves behavior first; it
does not claim generated client-contract coverage yet.

The structured source editor and its web/API integration are now implemented in
the Cycle 4 slice. The next product work remains PDF export and then the
deterministic four-piece generator only after its validators and fixtures are
specified.
