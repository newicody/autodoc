# Phase 0213 Test Report — Context recall integration audit

Status: prepared.

Scope:
- Reads `controlled_sql_qdrant_projection_acceptance.json`.
- Produces `context_recall_integration_audit.json`.
- Audits context/query surfaces.
- Audits recall/Qdrant surfaces.
- Audits sql_ref rehydrate surfaces.
- Audits response/result artifact surfaces.
- Applies `doc/code-rules/code_rule.md`.
- Updates docs, graph, changelog, manifest, and rule.
- Opens Bloc G.
- No recall execution.
- No Qdrant query.
- No SQL record read.
- No SQL/Qdrant write.
- No new SQL/Qdrant backend.
- No new inference path.
- No Scheduler.run execution.
- No Scheduler.run modification.
- No runtime import.
- No handler call.
- No frame write by 0213.
- No ControlProxy frame write.
- No GitHub API/network.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/tools/test_audit_context_recall_integration_0213.py \
  tests/rules/test_context_recall_integration_audit_0213_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
