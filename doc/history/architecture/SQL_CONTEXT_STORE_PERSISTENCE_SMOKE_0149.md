# 0149 — SQLContextStore persistence smoke

0149 connects the 0148 SQL persistence handoff to the existing SQL context authority boundary in a conservative way.

The validated path becomes:

```text
artifact_vector_indexing_report.json
+ artifact_intake_contract.json
+ vector_indexing_result frame
-> sql_persistence_handoff.json
-> sql_context_store_persistence_record.json
-> sql_context_store_persistence_report.md
```

Boundary:

- `src/context/sql_context_store_persistence_contract.py` is pure and serializable.
- `tools/run_sql_context_store_persistence_smoke.py` reads the 0148 handoff and writes a SQLContextStore persistence record.
- The tool inspects `src/context/sql_context_store.py` as the existing durable authority surface.
- 0149 does not create a SQL worker, SQL orchestrator, or backend-specific database client.
- 0149 does not call OpenVINO or Qdrant.
- Qdrant identifiers are carried as projection metadata only.
- The Scheduler run loop is not modified.

0149 is intentionally a persistence-record smoke. A later patch can bind this record to a concrete existing SQLContextStore method once that method is explicitly selected.
