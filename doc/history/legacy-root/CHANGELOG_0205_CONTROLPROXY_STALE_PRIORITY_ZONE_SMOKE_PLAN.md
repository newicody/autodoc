# Changelog — 0205 ControlProxy stale priority zone smoke plan

## Added

- Bloc D stale/priority/zone smoke plan.
- Planned contract path from Scheduler/policy/zone to ControlProxy contract to
  RouteProxy data-plane.
- P0206 explicit controlled execution unlock requirements.
- Provenance repair item carry-forward.
- Documentation, graph, changelog, manifest, and code-rule entry for the patch.

## Not changed

- No Scheduler.run execution or modification.
- No runtime handler import.
- No runtime handler call.
- No stale mark call.
- No new adapter, bus, Scheduler, RouteProxy runtime, ControlProxy runtime, SQL
  backend, Qdrant backend, GitHub client, graph renderer, or inference path.
- No ControlProxy or RouteProxy frame write.
- No production route write.
