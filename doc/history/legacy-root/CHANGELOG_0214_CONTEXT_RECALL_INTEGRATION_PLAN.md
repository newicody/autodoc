# Changelog — 0214 Context recall integration plan

## Added

- Bloc G context recall integration plan.
- Selection of context/query, recall/Qdrant, sql_ref rehydrate, response/result,
  and projection/sql_ref surfaces.
- Integration strategy `context_query_qdrant_recall_sql_ref_sql_rehydrate_response_artifact`.
- Explicit P0215 controlled integration acceptance unlock requirements.
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
