# 0287-r7-r8-r2 — context revision SQL authority

Prerequisite: `0287-r7-r8-r1-extensible-multitask-specialist-model`.

This patch adds a versioned DB-API authority for semantic context revisions
without modifying `missipy.sql_context_store.v1`.

It provides:

- immutable context authority objects;
- content-addressed artifact descriptors;
- multi-parent context revision DAGs;
- complete active/superseded/invalidated membership snapshots;
- graph relations and provenance;
- Qdrant projection metadata without raw vectors;
- a bridge from historical `SqlContextRecord` records;
- SQLite tests and PostgreSQL-compatible DB-API SQL.

It does not modify Scheduler, ControlProxy, OpenVINO, Qdrant, EventBus, GitHub
or `INSTALLATION.md`.

Apply from the repository root with `apply_patch_queue.py`.
