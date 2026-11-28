# 0148 — SQL persistence handoff

0148 creates a structured handoff envelope from the validated local artifact
vector-indexing result toward SQL persistence.

The current validated path is:

```text
artifact_intake_contract
-> dynamic artifact route refs
-> Scheduler-shaped request frame
-> OpenVINO/E5 full vector handoff
-> Qdrant projection/search
-> vector_indexing_result frame
-> artifact_vector_indexing_report.json
```

0148 adds:

```text
artifact_vector_indexing_report.json
+ artifact_intake_contract.json
+ optional vector_indexing_result frame
-> sql_persistence_handoff.json
-> sql_persistence_handoff_report.md
```

Boundary:

- `src/context/sql_persistence_handoff_contract.py` is pure and serializable.
- `tools/run_sql_persistence_handoff_smoke.py` is an operator smoke tool only.
- 0148 does not write SQL rows.
- 0148 does not create a SQL worker or orchestrator.
- SQLContextStore remains the durable authority.
- Qdrant remains a projection and recall index.
- OpenVINO and Qdrant adapters are not modified.
- The Scheduler run loop is not modified.

The next patch can connect this handoff to the existing SQLContextStore surface.
