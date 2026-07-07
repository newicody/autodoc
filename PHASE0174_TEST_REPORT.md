# Phase 0174 Test Report — Rebuilt runtime global graph draft

Status: prepared.

Scope:
- Documentation/graph reconstruction draft only.
- Does not rewrite `doc/docs/architecture/00_global.dot`.
- Adds a current-state global draft graph and maintained subgraph drafts.
- Deduces the graph from existing code surfaces, passing rule intent, and the
  0162..0173 chain.
- Marks stale or planned areas explicitly.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q tests/rules/test_rebuilt_runtime_global_graph_draft_0174_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
