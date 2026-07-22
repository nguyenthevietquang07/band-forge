# ADR-003: Hybrid Hierarchical Generation Before Custom Training

## Status

Accepted.

## Context

Training a useful multitrack arranger requires legally usable data, representation
work, GPU resources, evaluation, and musician feedback. Those do not exist at
project start. The product can still create value through coordinated rules,
licensed patterns, and optional model planning.

## Decision

Implement seeded hierarchical style rules first, then retrieval and structured
model-assisted plans, then a conditional symbolic model behind the same
interfaces only after it beats the baseline. Generate pulse, foundation,
comping, and decorative roles in that order.

## Alternatives

- Train from scratch first: rejected for product and rights risk.
- General LLM directly emits the final score: rejected for timing, feasibility,
  consistency, and observability risk.
- Prompt-to-audio generation: rejected because musicians need editable notation
  and per-player parts.

## Consequences

The MVP is explainable and CPU-runnable. Style-pack authoring is real product
work. Model integration cannot bypass domain validation.

