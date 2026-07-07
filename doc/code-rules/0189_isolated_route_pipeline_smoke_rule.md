# 0189 isolated route pipeline smoke rule

0189 consolidates the isolated write/read route pipeline prototype.

Rules:

- Run only against an explicit isolated_runtime_root.
- Keep scheduler.route_requests.jsonl append-only.
- Build scheduler.route_requests.policy_scoped.jsonl for the current policy_decision_id.
- Downstream isolated pipeline stages must read the policy-scoped queue.
- Reuse existing 0179 and 0184 through 0188 stages.
- Require explicit policy_decision_id.
- Write only pipeline artifacts under the requested runtime_root and RouteProxy frames under isolated_runtime_root.
- Do not add a new runtime handler.
- Do not modify Scheduler.run.
- Do not instantiate Scheduler.
- Do not instantiate EventBus.
- Do not create a parallel bus.
- Do not write ControlProxy frames.
- Do not call GitHub API.
- Do not use network.
- Do not execute conversion.
- Do not execute inference.
- Do not write SQL.
- Do not write Qdrant.
- Do not write directly to VisPy.
