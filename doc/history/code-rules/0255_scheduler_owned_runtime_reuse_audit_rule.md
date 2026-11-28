# Code rule 0255 - Scheduler-owned runtime reuse audit

Before adding Scheduler-owned runtime execution code, audit existing surfaces.

Required:

```text
reuse existing surfaces before new runtime code
audit first, adapt second
Scheduler owns runtime components
no CLI per component
```

The audit may add a temporary smoke tool.  It must not add a new runtime manager,
new bus, new orchestrator, or component-specific production CLI.
