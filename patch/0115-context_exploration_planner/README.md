# 0115-context_exploration_planner

Adds a deterministic, bounded context exploration planner after the 0114-r2 core
contract. The planner turns a `ContextVariationObjective` into a bounded
`ContextExplorationPlan` made of reference-only trajectories.

It represents the intended path as capability hints only:

```text
SQL hydrate -> OpenVINO embed -> Qdrant recall -> SQL re-hydrate -> specialist note
```

Scope:

- Adds `src/context/context_exploration_planner.py`.
- Adds runtime tests, rule tests, architecture docs, graph, manifest, changelog,
  and phase report.
- Does not add MVTC runtime.
- Does not import SQL/Qdrant/OpenVINO/LLM runtime libraries.
- Does not modify Scheduler, Dispatcher, PriorityQueue, PolicyEngine, EventBus,
  ControlProxy, or RouteRuntimeManager.

Expected validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_context_exploration_planner.py
PYTHONPATH=src:. pytest -q tests/rules/test_context_exploration_planner_0115_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
