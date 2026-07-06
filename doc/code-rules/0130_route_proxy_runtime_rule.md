# code_rule supplement — 0130 RouteProxy runtime membrane

This supplement extends `doc/code-rules/code_rule.md` for the first RouteProxy runtime step.

## Rule

RouteProxy runtime may perform local filesystem IO under its configured route root, but it must remain a data-plane executor.

## Mandatory boundaries

- RouteProxy runtime is a data-plane executor, not an orchestrator.
- Scheduler remains the orchestrator.
- Scheduler.run() must not be changed for 0130.
- RouteProxy runtime must not import network clients, OpenVINO, Qdrant, PostgreSQL drivers, VisPy, Graphviz, NetworkX, subprocess, or socket.
- RouteProxy runtime must not scan the global mount table.
- EventBus output must be observation-ready facts only.
- SQLContextStore remains durable authority.
- `/dev/shm` is the default production route root.
- Non-`/dev/shm` roots are allowed only for tests with explicit opt-in.

## Rationale

The project previously hit a runtime failure while resolving unrelated protected mount points. RouteProxy runtime must validate its own root, not the whole machine.
