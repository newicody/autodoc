# Scheduler runtime bootstrap registry attachment - 0258

## Intent

0258 attaches the 0257 registry to Scheduler bootstrap.

```text
OpenRC -> launcher -> Scheduler -> runtime registry -> runtime components
```

Scheduler owns the registry attachment.  The launcher remains bootstrap-only.
OpenRC remains a process supervisor.

## What changes

The patch adds a small attachment helper that can attach the validated 0257
registry payload to an existing Scheduler object.

This is intentionally not a runtime manager.  There is no RuntimeManager.

The attachment records:

```text
registry_component_ids
capability_index
dependency_index
lifecycle_steps
```

## Boundary

0258 does not instantiate components, start components, connect to PostgreSQL,
run OpenVINO, call Qdrant, call GitHub, publish EventBus messages, or modify
Scheduler.run.

The required wording is: does not modify Scheduler.run.

The Scheduler does not start PostgreSQL, Qdrant, OpenVINO drivers, OpenVINO
runtime services, or external system daemons.  OpenRC and the host operating
system own those external service lifecycles.

Scheduler owns Autodoc runtime objects that use external services:

```text
SQLContextStore uses PostgreSQL
OpenVINOEmbeddingService uses OpenVINO/model/device resources
QdrantProjectionStore uses Qdrant
```

EventBus remains observation-only.

Smoke tools remain validation helpers only.  There is no CLI per component as
the runtime API.

## Next step

0259 can start adapting real SQL execution through Scheduler ownership, using
the existing `DbApiSqlContextStore` controlled write surface.
