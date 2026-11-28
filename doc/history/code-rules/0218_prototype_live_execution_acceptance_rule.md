# 0218 prototype live execution acceptance rule

0218 executes the live controlled prototype.

Rules:

- Read prototype_live_execution_plan.json from 0217.
- Execute the live controlled prototype.
- Do not create another contract-only smoke loop.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Write SQL dev record in 0218.
- Create or recreate the dedicated local Qdrant collection in 0218.
- Upsert Qdrant point in 0218.
- Query Qdrant in 0218.
- Extract payload.sql_ref from Qdrant result in 0218.
- Read SQL record in 0218.
- Rehydrate response in 0218.
- Write response artifact in 0218.
- Require prototype_success true only when all true flags are true.
- Only localhost Qdrant is allowed.
- External network remains forbidden.
- Do not call GitHub API.
- Do not add a new SQL backend.
- Do not add a new Qdrant backend.
- Do not add a new inference path.
- Do not rewrite runtime history.
- Do not execute Scheduler.run.
- Do not modify Scheduler.run.
- Do not import runtime handler modules.
- Do not write ControlProxy or RouteProxy frames.
