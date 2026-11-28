# Qdrant real binding preview-first CLI — 0283-r7

## Purpose

Expose the existing 0283 real-Qdrant chain through one operational CLI while
preserving explicit boundaries between preview, live readiness and data
effects.

```text
architecture_preserved: true
preview_first: true
existing_r2_configuration_reused: true
existing_r4_projection_binding_reused: true
existing_r5_recall_binding_reused: true
existing_r6_readiness_reused: true
```

## Default

Running the tool without effect arguments performs only local readiness:

```text
configuration r2
→ dependency/factory inspection r6
→ no Qdrant client
→ no network
→ no SQL store
→ no data effect
```

## Independent gates

A live metadata read requires:

```text
--live-readiness
```

A projection effect requires all of:

```text
--operation projection
--execute
--live-readiness
--authorize-projection
--policy-decision-id <typed decision>
--embedding-report <json>
```

A recall effect requires all of:

```text
--operation recall
--execute
--live-readiness
--authorize-recall
--policy-decision-id <typed decision>
--embedding-report <json>
```

Projection authorization cannot authorize recall and recall authorization
cannot authorize projection.

```text
live_readiness_is_explicit: true
operation_authorization_is_explicit: true
projection_authorization_separate: true
recall_authorization_separate: true
```

## Readiness before effect

Execute mode always runs r6 live readiness first. The requested action is not
called unless:

```text
operational_ready = true
and projection_ready = true
```

or:

```text
operational_ready = true
and recall_ready = true
```

## SQL authority

Recall opens the existing SQLite authority only after live readiness succeeds.
It opens the existing database with SQLite URI `mode=ro` and wraps the
connection with the existing `DbApiSqlContextStore`.

Preview recall passes no open SQL connection because 0263 performs no SQL read
in preview mode.

## Current constraints

The first CLI intentionally supports the current local architecture only:

```text
Qdrant endpoint = loopback
transport = existing strict gRPC
collection = autodoc_context_embeddings
dimension = 384
distance = Cosine
SQL authority = existing SQLite file
```

Remote endpoints and PostgreSQL CLI wiring remain outside r7.

## Non-goals

```text
collection_created: false
collection_updated: false
collection_deleted: false
qdrant_started: false
scheduler_modified: false
new_scheduler_added: false
new_qdrant_executor_added: false
new_transport_added: false
control_proxy_integrated: false
event_bus_integrated: false
shm_or_mmio_integrated: false
projects_repository_change_required: false
external_dependencies_added: false
```
