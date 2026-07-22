# ADR-007: User Files and Datasets Are Excluded From Training by Default

## Status

Accepted.

## Context

Charts may be private, commercially copyrighted, or entrusted to a workspace
for one performance. Public datasets also have layered code, data, composition,
recording, and attribution rights.

## Decision

Do not use user content for model training without separate explicit consent and
an approved program. Require a dataset registry and rights review before every
training source. Store lineage through training, checkpoint, and evaluation.

## Alternatives

- Product-usage terms imply training consent: rejected as insufficiently clear.
- Use every public MIDI repository: rejected because public availability and
  software licenses do not establish composition rights.

## Consequences

Early custom-model data grows slowly, so rules and authored/licensed style packs
remain important. Rights provenance becomes part of ML operations.

