# Production server initial configuration requirements - 0240

## Intent

This patch defines the initial production server configuration required before
later phases activate the Autodoc runtime.

It is not a deployment system and it does not start the system.

## Runtime direction

```text
OpenRC -> launcher -> Scheduler -> handlers/components
```

OpenRC starts the launcher. The launcher validates the production server
configuration and builds the runtime surface in later phases. The Scheduler
remains the orchestration authority.

## Observation direction

```text
EventBus -> PassiveSupervisorSink -> CellularState
```

EventBus is the observation path. It is not the command path. PassiveSupervisor
remains downstream and cannot become runtime authority.

## Durable and projection stores

PostgreSQL is the durable authority. Qdrant is a projection and recall surface.
Qdrant payloads must carry `sql_ref` so recall can rehydrate through SQL.

## GitHub integration

GitHub is an artifact exchange surface until a reviewed adapter explicitly
publishes remote mutations.

Initial requirements:

```text
token_env = GITHUB_TOKEN
repository_allowlist_required = true
mode = artifact_exchange
copilot_advisory_only = true
publication_review_required = true
publish_enabled_by_default = false
scan_once_writes_sql = false
scan_once_writes_qdrant = false
```

The production server may import GitHub ticket/project artifacts as source
candidates, but GitHub does not become the runtime authority. Copilot output is advisory only.
publication review is required before pushing results back to a GitHub Project/Kanban surface.

## INI sections

The production server configuration reserves these INI sections:

```text
server
openrc
component.scheduler
component.eventbus
component.sql_context_store
component.qdrant_projection
component.github_artifact_exchange
component.passive_supervisor_sink
postgresql.connection
postgresql.table.context_records
postgresql.table.event_journal
postgresql.table.result_frames
postgresql.table.github_project_push_frames
qdrant.connection
qdrant.collection.autodoc_context_e5_small
github
github.repositories
github.artifacts
github.publication
eventbus.attributes
```

No ConfigObj dependency is added in this patch. The layout is compatible with a
future ConfigObj parser while remaining stdlib-only here.

## Advanced EventBus attributes

Objects may expose event fields only through an allowlist. Required baseline
fields are:

```text
schema_version
event_type
trace_id
component
phase
```

Optional fields include `intent_id`, `result_id`, `sql_ref`, `qdrant_ref`,
`github_ref`, `project_push_frame_ref`, `payload_hash`, and `priority`.
Sensitive fields must be redacted before an event envelope is published.

## Boundary

This phase is requirements-only. It does not start OpenRC, instantiate Scheduler
or EventBus, start threads, publish events, call GitHub, publish to GitHub,
execute PostgreSQL DDL/DML, or create Qdrant collections.
