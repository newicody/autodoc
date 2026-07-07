# Phase 0215 Test Report — Controlled context recall integration acceptance

Status: prepared.

Scope:
- Reads `context_recall_integration_plan.json`.
- Produces `controlled_context_recall_integration_acceptance.json`.
- Checks selected surfaces exist.
- Builds controlled context/query artifact.
- Builds controlled recall result with `sql_ref`.
- Builds controlled rehydrate result.
- Builds controlled response artifact.
- Applies `doc/code-rules/code_rule.md`.
- Updates docs, graph, changelog, manifest, and rule.
- Closes Bloc G.
- Opens Bloc H.
- No live Qdrant recall.
- No Qdrant query.
- No SQL record read.
- No SQL/Qdrant write.
- No new SQL/Qdrant backend.
- No new inference path.
- No Scheduler.run execution.
- No Scheduler.run modification.
- No runtime import.
- No handler call.
- No frame write by 0215.
- No ControlProxy frame write.
- No GitHub API/network.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/tools/test_accept_controlled_context_recall_integration_0215.py \
  tests/rules/test_controlled_context_recall_integration_acceptance_0215_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
