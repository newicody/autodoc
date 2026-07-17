# Phase 0287-r7-r15-r3-r2 — manual runtime configuration and provider binding

## Decision

The installed prototype uses one unversioned local INI for machine-specific
PostgreSQL, Qdrant and OpenVINO values.  Passwords and API keys remain in named
environment variables.  The canonical provider is versioned in Autodoc and is
no longer typed manually by the operator.

The provider does not create another Scheduler.  The canonical server bootstrap
must register its already-composed `ImportedActionsRuntimePorts`; the provider
runs read-only backend readiness and returns those exact ports.

## Installed target

- PostgreSQL: `127.0.0.1:5432`, database/schema/user `autodoc`;
- Qdrant: `http://127.0.0.1:6333`, alias `autodoc_context_current`;
- embedding: OpenVINO multilingual E5 small, CPU, dimension 384;
- Qdrant distance: Cosine;
- SQL remains durable authority and Qdrant returns references only.

## Readiness effects

- PostgreSQL: one `SELECT` through `psql`;
- Qdrant: `GET /readyz` and `GET /collections/<alias>`;
- OpenVINO: import, device discovery, model read and optional compilation;
- no SQL write, Qdrant mutation or model inference;
- no secret value is serialized.

## Follow-up

The next unit binds the canonical server bootstrap to
`register_installed_runtime_ports()` and captures the first live preview
attestation.  This phase deliberately does not invent a second Scheduler or a
parallel runtime manager.
