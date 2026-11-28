# 0192 — Isolated route pipeline acceptance gate

## Decision

0192 accepts or rejects the isolated route pipeline baseline.

The input is isolated_route_pipeline_artifact_audit.json.
The output is isolated_route_pipeline_acceptance.json.

It accepts isolated-route-pipeline-write-read-v1.
It does not rerun the pipeline.
It does not call runtime APIs.

This is the CI-style gate for the first isolated prototype.

## Why this exists

0191 audits the saved artifacts. 0192 turns that audit into a compact acceptance
verdict that can be used by humans, CI, or a future project status layer.

The accepted baseline proves:

```text
context.bus
-> authorized policy-scoped route request
-> command builder
-> isolated handler write
-> isolated readback
-> artifact audit
```

without touching Scheduler.run, EventBus, ControlProxy, GitHub, SQL, Qdrant,
inference, or VisPy.

## Boundary

0192:

- reads `isolated_route_pipeline_artifact_audit.json`,
- verifies `audit_success`,
- verifies empty audit issues,
- verifies safety flags are false,
- verifies `policy_scoped_queued_count` matches downstream counts,
- writes optional `isolated_route_pipeline_acceptance.json`.

0192 does not:

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
0192 approves the isolated prototype baseline only. It does not approve
production route writes.
