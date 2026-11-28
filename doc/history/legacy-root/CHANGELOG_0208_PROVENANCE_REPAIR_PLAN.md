# Changelog — 0208 Provenance repair plan

## Added

- Bloc E forward-only provenance repair plan.
- Selection of `source_baseline_ref` candidate.
- Selection of `source_entry_digest` candidate.
- Explicit P0209 unlock requirements.
- Documentation, graph, changelog, manifest, and code-rule entry for the patch.

## Not changed

- No provenance repair write.
- No runtime history rewrite.
- No SQL write.
- No Qdrant write.
- No Scheduler.run execution or modification.
- No runtime handler import or call.
- No ControlProxy or RouteProxy frame write.
- No network/GitHub call.
