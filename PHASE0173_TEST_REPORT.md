# Phase 0173 Test Report — Runtime graph rebuild from code audit

Status: prepared.

Scope:
- Audit and reconstruction contract only.
- No runtime code.
- No Scheduler modification.
- No new bus.
- No VisPy renderer.
- No direct `00_global.dot` rewrite.
- Defines how the global graph and subgraphs must be rebuilt from working code,
  passing tests, manifests, rules, and the planned 0162..0172 chain.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q tests/rules/test_runtime_graph_rebuild_from_code_audit_0173_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
