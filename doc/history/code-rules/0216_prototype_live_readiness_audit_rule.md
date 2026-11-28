# 0216 prototype live readiness audit rule

0216 audits prototype live readiness.

Rules:

- Read controlled_context_recall_integration_acceptance.json from 0215.
- Audit prototype live readiness.
- Do not create another contract-only smoke loop.
- Require P0218 true flags.
- Only localhost Qdrant probe may be allowed in 0216.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not write SQL in 0216.
- Do not write Qdrant in 0216.
- Do not query Qdrant semantic results in 0216.
- Do not read SQL records in 0216.
- Do not add a new SQL backend.
- Do not add a new Qdrant backend.
- Do not add a new inference path.
- Do not rewrite runtime history.
- Do not execute Scheduler.run.
- Do not modify Scheduler.run.
- Do not import runtime handler modules.
- Do not write ControlProxy or RouteProxy frames.
- Do not call GitHub API.
- Do not use external network.
- Allow P0217 to plan live prototype execution.
