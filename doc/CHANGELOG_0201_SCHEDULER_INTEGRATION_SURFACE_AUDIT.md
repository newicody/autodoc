# Changelog — 0201 Scheduler integration surface audit

## Added

- Bloc C Scheduler integration surface audit.
- AST/text audit of existing Scheduler/RouteProxy integration candidates.
- Reuse-first recommendation for adapter -> command builder -> minimal handler -> readback.
- Provenance repair warning for missing `source_baseline_ref` or `source_entry_digest`.
- Documentation, graph, changelog, manifest, and code-rule entry for the patch.

## Not changed

- No Scheduler.run execution.
- No Scheduler hook.
- No runtime handler import.
- No runtime handler call.
- No new adapter, bus, Scheduler, RouteProxy runtime, ControlProxy runtime, SQL
  backend, Qdrant backend, GitHub client, graph renderer, or inference path.
- No ControlProxy or RouteProxy frame write.
- No production route write.
