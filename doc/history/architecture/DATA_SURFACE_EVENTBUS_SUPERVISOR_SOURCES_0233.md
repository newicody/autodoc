# 0233 — Data-surface EventBus supervisor sources

This patch extends the existing passive bus supervisor module with canonical
data-surface EventBus events.

The path remains:

```text
GitHub artifact / SourceCandidate / SQL / Qdrant / Rehydration / Pushback
  -> existing EventBus
  -> PassiveSupervisorSink / cellular snapshot projection
```

The patch does not add a new bus and does not create a parallel runtime.

## Added observed surfaces

The data-surface cell kinds are:

```text
GITHUB_ARTIFACT
SOURCE_CANDIDATE
SQL_STORE
QDRANT_PROJECTION
REHYDRATION
PUSHBACK
```

They are represented as first-class observation cells so that future GitHub,
SQL, Qdrant, rehydration, and pushback flows can be supervised without giving
the supervisor authority over those flows.

## Authority boundary

The helpers are data-only. They do not:

```text
call GitHub APIs
mutate issues/projects/comments/labels/status
promote/reject SourceCandidate objects
read/write SQL
query/upsert Qdrant
execute rehydration
send pushback
call Scheduler.run()
control proxy or SHM
decide policy
```

## Reuse rule

This patch updates the existing module:

```text
src/context/passive_bus_supervisor_cellular_snapshot.py
```

It reuses:

```text
BusSupervisorEvent
build_cellular_snapshot
PassiveSupervisorSink
authority_boundary
```

No new supervisor module, bus, scheduler, persistence writer, Qdrant adapter,
or GitHub client is introduced.

## Snapshot and audit

Snapshot and audit remain optional outputs. The normal runtime path is still
EventBus -> passive supervisor, not EventBus -> events.jsonl -> supervisor.
