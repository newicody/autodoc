# Changelog — 0206 ControlProxy RouteProxy coherence acceptance

## Added

- Controlled ControlProxy/RouteProxy coherence execution and acceptance.
- Explicit reuse of `tools/run_isolated_route_pipeline_smoke.py`.
- Bloc D acceptance baseline `controlproxy-routeproxy-stale-priority-zone-coherence-v1`.
- Next Bloc E direction toward provenance repair audit.
- Documentation, graph, changelog, manifest, and code-rule entry for the patch.

## Not changed

- No Scheduler.run execution or modification.
- No new ControlProxy runtime.
- No new RouteProxy runtime.
- No new Scheduler hook implementation.
- No direct `mark_route_frame_stale` call.
- No new runtime handler, adapter, bus, Scheduler, SQL backend, Qdrant backend,
  GitHub client, graph renderer, or inference path.
- No ControlProxy frame write.
- No production route write.
