# 0201 — Scheduler integration surface audit

## Decision

0201 opens Bloc C with a Scheduler integration surface audit.

The input is controlled_dev_routeproxy_smoke_post_execution_acceptance.json.
The output is scheduler_integration_surface_audit.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0201 does not hook Scheduler.run.
0201 audits existing code before P0202 may plan a hook.
The provenance gap from P0200 is kept as a repair item.

## Why this exists

Bloc B proved a controlled dev RouteProxy write/read smoke through the existing
pipeline.

Bloc C must decide how the Scheduler can be connected without inventing a new
parallel scheduler path. The first step is to audit existing surfaces.

## Existing-surface reuse decision

0201 inspects existing code by AST/text and does not import runtime modules.

Candidate surfaces:

- `src/runtime/scheduler_route_adapter.py`,
- `src/runtime/scheduler_route_handshake.py`,
- `src/runtime/scheduler_route_handler_minimal.py`,
- `src/runtime/controlproxy_scheduler_handler.py`,
- `src/runtime/route_proxy_runtime_minimal.py`,
- `src/runtime/shm_runtime_schema.py`.

The recommended path should reuse adapter -> command builder -> minimal handler
-> readback before any new runtime surface is considered.

## Boundary

0201:

- reads `controlled_dev_routeproxy_smoke_post_execution_acceptance.json`,
- validates Bloc B is complete,
- inspects existing source files,
- records required functions/classes,
- records missing surfaces,
- writes optional `scheduler_integration_surface_audit.json`.

0201 does not:

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

## Provenance repair item

The P0200 manual output can contain empty `source_baseline_ref` and
`source_entry_digest`.

0201 does not block Bloc C on that gap, because controlled dev execution was
accepted, but it preserves the gap as a provenance repair item.

## Next

If 0201 succeeds, P0202 may create a Scheduler hook dry-run plan.
