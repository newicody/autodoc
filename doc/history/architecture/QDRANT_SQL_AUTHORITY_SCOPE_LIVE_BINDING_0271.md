# Qdrant SQL-authority scope live binding — 0271-r5

## Objective

Bind the reusable SQL-authority membrane from 0271-r4 to the existing live
projection and recall tools. A shared Qdrant collection may contain points from
several SQL stores, but only references owned by the current SQL authority may
reach SQL rehydration.

## Existing surfaces reused

- 0262 projection use case and CLI;
- 0263 recall/rehydration use case and CLI;
- 0269 one-shot composition;
- `QdrantClientProjectionExecutor` from 0271-r2;
- `SqlAuthorityScopedQdrantExecutor` and
  `QdrantStrictGrpcTransportPolicy` from 0271-r4.

No manager, worker or parallel orchestration path is added.

## Live flow

```text
0269 database_path
  -> derive opaque sql_authority_ref
  -> 0262 scoped upsert
       payload.sql_ref
       payload.sql_authority_ref
       payload.sql_store_kind
  -> qdrant-client data operations over gRPC 6334
  -> 0263 scoped recall
       foreign and legacy unscoped hits rejected
  -> current SQL store rehydrate
  -> missing_count=0
```

The current implementation filters returned hits inside the existing protocol
wrapper before SQL rehydration. It oversamples within the existing policy cap.
It does not delete or migrate foreign or legacy points.

## Transport contract

Live execution now requires both `qdrant_prefer_grpc=True` and
`strict_data_grpc=True`. The REST URL remains a distinct administration endpoint
such as `http://127.0.0.1:6333`; data operations request gRPC on port 6334.

## Boundaries

- SQL remains the durable authority;
- Qdrant remains a reconstructible projection;
- OpenRC/OS/admin starts and configures Qdrant;
- no collection creation, deletion or migration;
- no SQL write beyond the pre-existing 0260 step;
- no SHM, RouteProxy or ControlProxy change;
- no Scheduler loop change;
- no API-key value serialization.
