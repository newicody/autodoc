# 0217 prototype live execution plan rule

0217 plans live prototype execution.

Rules:

- Read prototype_live_readiness_audit.json from 0216.
- Plan live prototype execution for P0218.
- Do not create another contract-only smoke loop.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not execute the prototype in 0217.
- Do not write SQL in 0217.
- Do not read SQL records in 0217.
- Do not create Qdrant collections in 0217.
- Do not upsert Qdrant points in 0217.
- Do not query Qdrant semantic results in 0217.
- Do not write Qdrant in 0217.
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
- Require P0218 true flags.
- Allow P0218 to execute the live controlled prototype.
