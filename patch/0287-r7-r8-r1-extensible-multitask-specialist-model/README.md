# 0287-r7-r8-r1 — extensible multitask specialist model

Adds a generic versioned task layer above the existing portable specialist,
specialist/laboratory message v2 and deep-analysis contracts.

The patch provides:

- extensible task-type declarations bound to existing capabilities;
- immutable task requests and standard task results;
- Scheduler-owned acyclic multitask plans;
- dependency-ready calculation without scheduling or execution;
- follow-up proposals that require a later Scheduler decision;
- typed execution bindings that reuse existing OpenVINO surfaces;
- bridges preserving the existing deep-analysis request and contribution as
  `specialist-task-type:analysis.deep`;
- roadmap boundaries for SQL authority, Qdrant projection/retrieval, semantic
  context revisions and transport-only ControlProxy integration.

Prerequisite:

- `0287-r7-r8-specialist-message-v2-deep-analysis-contract`.

Validation:

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_specialist_multitask_model_0287.py \
  tests/rules/test_extensible_multitask_specialist_0287_r7_r8_r1_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

This phase is contract-only. It adds no Scheduler, worker, queue, global
registry, laboratory runtime, OpenVINO implementation, SQL/Qdrant write,
ControlProxy behavior, network access or GitHub mutation. `INSTALLATION.md` is
unchanged.
