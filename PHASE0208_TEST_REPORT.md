# Phase 0208 Test Report — Provenance repair plan

Status: prepared.

Scope:
- Reads `provenance_repair_audit.json`.
- Produces `provenance_repair_plan.json`.
- Selects `source_baseline_ref` candidate.
- Selects `source_entry_digest` candidate.
- Plans forward-only provenance repair.
- Applies `doc/code-rules/code_rule.md`.
- Updates docs, graph, changelog, manifest, and rule.
- No provenance repair write.
- No runtime history rewrite.
- No SQL/Qdrant write.
- No Scheduler.run execution.
- No Scheduler.run modification.
- No runtime import.
- No handler call.
- No mark_route_frame_stale call.
- No frame write by 0208.
- No ControlProxy frame write.
- No GitHub API/network.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/tools/test_plan_provenance_repair_0208.py \
  tests/rules/test_provenance_repair_plan_0208_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
