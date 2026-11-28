# Changelog — 0225 Cellular Topology EventBus Supervision Contract

## Added

- Documented the cellular topology contract for passive EventBus supervision.
- Locked the distinction between observed cell movement and runtime authority.
- Documented locality grouping for scheduler, proxy, SHM, policy, GitHub, SQL,
  Qdrant, rehydration, and pushback surfaces.
- Added a code-rule requiring topology/movement to remain a projection over
  canonical EventBus events.
- Added DOT architecture graph showing topology projection as downstream-only.
- Added rule test to keep the topology contract traceable.

## Not added

- No runtime code.
- No new EventBus.
- No scheduler wrapper.
- No proxy controller.
- No SHM reader/writer.
- No policy decision engine.
- No SQL/Qdrant/GitHub mutation.
- No VisPy renderer.
