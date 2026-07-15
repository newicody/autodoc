# Phase 0287 roadmap

1. `0287-r1` — reuse audit.
2. `0287-r2` — immutable evidence item and aggregate contract.
3. `0287-r3` — laboratory/visit/specialist provenance contract.
4. `0287-r4` — digest-based deduplication.
5. `0287-r5` — contradiction detection.
6. `0287-r6` — operator-authorized weighting policy.
7. `0287-r7` — append-only SQL-authority history.
8. `0287-r8` — Scheduler selection constraints.
9. `0287-r9` — passive EventBus/PassiveSupervisor/Cell Lens projection.
10. `0287-r10` — multi-laboratory closed-loop smoke.

## Locked boundaries

- Scheduler remains the only orchestrator.
- SQL remains the durable authority.
- Qdrant remains projection and recall.
- EventBus remains observation-only.
- GitHub Projects remains a workflow/review projection.
- no LaboratoryManager.
- no global evidence registry.
- no laboratory or specialist self-authorization.
