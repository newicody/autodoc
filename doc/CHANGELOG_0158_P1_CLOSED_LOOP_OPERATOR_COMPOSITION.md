# Changelog — 0158-r1 P1 closed-loop operator composition

0158-r1 adds a single operator composition command for the validated P1 chain.

## Added

- `tools/run_p1_closed_loop_operator_smoke.py`
- tests for the 0158 operator plan and result summary
- 0158 code rule
- 0158 architecture document
- 0158 runtime DOT
- manifest and test report

## Decision

P1 closure is a composition problem, not a new architecture problem.

The operator composes:

```text
0145 -> 0148 -> 0149 -> 0150 -> 0151/0152
```

## Boundary

No runtime Python under `src/` is modified.

No Scheduler runner, SQL worker, orchestrator, OpenVINO adapter or Qdrant adapter
is introduced.
