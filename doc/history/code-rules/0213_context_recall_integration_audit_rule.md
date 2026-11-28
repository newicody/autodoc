# 0213 context recall integration audit rule

0213 audits context recall integration readiness only.

Rules:

- Read controlled_sql_qdrant_projection_acceptance.json from 0212.
- Audit context/query surfaces.
- Audit recall/Qdrant surfaces.
- Audit sql_ref rehydrate surfaces.
- Audit response/result artifact surfaces.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not execute recall in 0213.
- Do not query Qdrant in 0213.
- Do not read SQL records in 0213.
- Do not write SQL in 0213.
- Do not write Qdrant in 0213.
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
- Allow P0214 to plan context recall integration only after audit.
