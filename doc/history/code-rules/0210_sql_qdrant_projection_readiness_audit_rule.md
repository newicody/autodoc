# 0210 SQL/Qdrant projection readiness audit rule

0210 audits SQL/Qdrant projection readiness only.

Rules:

- Read provenance_repair_acceptance.json from 0209.
- Audit existing SQL and Qdrant projection surfaces.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not write SQL in 0210.
- Do not write Qdrant in 0210.
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
- Rehydrate Qdrant results from SQL authority.
- Allow P0211 to plan SQL/Qdrant projection only after audit.
