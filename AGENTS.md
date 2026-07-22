# BandForge Agent Instructions

Read `README.md` and every document directly relevant to the requested slice
before changing code. The design dossier is authoritative until a newer ADR
explicitly supersedes a decision.

## Non-Negotiable Product Rules

- Do not derive chords or copyrighted notation from a song title, Spotify item,
  or MusicBrainz recording. Those sources are metadata only.
- Do not present generated output as flawless, authoritative, or guaranteed
  playable. Surface validator findings and require user review.
- Keep `ArrangementDocument` as the canonical musical state. MusicXML, MIDI,
  PDF, SVG, ChordPro, and audio are generated or imported representations.
- Preserve arrangement versions. Never overwrite the accepted version during
  regeneration.
- Every generation must record seed, engine version, style-pack version,
  validator version, input revision, and provenance.
- Hard validator failures block `READY`; warnings do not silently disappear.
- Treat uploaded files and third-party API responses as untrusted.
- Do not train on user uploads unless the user separately and explicitly opts
  in to an approved training-data program.

## Engineering Rules

- Implement one vertical slice at a time and keep the repository runnable.
- Define or update contracts before implementations that cross module
  boundaries.
- Validate external input once at the boundary; use typed domain objects inside.
- Business and music logic must not live in route handlers or UI components.
- Every job is idempotent and resumable or explicitly marked non-retryable.
- Pin dependencies in lockfiles. Verify exact versions against official
  documentation at implementation time.
- Add unit, contract, integration, and workflow tests in proportion to risk.
- Save benchmark and evaluation output before making quantitative claims.
- Update the affected design document or add an ADR before changing an accepted
  architectural decision.

## Definition of Done for a Slice

The acceptance criteria pass; unit and integration tests pass; type checking,
linting, and production builds pass; a happy path and relevant failure path are
verified; documentation and fixtures are updated; no placeholder behavior is
left in a production path.

## Automatic Skill Discovery and Loading

Every master agent, subagent, implementer, reviewer, and verification worker
must begin its assigned task by reading and following
`agent-skills:using-agent-skills`. It must classify the task phase, discover the
applicable skills, and load those skill files before taking task actions.

Skills are selected by relevance, not loaded indiscriminately:

- planning/specification: `spec-driven-development`,
  `planning-and-task-breakdown`, and `documentation-and-adrs`;
- implementation: `incremental-implementation` and
  `test-driven-development`;
- frontend: `frontend-ui-engineering`, relevant framework skills, and
  `browser-testing-with-devtools`;
- API/domain: `api-and-interface-design` and
  `source-driven-development`;
- debugging: `debugging-and-error-recovery` or
  `superpowers:systematic-debugging`;
- review: `code-review-and-quality`, `code-simplification`, and
  `superpowers:requesting-code-review` when applicable;
- verification: `superpowers:verification-before-completion` plus every
  domain-specific build, contract, browser, security, or performance skill
  required by the slice;
- shipping: `git-workflow-and-versioning`, `ci-cd-and-automation`, and
  `shipping-and-launch` when the repository state supports those actions.

The orchestrating agent must attach explicit skill items or absolute skill
paths when spawning a worker whenever the agent tool supports structured skill
inputs. Natural-language skill names alone are not sufficient when attachment
is available.

Each worker report and `.superpowers/sdd/progress.md` entry must record:

1. skills loaded;
2. why each skill applied;
3. required verification commands and their results;
4. any relevant skill that could not be loaded and the fallback used.

If no specialized skill applies, the worker must record that decision and
continue with the project instructions. A worker must never silently skip a
clearly applicable skill or load unrelated skills merely to increase the count.
