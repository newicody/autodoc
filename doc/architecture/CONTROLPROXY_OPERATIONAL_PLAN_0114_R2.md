# ControlProxy operational plan — 0114-r2 note

0114-r2 recenters the roadmap on context variability.

ControlProxy / RouteRuntimeManager remain secondary data-plane infrastructure.
They are not the center of context variation, not a Scheduler replacement, and
not the owner of SQL, Qdrant, OpenVINO, LLM, or GitHub project logic.

Next implementation order:

```text
0115 ContextExplorationPlanner minimal
0116 SQLContextStore minimal
0117 ContextCollector / ContextHydrator real path
0118 OpenVINO embedding adapter for context refs
0119 Qdrant projection/retrieval for context refs
0120 Specialist / LLM boundary for InferenceContextDraft
0121 GitHub baby-fork end-to-end scenario
```

MVTC remains future, not runtime in 0114-r2.
