# Phase 0207 Test Report — Provenance repair audit

Status: prepared.

Scope:
- Reads `controlproxy_routeproxy_coherence_acceptance.json`.
- Produces `provenance_repair_audit.json`.
- Audits missing `source_baseline_ref` and `source_entry_digest`.
- Inventories runtime chain artifacts.
- Applies `doc/code-rules/code_rule.md`.
- Updates docs, graph, changelog, manifest, and rule.
- Opens Bloc E.
- No provenance repair write.
- No runtime history rewrite.
- No SQL/Qdrant write.
- No Scheduler.run execution.
- No Scheduler.run modification.
- No runtime import.
- No handler call.
- No mark_route_frame_stale call.
- No frame write by 0207.
- No ControlProxy frame write.
- No GitHub API/network.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/tools/test_audit_provenance_repair_0207.py \
  tests/rules/test_provenance_repair_audit_0207_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
