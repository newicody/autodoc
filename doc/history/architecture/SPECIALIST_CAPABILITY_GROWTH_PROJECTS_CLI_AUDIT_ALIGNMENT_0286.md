# 0286-r6-r1 — CLI and audit alignment

The r6 core adapter already enforced `approve`, `execute` and exact digest
confirmation. The 0286 reuse audit, however, deliberately detects the concrete
operator CLI:

```text
tools/apply_specialist_capability_growth_projects_projection_0286.py
```

This correction closes that gap without changing the r6 contracts.

## Flow

```text
r5 plan JSON
→ schema and SHA-256 recomputation
→ preview by default
→ operator approve
→ --execute
→ exact --confirm-plan-digest
→ existing gh api boundary
→ Issue comment + ProjectV2 fields
```

GitHub Projects reste non autoritatif. SQL reste l’autorité durable. Scheduler
reste l’unique autorité d’orchestration. Qdrant reste projection/rappel.
