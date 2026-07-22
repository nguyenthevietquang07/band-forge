# ADR-004: Deterministic Validation Gates Creative Output

## Status

Accepted.

## Context

Generative models optimize likelihood or preference, not strict bar accounting,
source locks, instrument range, file validity, or user-level constraints. Asking
the same model to certify itself does not provide independent assurance.

## Decision

Run versioned deterministic hard validators on every candidate. Permit only
bounded local repairs. Reject unrepairable candidates. Rank only hard-valid
candidates, retain warnings, and require human playback/score review.

## Alternatives

- Model self-critique only: rejected as non-independent and hard to reproduce.
- Rules only with no human review: rejected because musical quality and personal
  comfort are not fully formalizable.

## Consequences

Rule packs and instrument profiles become maintained product assets. Results can
be withheld honestly instead of being presented as flawless.

