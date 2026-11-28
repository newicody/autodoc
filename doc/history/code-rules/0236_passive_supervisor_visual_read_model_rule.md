# Code rule 0236 — passive supervisor visual read-model

The passive supervisor visual read-model must remain read-only.

Required:

- derive from an existing passive supervisor snapshot
- use only stdlib
- keep VisPy out of this patch
- keep snapshot as the input, not status JSON as a runtime path
- expose nodes/edges/zones for a future renderer

Forbidden:

- `Scheduler.run()`
- EventBus creation
- RouteProxy or ControlProxy control
- SHM writes
- policy decisions
- SQL/Qdrant/GitHub mutations
- introducing a renderer dependency
