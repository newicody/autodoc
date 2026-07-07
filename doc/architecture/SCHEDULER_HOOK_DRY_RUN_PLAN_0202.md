# 0202 — Scheduler hook dry-run plan

## Decision

0202 creates a Scheduler hook dry-run plan from the 0201 surface audit.

The input is scheduler_integration_surface_audit.json.
The output is scheduler_hook_dry_run_plan.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0202 does not execute Scheduler.run.
0202 does not write RouteProxy or ControlProxy frames.
P0203 may unlock a controlled Scheduler hook smoke explicitly.
The provenance repair item from P0201 is carried forward.

## Why this exists

0201 showed that the existing surfaces are present and coherent. 0202 converts
that audit into a concrete dry-run plan without adding a new hook path.

The planned reuse path is:

```text
adapter -> command builder -> minimal handler -> readback
```

## Existing-surface reuse decision

0202 reuses the 0201 audit and plans to reuse:

- `src/runtime/scheduler_route_adapter.py`,
- `src/runtime/scheduler_route_handshake.py`,
- `src/runtime/scheduler_route_handler_minimal.py`.

It treats these as optional existing candidates:

- `src/runtime/controlproxy_scheduler_handler.py`,
- `src/runtime/route_proxy_runtime_minimal.py`,
- `src/runtime/shm_runtime_schema.py`.

## Boundary

0202:

- reads `scheduler_integration_surface_audit.json`,
- validates the audit is clean,
- validates the recommended integration path,
- records reuse sequence,
- carries provenance repair items,
- writes optional `scheduler_hook_dry_run_plan.json`.

0202 does not:

- execute Scheduler.run,
- add a new Scheduler hook implementation,
- import runtime handler modules,
- call handle_scheduler_route_command,
- call handle_scheduler_route_request,
- call prepare_route_proxy_runtime,
- call read_route_frame,
- request writer permits,
- call write_route_frame,
- instantiate Scheduler,
- instantiate EventBus,
- create a parallel bus,
- write ControlProxy or RouteProxy frames,
- call GitHub API,
- use network,
- execute conversion,
- execute inference,
- write SQL,
- write Qdrant,
- write directly to VisPy.

## Next

If 0202 succeeds, P0203 may unlock a controlled Scheduler hook smoke explicitly.
