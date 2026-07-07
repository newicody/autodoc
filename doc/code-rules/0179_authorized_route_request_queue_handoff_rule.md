# 0179 authorized route request queue handoff rule

0179 materializes authorized SchedulerRouteRequest mappings into a local JSONL
handoff queue.

Rules:

- Read from context.bus.jsonl through the 0178 reader.
- Write only scheduler.route_requests.jsonl handoff entries.
- Require explicit policy_decision_id.
- Validate queued items with SchedulerRouteRequest.from_mapping.
- Queue only authorized SchedulerRouteRequest mappings.
- Do not call handle_scheduler_route_request.
- Do not modify Scheduler.run().
- Do not instantiate Scheduler.
- Do not instantiate EventBus.
- Do not create a parallel bus.
- Do not write ControlProxy or RouteProxy frames.
- Do not call GitHub API.
- Do not use network.
- Do not execute conversion.
- Do not execute inference.
- Do not write SQL.
- Do not write Qdrant.
- Do not write directly to VisPy.
