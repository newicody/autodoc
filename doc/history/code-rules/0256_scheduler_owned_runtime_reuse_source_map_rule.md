# Code rule 0256 - Scheduler-owned runtime reuse source map

Required:

```text
in line with 0254 and 0255
Scheduler owns runtime components
reuse existing implementation surfaces
audit first, adapt second
last audit before adaptation
no CLI per component
```

Forbidden:

```text
new RuntimeManager
new parallel orchestrator
launcher-owned lifecycle
EventBus command path
component-specific production CLI
```

0256 may add a temporary smoke tool for building the source map.  That tool is
not a runtime API.
