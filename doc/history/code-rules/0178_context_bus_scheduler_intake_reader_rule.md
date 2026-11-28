# 0178 context bus scheduler intake reader rule

0178 makes context.bus the scheduler intake source for GitHub artifact dataset
facts.

Rules:

- Read scheduler intake source from context.bus.jsonl.
- Use ContextBusMessage.from_mapping.
- Accept only topic github.artifact_dataset.context.
- Accept only payload_schema missipy.github_artifact.dataset_context.v1.
- Do not introduce arbitrary direct JSON scheduler intake.
- Do not instantiate EventBus.
- Do not create a parallel bus.
- Do not modify Scheduler.run().
- Do not call handle_scheduler_route_request.
- Do not bypass Scheduler/policy/zone.
- Do not emit authorized SchedulerRouteRequest without policy_decision_id.
- Do not call GitHub API.
- Do not use network.
- Do not execute conversion.
- Do not execute inference.
- Do not write SQL.
- Do not write Qdrant.
- Do not write directly to VisPy.
