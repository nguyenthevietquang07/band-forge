# Cycle Demo Gate

Every BandForge implementation cycle closes only after all of these are true:

1. The scope is written in a plan with explicit exclusions.
2. New behavior has test-first coverage and the relevant suite passes.
3. Lint and contract checks applicable to the slice pass.
4. A real demo runs through the user-visible happy path.
5. The SDLC log records the commands, result, evidence location, and limits.

The next cycle cannot claim to build on an unverified predecessor. A failed demo
is a failed cycle even when unit tests are green.

## Cycle 2 Checkpoint

Date: 2026-07-19

Scope: public structured-source resource routes and song-creation idempotency.

Automated evidence:

- `python -m pytest -q`: `14 passed`.
- `python -m ruff check src tests`: passed.

Live HTTP evidence on `127.0.0.1:8012`:

- created `song_4020461c773d48a4be438bdefaed6d27`;
- replayed the same request with the same key and received the same song ID;
- created and approved a structured `Am | F | C | G` source;
- created `arrangement_edff83eb6ad4416895b12081f321c048` with draft version
  `arr_version_c6b2cd4faa124b75b607332140b89a13`.

Exclusions: full OpenAPI semantic validation, idempotency for all mutation
routes, authentication, editor UI, generation, playback, rendering, and
exports remain unimplemented.

## Cycle 3 Contract Checkpoint

Date: 2026-07-19

Scope: validate the OpenAPI document semantically and align its structured
source request schema with the implementation.

Automated evidence:

- `python -m pytest -q`: `16 passed`.
- `python -m ruff check src tests`: passed.
- `openapi-spec-validator` validates the committed OpenAPI 3.1 document.

The public source contract now accepts only the implemented `STRUCTURED`
source type with `{key, bars}` content. ChordPro, MusicXML, MIDI, PDF, and
image imports remain planned adapters; they are no longer implied by this
currently executable endpoint.

## Cycle 4 Editor Checkpoint

Date: 2026-07-19

Scope: source-to-draft integrity, non-destructive legacy SQLite compatibility,
and a dependency-free structured-source editor screen. The editor accepts only
user-authored/licensed chord bars and keeps title/artist/provider fields as
metadata.

Automated evidence:

- `python -m pytest -q`: `38 passed`.
- `python -m ruff check src tests scripts`: passed.
- `python -m openapi_spec_validator contracts/openapi.yaml`: OK.
- Red-to-green migration regression: a copied legacy fixture failed before the
  SQLite compatibility migration and passed after it, including a second open.

Real HTTP evidence:

- Reproducible runner: `python scripts/run_cycle4_demo.py`.
- Saved report: `reports/cycle-4-editor-demo.md`.
- Static page fetched successfully from `127.0.0.1:8012`.
- Song create returned `201`; identical idempotent replay returned `201` with
  the same song ID.
- Authored `Am | F | Cmaj9#11 | G` returned a blocking finding on bar 3.
- Corrected `Am | F | C | G` returned a distinct immutable revision with zero
  findings; approval returned `200 APPROVED`.
- Seed creation returned `201` with canonical arrangement/version IDs,
  `ticksPerQuarter=960`, a `HARMONY` lock, and the corrected source revision.

Browser limitation: `agent-browser`, Chrome/Edge, and Chrome DevTools MCP were
not available in this environment. The evidence therefore claims HTTP/static
smoke and API behavior, not visual browser verification.

Exclusions: PDF export, generated parts, validators beyond the source review,
playback, notation, imports, model-assisted planning, learned generation,
evaluation beta, authentication, production deployment, and scale readiness
remain roadmap work.

## Cycle 5 Chart Export Checkpoint

Date: 2026-07-19

Scope: deterministic approved-source HTML/print chart artifact. The artifact
is read-only, traceable to an immutable approved source revision, and contains
title/key/ordered bars, rights attestation, source revision ID/content hash,
and `ticksPerQuarter=960`.

Automated evidence:

- `python -m pytest -q`: `39 passed`.
- `python -m ruff check src tests scripts`: passed.
- `python -m openapi_spec_validator contracts/openapi.yaml`: OK.
- Draft export regression is covered and returns `409 SOURCE_NOT_READY`.

Real HTTP evidence:

- `reports/cycle-5-chart-export-demo.md` records a `200 text/html` export after
  approval with the title, source revision ID, and content hash present.

PDF boundary: `reportlab` and `weasyprint` were unavailable. This checkpoint
does not claim PDF generation or PDF validation; authored chart PDF export
remains a roadmap item.

## Cycle 6 Generator Baseline Checkpoint

Date: 2026-07-19

Scope: deterministic rules-based drums/bass/guitar/keys candidate generation
from a canonical source-locked document, with hard source-lock, timing, range,
polyphony, schema, written/sounding range, and rights findings, collision-safe
candidate identity, and persisted generation lineage.

Evidence:

- `python -m pytest -q`: `50 passed`.
- `python -m ruff check src tests scripts`: passed.
- `python -m openapi_spec_validator contracts/openapi.yaml`: OK.
- `python scripts/run_cycle6_demo.py`: same seed replay matched, source
  harmony remained unchanged, four generated instruments were present, lineage
  was recorded, and the candidate validated against the ArrangementDocument
  schema.
- Saved report: `reports/cycle-6-generator-demo.md`.

Boundaries: this is a deterministic rules baseline, not a playability claim.
Candidate comparison, the full validator catalog, playback, scoped
regeneration, model-assisted planning, training, and evaluation remain roadmap
work.

## Cycle 7 Candidate Comparison and Validator Catalog Checkpoint

Date: 2026-07-19

Scope: bounded comparison of one to eight distinct deterministic BEGINNER
candidates from one approved source, plus machine-readable hard-validator
definitions and representative failure evidence.

Evidence:

- `python -m pytest -q`: `53 passed`.
- `python -m ruff check src tests scripts`: passed.
- `python -m openapi_spec_validator contracts/openapi.yaml`: OK.
- `python scripts/run_cycle7_demo.py`: three accepted candidates, stable
  same-seed replay, unchanged source harmony, complete lineage, and catalog
  failure evidence.
- Saved report: `reports/cycle-7-candidate-validation-demo.md`.

Boundaries: comparison summaries and catalog findings are structural evidence,
not playability, quality, audio, musician preference, or launch readiness.
Playback, scoped regeneration, notation/packets, imports, model planning,
learned generation, evaluation, deployment, and scale remain roadmap work.

## Cycle 8 MIDI Artifact and Scoped-Regeneration Integrity Checkpoint

Date: 2026-07-19

Scope: dependency-free deterministic Standard MIDI File type-1 export and
immutable `SAFE` regeneration over an explicit track/measure event scope.

Evidence:

- `python -m pytest -q`: `59 passed`.
- `python -m ruff check src tests scripts`: passed.
- `python -m openapi_spec_validator contracts/openapi.yaml`: OK.
- `python scripts/run_cycle8_demo.py`: candidate and regenerated artifacts
  validated as type 1 with six tracks and 960 TPQ; source harmony stayed
  unchanged; one scoped event changed; outside-scope hashes matched.
- Saved artifacts: `reports/cycle-8-candidate.mid`,
  `reports/cycle-8-regenerated.mid`, and
  `reports/cycle-8-midi-manifest.json`.

Boundaries: this is artifact and preservation evidence, not browser playback,
audio, musician playability, later regeneration modes, notation/packets,
imports, model planning, evaluation, or production readiness.

## Cycle 9 MusicXML and Player-Packet Integrity Checkpoint

Date: 2026-07-19

Scope: deterministic MusicXML score export plus a printable player-packet ZIP
with manifest, hashes, canonical-version lineage, and accepted-source/rights
gates.

Evidence:

- `python -m pytest tests/domain/test_notation.py tests/domain/test_packets.py -q`:
  14 passed.
- `python -m pytest -q`: 79 passed.
- `python -m ruff check src tests scripts`: passed.
- `python -m openapi_spec_validator contracts/openapi.yaml`: passed.
- `python scripts/run_cycle9_demo.py`: passed and saved
  `reports/cycle-9-score.musicxml`,
  `reports/cycle-9-player-packet.zip`, and
  `reports/cycle-9-player-packet-manifest.json`.

Boundaries: the packet is deterministic printable/player-ready artifact
basics, not a browser score renderer, PDF renderer, signed download service,
visual regression result, or four-song setlist. PDF generation and visual
browser verification remain unavailable; imports, model planning, learned
generation, evaluation, deployment, and scale remain outside this checkpoint.

## Cycle 10 MVP Candidate-Backed Playback Checkpoint

Date: 2026-07-19

Scope: candidate-projection API and local Web Audio review surface for an
accepted, rights-attested deterministic candidate, with mute/solo, loop,
metronome, count-in, and tempo override controls. The canonical candidate and
domain playback plan remain immutable.

Evidence:

- `python -m pytest tests/domain/test_playback.py tests/api/test_source_workflow.py tests/contracts/test_openapi_contract.py tests/web/test_editor_static.py -q`:
  24 passed.
- `python -m pytest -q`: 90 passed.
- `python -m ruff check src tests scripts`: passed.
- `python -m openapi_spec_validator contracts/openapi.yaml`: passed.
- `node --check web/editor.js`: passed.
- `python scripts/run_cycle10_demo.py`: passed and saved
  `reports/cycle-10-mvp-playback-demo.md`; evidence records accepted candidate
  identity, complete lineage, rights, four-track controls, arbitrary loop
  bounds, metronome, count-in, tempo override, canonical immutability, and
  browser-tool availability.
- Final verification summary: `reports/final-mvp-review.md`.

Boundaries: this is a candidate-backed local playback review surface, not
actual-audio proof, musician playability evidence, job cancellation/reconnect,
PDF rendering, hosted deployment, or later roadmap work. Browser runtime
automation was unavailable in the original local environment.

## Portfolio-Grade MVP Gate

Date: 2026-07-22

Status: **COMPLETE** for the owner-approved local portfolio-grade MVP scope.

The complete vertical slice includes the structured source editor with
invalid-bar review, immutable correction, approval, and source locking; the
deterministic four-piece candidate generator with hard validation and bounded
structural ranking; candidate-backed MIDI review controls; immutable SAFE scoped
regeneration with outside-scope preservation; and deterministic MusicXML plus
printable player-packet basics.

Final evidence:

- `reports/cycle-4-editor-demo.md`
- `reports/cycle-6-generator-demo.md`
- `reports/cycle-7-candidate-validation-demo.md`
- `reports/cycle-8-midi-regeneration-demo.md`
- `reports/cycle-9-notation-packet-demo.md`
- `reports/cycle-10-mvp-playback-demo.md`
- `reports/final-mvp-review.md`
- `python -m pytest -q`: 90 passed; Ruff, OpenAPI validation, Node syntax,
  and all Cycle 4/6/7/8/9/10 demos passed.

Known gaps and explicit exclusions: browser visual/audio automation was
unavailable; no actual-audio, musician-playability, PDF-rendering, signed
download, job cancellation/reconnect, broad import, model-assisted, learned
model, evaluation-beta, hosted-auth/deployment, or scale claim is made. These
remain roadmap work and are not started by this MVP gate.

## Post-MVP Playback-Control Defect Repair

Date: 2026-07-22

Status: **COMPLETE** for the user-reported mute/solo and role-audibility
functional defects. This does not reopen model, evaluation-beta, deployment,
or scale scope.

Evidence:

- TDD red 1: 2 failed and 8 passed, proving rendered controls lost canonical
  underscore track IDs and the scheduler lacked role-aware preview voices.
- TDD red 2 after review: 1 failed and 10 passed, proving active playback did
  not react to control changes.
- `python -m pytest -q`: 93 passed.
- Ruff, OpenAPI validation, and JavaScript syntax checks passed.
- `$env:BANDFORGE_CHROME_DEBUG_PORT='9224'; node scripts/run_playback_browser_check.mjs`:
  exit 0 against the running `127.0.0.1:8012` screen.
- Browser evidence: `reports/playback-controls-fixed-browser.json` and `.png`.
- Repair report: `reports/playback-controls-fix.md`.
- Fresh acceptance reviewer `019f89fe-9793-7d73-a3df-b5e56ea27f7f` returned
  CLEAN after 11 focused tests and both Node syntax checks.

The live browser observed generated drums, bass, guitar, and keys together;
each individual mute and solo while playback was already active; matching API
control payloads/active tracks; actual oscillator starts with distinct role
profiles; zero source-guide audio events; and zero console problems.

Boundary: control changes restart playback at the selected loop boundary.
Seamless mid-beat gain automation, human listening-quality assessment,
professional sampled timbres, mix-balance validation, and MuseScore mapping
repairs are not claimed.

## Post-MVP Acoustic Preview and Overlap Repair

Date: 2026-07-22

Status: **COMPLETE** for the user-reported synthetic-timbre, limited-drum, and
stacked Stop/replay defects.

Evidence:

- TDD red: 4 failed/30 passed for session cancellation, abort handling,
  replay intent, and expanded drums; the sampler gate also failed before asset
  integration.
- Focused green: 35 passed and JavaScript syntax passed.
- Final full suite: 97 passed; semantic OpenAPI, Cycle 6, and Cycle 10 demos
  passed. Final lint evidence is recorded in the closure report/ledger.
- Isolated Chrome against the deployed local screen/API observed four roles,
  four mute and four solo cases, zero pitched-track oscillators, 33 generated
  drum events, 12 stopped sample sources, exact 12-of-12 non-stacked rapid
  replay scheduling, and zero console problems.
- Evidence: `reports/acoustic-preview-overlap-fix.md` and
  `reports/playback-controls-fixed-browser.{json,png}`.

Boundary: local CC BY 3.0 FluidR3 samples improve instrument identity but do
not prove professional arrangement quality, mix quality, playability, or a
MuseScore-specific sound-bank result. No model, private-beta, hosted
deployment, evaluation-beta, or scale work was started.

## Browser Evidence Reconciliation

The original Cycle 4-10 gate reports correctly say browser automation was not
available in that earlier verification environment. The later 2026-07-22
playback repairs used an isolated local Chrome run and saved
`reports/playback-controls-fixed-browser.json` and `.png`. These are not
conflicting claims: the later browser evidence verifies the post-MVP playback
repair only; it does not retroactively establish browser evidence for the
original MVP gate, human listening quality, or professional arrangement
quality.
