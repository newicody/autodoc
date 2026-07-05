# Changelog — 0114-r2 context variation core contract

- Replaces the rejected linear 0114 direction with a trajectory-based context
  variation contract.
- Adds reference-only dataclasses for objectives, axes, trajectories,
  candidates, exploration results, reduction plans, and inference drafts.
- Keeps MVTC as future architecture without implementing it in this phase.
- Keeps SQL/Qdrant/OpenVINO/LLM behind future adapters.
- Does not touch Scheduler, Dispatcher, PriorityQueue, PolicyEngine, EventBus,
  ControlProxy, or RouteRuntimeManager.
