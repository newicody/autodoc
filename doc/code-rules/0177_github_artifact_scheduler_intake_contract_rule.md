# 0177 GitHub artifact scheduler intake contract rule

0177 prepares scheduler-addressable intake data without becoming the Scheduler.

Rules:

- Reuse runtime.scheduler_route_adapter.scheduler_route_request_mapping.
- Do not call handle_scheduler_route_request.
- Do not modify Scheduler.run().
- Do not instantiate Scheduler.
- Do not instantiate EventBus.
- Do not instantiate Dispatcher.
- Do not instantiate PriorityQueue.
- Do not bypass Scheduler/policy/zone.
- Do not emit authorized SchedulerRouteRequest without policy_decision_id.
- A candidate is not authorized work.
- Do not call GitHub API.
- Do not use network.
- Do not execute conversion.
- Do not execute inference.
- Do not write SQL.
- Do not write Qdrant.
- Do not write directly to VisPy.
