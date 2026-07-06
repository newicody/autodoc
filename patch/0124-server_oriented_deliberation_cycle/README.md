# 0124 — Server-oriented deliberation cycle

This patch adds local contracts for the server/specialist deliberation loop.

It keeps GitHub as artifact exchange only: artifact in, final artifact out.  The local server creates `ServerOrientation`, collects `SpecialistPreliminaryOpinion` values, recomposes them into `RefinedSpecialistDemand` values, records `DeliberationRound` state, aggregates local `SpecialistBusStatistics`, and prepares a `FinalArtifactEnvelope` only after local convergence.

No Scheduler, Dispatcher, Queue, PolicyEngine, EventBus, RouteRuntimeManager, GitHub client, HTTP client, socket, watcher, service, VisPy renderer, Qdrant client, OpenVINO runtime, or PostgreSQL driver is added.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_server_oriented_deliberation_cycle.py
PYTHONPATH=src:. pytest -q tests/rules/test_server_oriented_deliberation_cycle_0124_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
