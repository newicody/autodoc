# Production server INI validation - 0241

## Intent

This patch adds production server INI validation for the initial server
configuration defined in phase 0240.

The INI layout is ConfigObj-compatible, but this patch uses stdlib
`configparser` so no non-stdlib dependency is introduced.

No runtime service is started.

## Validated areas

```text
server paths
OpenRC launcher command/configtest
component factories
PostgreSQL connection and table sections
Qdrant connection and collection shape
GitHub artifact exchange settings
EventBus attribute allowlist
```

## GitHub boundary

GitHub remains artifact exchange. The required initial settings are:

```text
token_env = GITHUB_TOKEN
mode = artifact_exchange
publish_enabled_by_default = false
publication_review_required = true
```

The scan-once entrypoint is recorded, but this patch does not call GitHub and
does not write SQL or Qdrant during validation.

## Qdrant boundary

The initial collection section must keep:

```text
vector_dimension = 384
distance = cosine
required_payload includes sql_ref
```

Qdrant is still projection/recall only. SQL remains the durable authority.

## EventBus attributes

The required event attribute list must include:

```text
schema_version, event_type, trace_id, component, phase
```

Optional attributes may include `sql_ref`, `qdrant_ref`, `github_ref`, and
`project_push_frame_ref`. Sensitive optional attributes are listed separately in
`optional_redacted`.

## Boundary

This phase only validates a local INI file and can write a JSON validation
report. It does not start OpenRC, create Scheduler/EventBus, publish events,
call GitHub, publish to GitHub, execute PostgreSQL DDL/DML, or create Qdrant
collections.
