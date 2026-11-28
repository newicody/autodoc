# Changelog — 0204 ControlProxy contract audit

## Added

- Bloc D ControlProxy contract audit.
- AST/text audit of existing ControlProxy/RouteProxy contract candidates.
- Contract decision: ControlProxy is coordination, not business authority.
- Contract decision: Scheduler/policy/zone remain authority.
- Contract decision: RouteProxy remains fast data-plane frame surface.
- Next patch direction for stale/priority/zone planning.
- Documentation, graph, changelog, manifest, and code-rule entry for the patch.

## Not changed

- No Scheduler.run execution or modification.
- No runtime handler import.
- No runtime handler call.
- No new adapter, bus, Scheduler, RouteProxy runtime, ControlProxy runtime, SQL
  backend, Qdrant backend, GitHub client, graph renderer, or inference path.
- No ControlProxy or RouteProxy frame write.
- No production route write.
