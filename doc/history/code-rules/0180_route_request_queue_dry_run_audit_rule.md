# 0180 route request queue dry-run audit rule

0180 audits the authorized route request handoff queue without executing it.

Rules:

- Read only scheduler.route_requests.jsonl.
- Produce only a dry-run readiness report.
- Validate queued items with SchedulerRouteRequest.from_mapping.
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
