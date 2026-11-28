# Scheduler-owned runtime registry - 0257

## Intent

0257 builds the Scheduler-owned runtime registry from the reuse source map from
0256.

The required wording is: reuse source map from 0256.

It is aligned with the corrected development axis:

```text
0254 -> Scheduler owns runtime components
0255 -> audit existing surfaces
0256 -> filtered source map
0257 -> registry of existing surfaces owned by Scheduler
```

## Ownership

Scheduler owns runtime components.

The launcher remains bootstrap-only.  OpenRC remains a process supervisor.
EventBus remains observation-only.

## Registry shape

The registry maps component ids to existing implementation surfaces:

```text
eventbus -> src/kernel/event_bus.py
passive_supervisor_sink -> passive supervisor source surfaces
sql_context_store -> existing DbApiSqlContextStore controlled write surface
openvino_embedding_service -> existing OpenVINO/E5 surface
qdrant_projection_store -> existing Qdrant projection/recall surfaces
github_artifact_exchange -> existing ProjectPushFrame / GitHub artifact surfaces
```

## Runtime API boundary

The registry is not a RuntimeManager.  There is no RuntimeManager.

The registry does not instantiate components, start components, call
Scheduler.run, open PostgreSQL, run OpenVINO, call Qdrant, call GitHub, or
publish EventBus messages.

There is no CLI per component.  Smoke tools remain validation helpers only.

## Next step

0258 will attach this registry to Scheduler bootstrap without changing
Scheduler.run.
