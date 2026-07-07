# 0193 — Isolated route pipeline baseline registry

## Decision

0193 registers the accepted isolated route pipeline baseline.

The input is isolated_route_pipeline_acceptance.json.
The output is isolated_route_pipeline_baseline_registry.jsonl.

It registers isolated-route-pipeline-write-read-v1.
It does not rerun the pipeline.
It does not call runtime APIs.

This is the baseline registry for accepted isolated prototypes.

## Why this exists

0192 accepts the first isolated prototype. 0193 creates a durable audit index
entry from that acceptance verdict so the baseline can be referenced later by
docs, CI, project status, or future promotion plans.

The registry entry is compact and includes:

- accepted baseline name,
- baseline ref,
- entry digest,
- policy decision id,
- runtime root references,
- top-level counts,
- artifact counts,
- safety flags.

## Boundary

0193:

- reads `isolated_route_pipeline_acceptance.json`,
- verifies `acceptance_approved`,
- verifies `accepted_baseline`,
- verifies safety flags are false,
- verifies scoped counts still match,
- writes `isolated_route_pipeline_baseline_registry.jsonl`.

0193 does not:

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
0193 registers an accepted isolated prototype baseline only. It does not approve
production route writes.
