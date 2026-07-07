# 0212 controlled SQL/Qdrant projection acceptance rule

0212 accepts controlled SQL/Qdrant projection contract only.

Rules:

- Read sql_qdrant_projection_plan.json from 0211.
- Write controlled_sql_qdrant_projection_acceptance.json only.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not write SQL rows in 0212.
- Do not write Qdrant points in 0212.
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
- Require qdrant_payload.sql_ref.
- Require rehydration from SQL authority.
- Open Bloc G only after acceptance.
