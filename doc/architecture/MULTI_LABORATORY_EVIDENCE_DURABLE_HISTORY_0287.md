# Multi-laboratory evidence durable history

```text
approved r6 weighting decision
→ optimistic append command
→ MultiLaboratoryEvidenceHistoryPort
→ SQL-addressed entry
→ append-only digest-chained snapshot
```

The first entry uses a zero previous digest. Later entries reference the prior
entry digest. SQL is authoritative; Qdrant remains projection-only.

R7 performs no Scheduler selection, laboratory execution, EventBus
publication or GitHub mutation. R8 will define Scheduler-owned selection
constraints over the durable head.
