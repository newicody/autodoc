# 0191 — Isolated route pipeline artifact audit

## Decision

0191 audits the isolated route pipeline artifacts without executing the pipeline.

The input is isolated_route_pipeline_smoke.json.
The output is isolated_route_pipeline_artifact_audit.json.

It verifies 0184 read scheduler.route_requests.policy_scoped.jsonl.
It does not call the handler.
It does not read RouteProxy frames through runtime APIs.

This is the baseline acceptance audit for the isolated prototype.

## Why this exists

0190 fixed replay by adding the policy-scoped queue. The isolated prototype is
now functional, but it needs a stable acceptance check that can validate a saved
pipeline report and its artifacts without re-running any runtime stage.

0191 turns the prototype output into an auditable baseline.

## Boundary

0191:

- reads `isolated_route_pipeline_smoke.json`,
- checks required artifact paths,
- reads JSON/JSONL artifacts as plain files,
- verifies top-level counters,
- verifies `0184_route_request_to_command_plan.queue_path` equals the
  policy-scoped queue,
- verifies handler smoke frame paths stay under `isolated_runtime_root`,
- verifies readback items do not call the handler or write frames,
- writes optional `isolated_route_pipeline_artifact_audit.json`.

0191 does not:

- import runtime handler modules,
- call handle_scheduler_route_command,
- call handle_scheduler_route_request,
- call prepare_route_proxy_runtime,
- call read_route_frame,
- request writer permits,
- call write_route_frame,
- modify Scheduler.run,
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

## Authority

Scheduler/policy/zone remain the authority.
0191 is an audit acceptance check, not a runtime path.
