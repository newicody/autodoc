# Qdrant SQL-authority scope and strict gRPC contract — 0271-r4

## Problem closed

The live 0269 smoke proved real projection and recall over gRPC, but a shared
collection can contain `sql_ref` values owned by another SQLite or PostgreSQL
authority. Such hits must never reach the current SQL rehydration step.

The successful network capture also established the intended split:

- REST administration: `http://127.0.0.1:6333`;
- gRPC data operations: `127.0.0.1:6334`.

## Reuse decision

0271-r4 wraps the existing `QdrantProjectionExecutor` protocol. It does not add
a Qdrant manager, worker, client or orchestrator.

The wrapper:

1. adds `payload.sql_authority_ref` and `payload.sql_store_kind` before upsert;
2. oversamples recall within the existing policy bound;
3. rejects foreign and legacy unscoped hits before SQL rehydration;
4. delegates close to the existing concrete executor.

SQL remains the durable authority. Qdrant remains a reconstructible projection.

## Transport contract

`QdrantStrictGrpcTransportPolicy` requires separate REST and gRPC ports. In
strict mode, `prefer_grpc` must be true. The REST URL is retained for
administration/readiness only; the requested data transport is gRPC.

This contract records operator intent. 0271-r5 will bind it to the existing
0262, 0263 and 0269 live CLIs and add live report proofs.

## Boundaries

- no network IO in this patch;
- no Qdrant service or collection creation;
- no SQL read or write;
- SHM remains unchanged;
- RouteProxy and ControlProxy remain unchanged;
- no Scheduler loop modification;
- no API-key value serialization.
