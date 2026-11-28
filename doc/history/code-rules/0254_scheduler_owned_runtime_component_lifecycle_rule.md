# Code rule 0254 - Scheduler-owned runtime component lifecycle

Required:

```text
OpenRC -> launcher -> Scheduler
Scheduler owns runtime components
EventBus remains observation-only
no CLI per component
```

The launcher is bootstrap-only.  Runtime components are instantiated and managed
by the Scheduler.

Forbidden:

```text
parallel runtime orchestrator
launcher-owned component lifecycle
EventBus command path
component-specific production CLI as runtime API
```
