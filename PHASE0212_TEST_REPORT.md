# Phase 0212 Test Report — Controlled SQL/Qdrant projection acceptance

Status: prepared.

Scope:
- Reads `sql_qdrant_projection_plan.json`.
- Produces `controlled_sql_qdrant_projection_acceptance.json`.
- Checks selected surfaces exist.
- Builds projection record with `qdrant_payload.sql_ref`.
- Applies `doc/code-rules/code_rule.md`.
- Updates docs, graph, changelog, manifest, and rule.
- Closes Bloc F.
- Opens Bloc G.
- No SQL row write.
- No Qdrant point write.
- No new SQL/Qdrant backend.
- No runtime history rewrite.
- No Scheduler.run execution.
- No Scheduler.run modification.
- No runtime import.
- No handler call.
- No frame write by 0212.
- No ControlProxy frame write.
- No GitHub API/network.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/tools/test_accept_controlled_sql_qdrant_projection_0212.py \
  tests/rules/test_controlled_sql_qdrant_projection_acceptance_0212_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
