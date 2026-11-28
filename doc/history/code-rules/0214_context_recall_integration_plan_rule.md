# 0214 context recall integration plan rule

0214 plans context recall integration only.

Rules:

- Read context_recall_integration_audit.json from 0213.
- Plan context recall integration only.
- Select context/query surface.
- Select recall/Qdrant surface.
- Select sql_ref rehydrate surface.
- Select response/result artifact surface.
- Select projection/sql_ref surface.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not execute recall in 0214.
- Do not query Qdrant in 0214.
- Do not read SQL records in 0214.
- Do not write SQL in 0214.
- Do not write Qdrant in 0214.
- Do not add a new SQL backend.
- Do not add a new Qdrant backend.
- Do not add a new inference path.
- Do not rewrite runtime history.
- Do not execute Scheduler.run.
- Do not modify Scheduler.run.
- Do not import runtime handler modules.
- Do not write ControlProxy or RouteProxy frames.
- Do not call GitHub API.
- Do not use network.
- Allow P0215 to execute controlled context recall integration acceptance.
