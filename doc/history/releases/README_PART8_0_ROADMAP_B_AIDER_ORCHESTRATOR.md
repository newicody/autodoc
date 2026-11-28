# Part 8.0 — Roadmap B Aider Orchestrator

Part 8.0 adds a Python orchestrator for Roadmap B.

It uses Aider to create patch bundles, then applies them with the existing
`apply_patch_queue.py` workflow.

The orchestrator is conservative:

```text
one small step by default
Aider auto-commits disabled
patch queue remains authoritative
tests run after each step
operator approval required for sensitive changes
```
