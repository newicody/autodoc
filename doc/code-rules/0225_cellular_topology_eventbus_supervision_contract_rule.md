# 0225 Rule — Cellular Topology EventBus Supervision Contract

Cellular topology is a passive projection over canonical EventBus events.

The passive supervisor may group cells by locality and may show observed movement
when upstream events describe handoff, route change, lease change, context
movement, artifact promotion, SQL/Qdrant reference creation, rehydration, or
pushback status.

The passive supervisor must not cause movement, schedule work, control proxy or
SHM, decide policy, mutate GitHub, write SQL/Qdrant, or introduce a parallel bus.

`events.jsonl` and `snapshot.json` remain optional outputs for audit, replay,
debug, and visualization. They are not the canonical runtime path.

`Scheduler.run()` remains outside the passive-supervisor path.
