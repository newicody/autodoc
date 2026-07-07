# 0204 — ControlProxy contract audit

## Decision

0204 opens Bloc D with a ControlProxy contract audit.

The input is controlled_scheduler_hook_smoke_acceptance.json.
The output is controlproxy_contract_audit.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0204 does not write ControlProxy or RouteProxy frames.
ControlProxy is not business authority.
Scheduler/policy/zone remain authority.
The next recommended patch is P0205 ControlProxy stale priority zone smoke plan.

## Why this exists

Bloc C accepted a controlled Scheduler hook smoke without executing or modifying
Scheduler.run. Bloc D now needs to clarify the ControlProxy contract before any
stale, priority, or zone behavior is planned.

## Existing-surface reuse decision

0204 audits existing code by AST/text only.

Candidate surfaces:

- `src/runtime/controlproxy_scheduler_handler.py`,
- `src/runtime/scheduler_route_adapter.py`,
- `src/runtime/scheduler_route_handler_minimal.py`,
- `src/runtime/route_proxy_runtime_minimal.py`,
- `src/runtime/shm_runtime_schema.py`,
- `src/runtime/bus_visualization_adapter.py`.

The expected contract is:

```text
Scheduler authority -> ControlProxy contract wrapper -> RouteProxy data-plane
```

## Boundary

0204:

- reads `controlled_scheduler_hook_smoke_acceptance.json`,
- verifies Bloc C is accepted,
- inspects existing ControlProxy and RouteProxy surfaces,
- records required functions/classes/tokens,
- records contract decisions,
- writes optional `controlproxy_contract_audit.json`.

0204 does not:

- execute Scheduler.run,
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

## Contract decisions

- ControlProxy remains a coordination and contract surface, not business authority.
- Scheduler/policy/zone remain authority.
- RouteProxy remains the fast data-plane frame surface.
- stale, priority, and zone behavior must be policy-scoped and auditable.
- Any future ControlProxy frame write requires explicit phase unlock and acceptance.

## Next

If 0204 succeeds, P0205 may plan stale priority zone behavior.
