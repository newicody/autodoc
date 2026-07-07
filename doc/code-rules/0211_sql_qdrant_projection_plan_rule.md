# 0211 SQL/Qdrant projection plan rule

0211 plans SQL/Qdrant projection only.

Rules:

- Read sql_qdrant_projection_readiness_audit.json from 0210.
- Plan SQL/Qdrant projection only.
- Select SQL authority surface.
- Select Qdrant projection surface.
- Select SQL rehydrate surface.
- Select provenance repair surface.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not write SQL in 0211.
- Do not write Qdrant in 0211.
- Do not add a new SQL backend.
- Do not add a new Qdrant backend.
- Do not rewrite runtime history.
- Do not execute Scheduler.run.
- Do not modify Scheduler.run.
- Do not import runtime handler modules.
- Do not write ControlProxy or RouteProxy frames.
- Do not call GitHub API.
- Do not use network.
- SQL remains durable authority.
- Qdrant remains projection/search/recall only.
- Qdrant payloads must carry sql_ref.
- Rehydrate Qdrant recall from SQL authority.
- Allow P0212 to execute controlled SQL/Qdrant projection acceptance.
