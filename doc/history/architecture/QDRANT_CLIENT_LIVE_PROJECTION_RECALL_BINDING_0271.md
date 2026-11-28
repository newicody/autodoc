# Qdrant-client live projection and recall binding — 0271-r3

## Decision

Reuse the existing `QdrantProjectionExecutor` protocol and the concrete
`QdrantClientProjectionExecutor` added by 0271-r2.  The existing 0262 and 0263
CLI boundaries now accept a mutually exclusive live opt-in in addition to their
historical demo executors.

## Live path

```text
0261 embedding report
  -> 0262 existing projection use case
  -> QdrantClientProjectionExecutor (write gate)
  -> existing Qdrant service
  -> 0263 existing recall use case
  -> QdrantClientProjectionExecutor (search gate)
  -> sql_ref hits
  -> existing SQLiteSqlContextStore rehydrate
```

Qdrant remains a reconstructible projection. SQL remains the durable authority.
The server must already be running under OpenRC/OS/admin responsibility.

## Operator gates

Live execution requires:

- `--execute`;
- a `policy_decision_id` beginning with `policy:`;
- `--live-qdrant`;
- an injected URL, timeout, optional gRPC preference and API-key environment
  variable name.

The API-key value is read from the environment only inside the IO CLI and is
never written to reports or child process arguments.

## Boundaries

- no collection creation;
- no Qdrant daemon start;
- no PostgreSQL or OpenVINO start;
- no SHM, RouteProxy or ControlProxy modification;
- no Scheduler loop modification;
- no manager or orchestrator;
- demo mode remains available for deterministic local regression tests.
