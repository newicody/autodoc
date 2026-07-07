# 0176 GitHub artifact dataset bus observation bridge rule

0176 maps GitHub artifact/server dataset outcomes to existing bus observation
messages.

Rules:

- Reuse runtime.shm_runtime_schema EventBusMessage and ContextBusMessage.
- Do not define replacement EventBusMessage or ContextBusMessage classes.
- Validate with EventBusMessage.from_mapping and ContextBusMessage.from_mapping.
- Do not instantiate EventBus.
- Do not subscribe to EventBus.
- Do not create a parallel bus.
- Do not modify Scheduler.run().
- Do not bypass Scheduler/policy/zone.
- Do not write directly to VisPy.
- Do not call the GitHub API.
- Do not use network.
- Do not execute conversion.
- Do not execute inference.
- Do not write SQL.
- Do not write Qdrant.
- Bus facts are observation-only.
