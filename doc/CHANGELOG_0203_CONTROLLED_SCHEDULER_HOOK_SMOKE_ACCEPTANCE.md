# Changelog — 0203 Controlled Scheduler hook smoke acceptance

## Added

- Controlled Scheduler hook smoke execution and acceptance.
- Explicit reuse of `tools/run_isolated_route_pipeline_smoke.py`.
- Bloc C acceptance baseline `controlled-scheduler-hook-routeproxy-write-read-v1`.
- Next Bloc D direction toward ControlProxy contract audit.
- Documentation, graph, changelog, manifest, and code-rule entry for the patch.

## Not changed

- No Scheduler.run execution.
- No Scheduler.run modification.
- No new Scheduler hook implementation.
- No new runtime handler, adapter, bus, Scheduler, RouteProxy runtime,
  ControlProxy runtime, SQL backend, Qdrant backend, GitHub client, graph
  renderer, or inference path.
- No ControlProxy frame write.
- No production route write.
