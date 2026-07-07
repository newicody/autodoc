# Changelog — 0207 Provenance repair audit

## Added

- Bloc E provenance repair audit.
- Detection of missing `source_baseline_ref` and `source_entry_digest`.
- Runtime artifact chain inventory.
- Candidate provenance refs collection.
- Forward-only repair planning boundary for P0208.
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
