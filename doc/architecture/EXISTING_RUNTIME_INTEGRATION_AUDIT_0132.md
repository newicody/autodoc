# 0132 — Existing runtime integration audit

0132 is an integration audit, not a new runtime feature.

The goal is to stop adding parallel wheels.  Before any new runtime, handler, worker, adapter, SQL store, EventBus path, or Scheduler integration is added, the patch must prove what already exists and decide whether to reuse, extend, modify, or create.

## Mandatory rule

reuse, extend, or modify existing modules before creating a new module.

New module default: forbidden until audit says no existing wheel fits.

Scheduler.run() must not be modified by integration patches unless a dedicated migration patch explicitly says so.

## What 0132 adds

0132 adds a static, dependency-free audit helper:

```text
tools/audit_existing_runtime_integration.py
```

The helper scans source, tests, and docs for candidate surfaces:

```text
scheduler
dispatcher
policy_queue
route_runtime
route_handler
openvino_adapter
qdrant_adapter
sql_context
event_bus
code_rules
```

It returns decision hints:

```text
reuse_or_extend_existing
create_only_after_documented_gap
```

This is not a live runtime component.  It does not import project modules, call OpenVINO, call Qdrant, touch PostgreSQL, start daemons, scan sockets, or mutate Scheduler.

## Integration decisions from the current line

The current local line already has:

```text
src/runtime/route_proxy_runtime_minimal.py
src/runtime/scheduler_route_handler_minimal.py
```

So the next runtime patches must not create parallel route writers or handler loops.  They must reuse or extend these surfaces unless a richer existing module in the real repository is detected by the audit.

## Required preflight for next patches

### RouteProxy work

RouteProxy work must first audit existing /dev/shm runtime surfaces.

If `src/runtime/route_proxy_runtime_minimal.py`, an older `route_dev_shm` runtime, or another route manager exists, modify or extend it before adding another route runtime.

### Scheduler/handler work

Fake specialist work must first audit existing handler/worker surfaces.

If a handler/dispatcher surface exists, add the specialist worker as an executor behind the existing handler path rather than inventing another loop.

### OpenVINO work

OpenVINO work must first audit existing embedding adapter surfaces.

If `src/inference/openvino_embedding_adapter.py`, `src/inference/*embedding*`, or another embedding adapter exists, modify or extend it.  Do not introduce a second OpenVINO adapter with overlapping responsibility.

### Qdrant work

Qdrant work must first audit existing projection adapter surfaces.

If `src/inference/qdrant_projection_adapter.py`, `src/vector/*`, or another projection adapter exists, modify or extend it.  Do not introduce a second Qdrant client wrapper with overlapping responsibility.

### Code rules

code_rule update required: yes.

0132 adds a supplement under:

```text
doc/code-rules/0132_no_reinvent_runtime_rule.md
```

This is written as a supplement to the main `doc/code-rules/code_rule.md`.  If the main file exists in the real repository, its next maintenance patch should link or include this rule rather than duplicating wording.

## Next patch gate

Before 0133 starts, run:

```bash
python tools/audit_existing_runtime_integration.py . --format markdown
```

Then choose one of:

```text
reuse existing
extend existing
modify existing
create new with documented gap
```

A new module must include the documented gap in its architecture doc and rule test.
