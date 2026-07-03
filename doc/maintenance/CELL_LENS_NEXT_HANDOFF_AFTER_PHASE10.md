# Cell Lens Next Handoff After Phase 10

Phase 10 created enough UI for local observation.

The next tranche should avoid adding more UI until the observation production
path is connected to real recorded events.

## Current stable read side

```text
missipy.cell.v1 journal
replay/tail reader
SSE stream
VisPy desktop
browser Canvas
browser health Canvas
```

## Next allowed work

```text
recorded observation producer
journal writer integration
replay compatibility checks
source_class lifetime registry
operator runbook
```

## Still forbidden

```text
browser command channel
SSE command channel
journal command channel
EventBus command channel
remote mutation
optimization loop
autonomous agent
```

## Command separation

Any future action must remain:

```text
typed command → Scheduler
```

The observation side must remain:

```text
events → snapshots → journal → views
```
