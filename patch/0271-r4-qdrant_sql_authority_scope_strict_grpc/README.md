# 0271-r4 — Qdrant SQL-authority scope and strict gRPC contract

## Purpose

Add a reusable membrane around the existing `QdrantProjectionExecutor` so that
Qdrant points carry an opaque SQL-authority identity and recall rejects foreign
or legacy unscoped hits before SQL rehydration.

The patch also records the validated transport split:

- REST administration/readiness: port 6333;
- Qdrant data operations: gRPC port 6334.

## Important boundary

This revision does **not** bind the membrane into 0262, 0263 or 0269 yet. It
adds the reusable implementation, readiness CLI, tests and documentation only.
The follow-up 0271-r5 will extend the existing live CLIs.

No network call, Qdrant operation, SQL operation, SHM access, service start,
Scheduler loop change, manager or orchestrator is introduced.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

Readiness-only check:

```bash
PYTHONPATH=src:. python \
  tools/check_qdrant_sql_authority_scope_0271.py \
  --db-path .var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3 \
  --qdrant-url http://127.0.0.1:6333 \
  --qdrant-grpc-port 6334 \
  --qdrant-prefer-grpc \
  --strict-data-grpc \
  --format summary
```
