# Implementation Roadmap

This roadmap is ordered by dependency and proof, not by visual excitement. Each
milestone is a complete vertical slice with a demo and saved evidence. Detailed
task planning begins after product-spec review.

## 0. Repository and Contract Foundation

Deliver:

- monorepo skeleton for web, API, worker, contracts, music domain, fixtures;
- pinned runtimes and lockfiles, Docker Compose for PostgreSQL/Redis/object store;
- CI for lint, type, unit, contract, build, security basics;
- generated/validated Python and TypeScript contract types;
- local health endpoints, request IDs, structured logging;
- decision and release-document conventions.

Gate: clean-clone setup runs one command; API, worker, DB, Redis, and storage are
healthy; schema examples pass in both languages.

## 1. Structured Source and Chord Chart

Current status (2026-07-19): the structured-source editor, blocking finding
review, immutable correction flow, explicit approval, and source-locked seed
are implemented and demonstrated in `reports/cycle-4-editor-demo.md`. PDF
export remains roadmap work; the deterministic HTML/print chart artifact is
implemented and demonstrated in `reports/cycle-5-chart-export-demo.md`.

The first deterministic four-piece baseline is also implemented in the domain
layer: same source and seed reproduce the same schema-valid candidate, and hard
source-lock/rights/schema/timing/written-and-sounding-range/polyphony findings
block acceptance; complete lineage and collision-safe candidate IDs are
persisted. The bounded evidence is in `reports/cycle-6-generator-demo.md`.
Style packs beyond the baseline,
playability evaluation, and later regeneration modes remain outside the
approved MVP.

Cycle 8 artifact/integrity work is implemented and demonstrated in
`reports/cycle-8-midi-regeneration-demo.md`: deterministic type-1 MIDI export,
structural validation, and immutable SAFE scoped regeneration with exact
outside-scope hash preservation. Cycle 9 MusicXML/player-packet basics are
implemented and demonstrated in `reports/cycle-9-notation-packet-demo.md`.
Cycle 10 candidate-backed local playback controls are implemented and
demonstrated in `reports/cycle-10-mvp-playback-demo.md`. Post-MVP repairs add
live mute/solo replanning, a pinned local sampled-acoustic preview, expanded
deterministic drum events, and stale-session/timer/source cancellation with
isolated-Chrome evidence in `reports/acoustic-preview-overlap-fix.md`. Human
listening-quality and professional-arrangement claims, worker-job cancellation/
reconnect, later regeneration modes, PDF rendering, and later roadmap stages
remain unimplemented.

Cycle 7 candidate comparison and the machine-readable validator catalog are
implemented and demonstrated in `reports/cycle-7-candidate-validation-demo.md`.
The summaries are structural evidence only; they do not rank musical quality
or establish playability. Human musician review and playability evaluation
remain outside the approved MVP.

Deliver:

- workspace/song/source records;
- structured section/bar/harmony editor;
- chord-text parser and review findings;
- source approval and immutable revisions;
- canonical measure/harmony document;
- simple chord-chart screen and PDF export.

Gate: a user enters the reference 16-bar fixture, resolves an invalid bar, locks
the approved source, and exports a correct chart. No AI is required.

## 2. Arrangement Domain and Deterministic Four-Piece Generator

Deliver:

- arrangement controls, tracks, roles, locks, and versions;
- acoustic-pop and pop-rock style packs;
- seeded drums -> bass -> guitar -> keys generation;
- two candidates with documented differences;
- structure, range, polyphony, harmony-fit, collision, and lock validators;
- candidate ranking and findings UI.

Gate: same seed is semantically reproducible; different seeds meet the variation
band; 100% of frozen fixtures either yield a hard-valid candidate or a clear
`NO_VALID_CANDIDATE` result.

## 3. MIDI Playback and Scoped Regeneration

Deliver:

- MIDI type-1 exporter and artifact validation;
- browser preview with mute/solo, loop, metronome, count-in, tempo override;
- section/track/bar scope selection;
- `SAFE`, `FRESH`, `SIMPLIFY`, and `SPICE_UP` modes;
- diff view and exact preservation proof outside scope;
- cancellation and reconnectable job progress.

Gate: regenerate chorus guitar only, retain identical hashes and IDs elsewhere,
hear both versions, cancel another job safely, and recover after refresh.

## 4. MusicXML Notation and Player Packets

Deliver:

- MusicXML 4.0 export validated against local XSD;
- OpenSheetMusicDisplay score/player rendering and cursor sync;
- transposed/written parts and instrument profiles;
- full score, player PDFs, chord chart, MIDI, and setlist ZIP;
- artifact manifest, hashes, signed downloads;
- visual regression and empty/overflow checks.

Gate: a four-song test setlist exports a readable packet; every file passes
schema/parser/smoke checks and is traceable to the accepted version.

## 5. Import Adapters

Deliver in order:

1. ChordPro text with preserved unknown directives;
2. MusicXML import with unsupported-feature findings;
3. MIDI import with track/grid review;
4. PDF/image secure reference upload and manual side-by-side entry;
5. optional OMR experiment behind a feature flag after license/security review.

Gate: import -> review -> approval -> generation uses no hidden assumptions, and
the original source remains downloadable and hash-linked.

## 6. Model-Assisted Planner and Reharmonization

Deliver:

- provider-neutral model gateway with structured output, timeout, budget, and
  rules-only fallback;
- high-level role/energy/texture planner;
- licensed style-pattern retrieval;
- explainable reharmonization proposals with melody/lock checks;
- provider manifests, cost telemetry, prompt-injection tests;
- offline A/B evaluation against deterministic planning.

Gate: the planner improves a predeclared musician preference measure without
degrading hard validity, latency budget, privacy, or reproducibility metadata.

## 7. Evaluation Beta

Deliver:

- frozen fixture/evaluation corpora and dataset registry;
- objective reports by style/instrument/difficulty;
- musician review workflow and blinded comparison template;
- feedback by track/bar, validator override analytics;
- model/style cards and explicit unsupported combinations;
- production SLO dashboards and incident runbooks.

Gate: at least five target users complete the full gig-packet workflow and the
team has evidence about time saved, playability, corrections, failures, and
retention. Do not invent a launch metric threshold before baseline data exists.

## 8. Learned Symbolic Generator Research

Deliver as a separate research track:

- legally approved dataset manifests and deduplicated work-level splits;
- synchronized multitrack tokenizer and baseline statistics;
- conditional/inpainting model prototype in Colab or managed GPU environment;
- rules baseline and ablations;
- memorization, control-adherence, validity, diversity, latency, and listening
  evaluation;
- model card, checkpoint provenance, and rollback path.

Gate: the model clears every release criterion in the generation design. Until
then it remains research and does not block the product.

## 9. Public Beta and Scale

Deliver:

- production tenant/auth configuration and deletion workflow;
- quotas, abuse controls, cost limits, backups, restore drill;
- deployment, migration, rollback, on-call, rights complaint runbooks;
- onboarding and sample content that is authored or safely licensed;
- measured load, reliability, and security reports;
- owner-set `human_verified: true` before market-ready status.

Gate: fresh user can create and export a packet without private help; one happy
path and major failure paths are demonstrated in production-like staging;
launch gaps and limitations are explicit.

## 10. Work That Can Run in Parallel

After contracts and domain invariants stabilize:

- web source editor and API source service;
- style-pack authoring and domain validator fixtures;
- infrastructure/CI and object-storage adapter;
- notation/playback research against fixed MusicXML/MIDI fixtures;
- security threat fixtures and dataset registry.

Do not parallelize competing edits to the canonical schema, job state machine,
or generation semantics without one owner and contract review.

## 11. Major Risks and Mitigations

| Risk | Probability/impact | Mitigation |
|---|---|---|
| Scope expands into DAW/transcription/practice app | high/high | enforce MVP non-goals and milestone gates |
| "AI" work delays useful product | high/high | deterministic vertical slices first |
| Generated parts are valid but dull | medium/high | multiple candidates, style packs, human evaluation, learned planner later |
| Output is interesting but unplayable | medium/high | instrument profiles, hard constraints, player-specific review |
| Dataset rights are unclear | high/high | registry and legal gate; authored/licensed data only |
| OMR is inaccurate or operationally awkward | high/medium | manual upload flow useful without OMR; optional adapter |
| MusicXML/MIDI round trips lose semantics | medium/high | canonical domain model and golden interoperability fixtures |
| Hosted model is nondeterministic/costly | medium/medium | manifests, budget, timeout, rules fallback, no default until measured |
| Microservices consume project time | medium/high | modular monolith; extract only measured bottlenecks |

## 12. Portfolio Proof Artifacts

Save, do not merely describe:

- architecture and ADRs;
- canonical schema and generated contract docs;
- deterministic fixture reports;
- validator rule catalog and failure examples;
- MusicXML/MIDI/PDF interoperability report;
- scoped-regeneration preservation report;
- latency/memory/cost benchmark with environment metadata;
- security and malicious-upload test report;
- blinded musician evaluation method/results;
- demo video and public sample packet using safe source music.

Resume claims must reference these artifacts and distinguish completed product
evidence from roadmap work.
