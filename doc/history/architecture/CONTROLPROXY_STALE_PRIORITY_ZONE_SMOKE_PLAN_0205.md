# 0205 — ControlProxy stale priority zone smoke plan

## Decision

0205 creates a ControlProxy stale priority zone smoke plan.

The input is controlproxy_contract_audit.json.
The output is controlproxy_stale_priority_zone_smoke_plan.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0205 does not write ControlProxy or RouteProxy frames.
ControlProxy remains coordination, not authority.
Scheduler/policy/zone remain authority.
P0206 may execute the controlled stale priority zone smoke explicitly.

## Why this exists

0204 proved the existing ControlProxy and RouteProxy contract surfaces are
available. 0205 converts that audit into a safe execution plan for stale,
priority, and zone behavior.

0205 still does not execute the behavior.

## Existing-surface reuse decision

0205 reuses the 0204 audit and plans to reuse:

- `src/runtime/controlproxy_scheduler_handler.py`,
- `src/runtime/scheduler_route_adapter.py`,
- `src/runtime/scheduler_route_handler_minimal.py`,
- `src/runtime/route_proxy_runtime_minimal.py`.

Observation-only surfaces:

- `src/runtime/shm_runtime_schema.py`,
- `src/runtime/bus_visualization_adapter.py`.

## Boundary

0205:

- reads `controlproxy_contract_audit.json`,
- validates the contract audit is clean,
- records planned stale/priority/zone smoke steps,
- carries provenance repair items,
- writes optional `controlproxy_stale_priority_zone_smoke_plan.json`.

0205 does not:

- execute Scheduler.run,
- modify Scheduler.run,
- import runtime handler modules,
- call handle_scheduler_route_command,
- call handle_scheduler_route_request,
- call prepare_route_proxy_runtime,
- call mark_route_frame_stale,
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

## Planned smoke

The planned contract path is:

```text
Scheduler/policy/zone -> ControlProxy contract -> RouteProxy stale priority zone data-plane
```

The controlled execution is deferred to P0206.

## Next

If 0205 succeeds, P0206 may unlock controlled stale priority zone smoke explicitly
and close Bloc D.
