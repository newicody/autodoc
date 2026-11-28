# 0188 — Isolated Scheduler route handler readback smoke

## Decision

0188 reads back frames written by 0187, but does not call the handler.

The input is isolated_scheduler_route_handler_smoke.jsonl.
The output is isolated_scheduler_route_handler_readback_smoke.jsonl.

It may call read_route_frame.
It must not call write_route_frame.
It must verify no new frame files are created by readback.

This proves isolated RouteProxy write/read smoke.

## Why this exists

0187 proved that the existing minimal scheduler route handler can write a
RouteProxy frame under an explicit isolated runtime root.

0188 proves the matching readback path without re-executing the handler and
without requesting writer permits.

## Boundary

0188:

- reads `isolated_scheduler_route_handler_smoke.jsonl`,
- prepares RouteProxyRuntime only in the recorded isolated root,
- calls `read_route_frame` for `written_route_refs` from 0187,
- verifies read `route_ref` values,
- verifies readback does not create new frame files,
- writes optional `isolated_scheduler_route_handler_readback_smoke.jsonl`.

0188 does not:

- call handle_scheduler_route_command,
- call handle_scheduler_route_request,
- request writer permits,
- call write_route_frame,
- modify Scheduler.run,
- instantiate Scheduler,
- instantiate EventBus,
- create a parallel bus,
- write ControlProxy frames,
- call GitHub API,
- use network,
- execute conversion,
- execute inference,
- write SQL,
- write Qdrant,
- write directly to VisPy.

## Authority

Scheduler/policy/zone remain the authority.
0188 proves isolated RouteProxy readback only. It does not enable production
route writes.
