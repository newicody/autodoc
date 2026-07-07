# 0215 controlled context recall integration acceptance rule

0215 accepts controlled context recall integration contract only.

Rules:

- Read context_recall_integration_plan.json from 0214.
- Write controlled_context_recall_integration_acceptance.json only.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not perform live Qdrant recall in 0215.
- Do not query Qdrant in 0215.
- Do not read SQL records in 0215.
- Do not write SQL in 0215.
- Do not write Qdrant in 0215.
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
- Require controlled recall result sql_ref.
- Require controlled rehydrate result.
- Require controlled response artifact.
- Open Bloc H only after acceptance.
