# 0003 — Phase 6.5 SourceCandidate Decision Live Path

Adds a Scheduler-first local operator decision path for SourceCandidate records.

Scope:

- add `SourceCandidateDecisionCommand` / `SourceCandidateDecisionResult`;
- load the real local SourceCandidate JSON store;
- find an existing candidate by id;
- apply a typed `SourceCandidateDecision`;
- write the updated candidate back through the existing atomic store upsert;
- publish an observable Scheduler result event;
- expose a CLI adapter that traverses Scheduler/Dispatcher/Handler;
- add unit, live-path, CLI and rule tests;
- add phase documentation and architecture DOT.

Out of scope:

- no GitHub API;
- no project board mutation;
- no server;
- no Qdrant;
- no LLM/OpenVINO;
- no Scheduler modification.

Expected commit:

```bash
git commit -m "phase6.5 add source candidate decision live path"
```

Expected gate:

```bash
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src pytest -q tests/context/test_source_candidate_decision.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_decision_live_path.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_decision_cli.py
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```
