# Scheduler-owned runtime reuse source map - 0256

## Intent

This patch is in line with 0254 and 0255.

0254 fixed the ownership boundary:

```text
OpenRC -> launcher -> Scheduler
Scheduler owns runtime components
no CLI per component
```

0255 proved that all required runtime surfaces exist, but its report was broad
and intentionally noisy.

0256 narrows that result into a source map so that the next patches reuse
existing implementation surfaces instead of inventing new wheels.

The required wording is: reuse existing implementation surfaces.

## Last audit before adaptation

This is the last audit before adaptation.

The next patches should adapt existing Scheduler, EventBus, SQL, OpenVINO,
Qdrant, GitHub, and PassiveSupervisor surfaces under Scheduler ownership.

## Filtered source selection

The source map excludes:

```text
.aider.chat.history.md
PHASE*.md
doc/
.var/
patch/
__pycache__/
*.pyc
```

It focuses on implementation paths:

```text
src/
tools/
tests/
```

## Boundary

The source map is read-only.  It does not import target modules, instantiate
components, call Scheduler.run, connect to PostgreSQL, run OpenVINO, call
Qdrant, call GitHub, or publish events.

It creates no RuntimeManager, no new orchestrator, and no production CLI per
component.
