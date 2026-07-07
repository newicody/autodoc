# Changelog — 0202 Scheduler hook dry-run plan

## Added

- Scheduler hook dry-run plan from 0201 surface audit.
- Reuse sequence for adapter -> command builder -> minimal handler -> readback.
- P0203 controlled Scheduler hook smoke unlock plan.
- Provenance repair item carry-forward.
- Documentation, graph, changelog, manifest, and code-rule entry for the patch.

## Not changed

- No Scheduler.run execution.
- No Scheduler hook implementation.
- No runtime handler import.
- No runtime handler call.
- No new adapter, bus, Scheduler, RouteProxy runtime, ControlProxy runtime, SQL
  backend, Qdrant backend, GitHub client, graph renderer, or inference path.
- No ControlProxy or RouteProxy frame write.
- No production route write.
