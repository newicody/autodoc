# Scheduler-owned runtime component lifecycle - 0254

## Intent

This patch pivots the production sequence from readiness-only artifacts toward
Scheduler-owned runtime execution.

```text
OpenRC -> launcher -> Scheduler
```

Scheduler owns runtime components.  The launcher is bootstrap-only.  OpenRC
supervises the process and must not become an internal runtime orchestrator.

## Runtime ownership

The Scheduler owns runtime components and their lifecycle:

```text
Scheduler
  -> ComponentRegistry
  -> validate
  -> instantiate
  -> start
  -> health
  -> stop
```

Initial Scheduler-managed components:

```text
EventBus
PassiveSupervisorSink
SQLContextStore
OpenVINOEmbeddingService
QdrantProjectionStore
GitHubArtifactExchange
```

## Command path and observation path

```text
Scheduler -> handlers/capabilities -> runtime components
EventBus -> PassiveSupervisorSink -> CellularState
```

EventBus remains observation-only.  It carries facts, refs, summaries, and
telemetry.  It does not become a command path.

## No CLI per component

The required wording is: no CLI per component.

The runtime API must not become one CLI per component.

Patch smoke tools are temporary validation helpers.  Production execution should
go through the Scheduler-owned objects, not through separated component CLIs.

## Execution phase

The execution phase is opened from this point forward.  New production patches
should expose explicit controlled execution gates where mutation is possible,
for example `--execute` plus a decision identifier, but the owned runtime path
must remain Scheduler-centered.
