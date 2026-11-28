# 0190 isolated route pipeline policy-scoped queue rule

0190 prevents append-only queue replay in the isolated route pipeline smoke.

Rules:

- Keep scheduler.route_requests.jsonl append-only.
- Rebuild scheduler.route_requests.policy_scoped.jsonl for the current policy_decision_id.
- Downstream 0184 through 0188 stages must read scheduler.route_requests.policy_scoped.jsonl.
- Report policy_scoped_queued_count.
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
