# Changelog — 0088 — ControlProxy Scheduler handler

## Added

- `runtime.controlproxy_scheduler_handler.ControlProxySchedulerRouteRequestHandler`
  as a concrete Dispatcher handler that receives a Scheduler event payload and
  calls the existing `handle_scheduler_route_request()` adapter from 0086.
- Unit tests for sync adapter calls, async adapter calls, missing payload
  rejection, and wrapper delegation.
- Rule guard ensuring 0088 remains outside Scheduler loop mutation and does not
  add a CLI, daemon, service, policy decision, Qdrant path, LLM path, or
  OpenVINO path.

## Priority review before 0088

0088 is still the right next step before producer/consumer mmap E2E work: the
route-request path must first have a real Scheduler/Dispatcher handler so the
later notifier and recorder phases can attach to a stable live boundary instead
of bypassing the Scheduler.

The priority order remains:

1. Handler boundary through Dispatcher.
2. End-to-end mmap write/notify/drain.
3. Recorder/journal ingestion of drained messages.
4. Generation g2/g3 for route update/resize without live resize.
5. Draining/closed cleanup.
6. UI/browser projection from event/context facts.

## Out of scope

- No `Scheduler.run()` change.
- No `PriorityQueue` change.
- No `Dispatcher` change.
- No `Component.tick()` / yield / reply contract change.
- No security decision inside ControlProxy.
- No new CLI.
- No daemon, watcher, OpenRC service, or resident process.
- No network bridge or hardware bridge.
- No live mmap resize.
