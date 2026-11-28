# Code rule 0258 - Scheduler runtime bootstrap registry attachment

Required:

```text
Scheduler runtime bootstrap registry attachment
Scheduler owns the registry attachment
launcher remains bootstrap-only
no RuntimeManager
does not modify Scheduler.run
Scheduler owns Autodoc runtime objects, not external service daemons
```

Forbidden:

```text
new runtime manager
new parallel orchestrator
launcher-owned lifecycle
component instantiation in 0258
component start in 0258
component-specific production CLI runtime API
EventBus command path
Scheduler starts PostgreSQL
Scheduler starts Qdrant
Scheduler starts OpenVINO external services
```

0259 may adapt real SQL execution through Scheduler ownership.  0258 only
attaches the validated registry metadata to Scheduler bootstrap.
