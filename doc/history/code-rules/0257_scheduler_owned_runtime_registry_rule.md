# Code rule 0257 - Scheduler-owned runtime registry

Required:

```text
Scheduler-owned runtime registry
reuse source map from 0256
Scheduler owns runtime components
selected_from_existing_surfaces
no CLI per component
no RuntimeManager
```

Forbidden:

```text
new runtime manager
new orchestrator
launcher-owned lifecycle
component-specific production CLI runtime API
EventBus command path
Scheduler.run modification
```

0258 may attach this registry to Scheduler bootstrap.  0257 must not instantiate
or execute runtime components.
