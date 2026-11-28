# 0122 changelog — context graph export

- Added `src/context/context_graph_export.py`.
- Added passive DOT export for `GitHubProjectScenarioPacket`.
- Added runtime tests for graph construction, policy bounds, and DOT output.
- Added rule tests to lock passive/no-runtime/no-EventBus behavior.
- Added architecture docs and runtime graph.

No kernel, scheduler, dispatcher, queue, policy, EventBus, route runtime,
Qdrant, OpenVINO, PostgreSQL, HTTP, socket, or LLM runtime integration was
added.
