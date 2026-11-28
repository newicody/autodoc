# Changelog — 0213 Context recall integration audit

## Added

- Bloc G context recall integration audit.
- Existing-surface scan for context/query, recall/Qdrant, sql_ref rehydrate, and response/result surfaces.
- Target path: context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact.
- Documentation, graph, changelog, manifest, and code-rule entry for the patch.

## Not changed

- No recall execution.
- No Qdrant query.
- No SQL record read.
- No SQL/Qdrant write.
- No new SQL/Qdrant backend.
- No new inference path.
- No Scheduler.run execution or modification.
- No runtime handler import or call.
- No ControlProxy or RouteProxy frame write.
- No network/GitHub call.
