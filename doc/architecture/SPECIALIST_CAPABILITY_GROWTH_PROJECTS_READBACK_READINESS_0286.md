# Specialist capability growth — Projects readback readiness

## Flow

```text
immutable r5 publication plan
+ approved/digest-confirmed r6 result
+ query-only Issue comment snapshot
+ query-only ProjectV2 item field snapshot
→ pure correlation verifier
→ readback evidence
```

A local fixture may establish `readback_ready`. Deployment readiness requires
the same verification against a live GitHub query-only readback.

## Correlation

The evidence verifies:

- repository, Issue, ProjectV2 project and item identity;
- exact `plan_digest` confirmation by r6;
- one and only one comment containing the r5 marker;
- exact comment body and SHA-256;
- the comment identifier returned by r6;
- all nine desired ProjectV2 values;
- `sql_ref`, revision and decision correlation.

## Authority

GitHub Projects remains a non-authoritative workflow projection. SQL remains
the durable authority, Scheduler remains the only orchestrator, and Qdrant
remains a projection/recall surface. Readback never creates a decision or
authorizes execution.
