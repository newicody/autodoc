# Scheduler-owned runtime reuse audit - 0255

## Intent

This patch enforces the no-reinventing-wheel direction before production
execution code is added.

The required rule is:

```text
reuse existing surfaces before new runtime code
```

## Relation to 0254

0254 established:

```text
OpenRC -> launcher -> Scheduler
Scheduler owns runtime components
EventBus remains observation-only
no CLI per component
```

0255 does not add runtime ownership code.  It audits the repository to locate
existing surfaces that must be reused or adapted first.

## Audit-first direction

```text
audit first, adapt second
```

The audit searches for existing surfaces:

```text
Scheduler
EventBus
PassiveSupervisorSink
SQLContextStore / DbApiSqlContextStore
OpenVINO / multilingual-e5-small
Qdrant
GitHubArtifactExchange / ProjectPushFrame
```

## Boundary

The audit is read-only.  It does not import target modules, instantiate
components, call Scheduler.run, connect to PostgreSQL, run OpenVINO, call
Qdrant, call GitHub, or publish events.

The output is a report for deciding which existing modules to reuse in the next
production execution patches.
