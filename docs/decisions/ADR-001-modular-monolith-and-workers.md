# ADR-001: Modular Monolith and Asynchronous Music Workers

## Status

Accepted for initial implementation.

## Context

Product CRUD and version changes need simple transactions. Import, generation,
validation, notation, and audio work can be slow, memory-heavy, retried, or later
GPU-backed. Python has the relevant music ecosystem, while the web client is best
served by TypeScript.

## Decision

Use one monorepo and control-plane deployment with strongly bounded modules.
Delegate expensive work to Celery Python workers through Redis. PostgreSQL is
durable state; the broker is not. Scale worker queues independently before
extracting services.

## Alternatives

- One TypeScript process: rejected because it weakens the music-engine ecosystem
  and subprocess lifecycle.
- Microservices/event bus: rejected for MVP because distributed operations and
  contracts add more risk than user value.

## Consequences

Local development needs several containers, and job idempotency is mandatory.
The music domain remains framework-independent, allowing later extraction.

