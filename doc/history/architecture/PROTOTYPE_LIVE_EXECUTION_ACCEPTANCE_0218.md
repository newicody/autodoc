# 0218 — Prototype live execution acceptance

## Decision

0218 executes and accepts the live controlled prototype.

The input is prototype_live_execution_plan.json.
The output is prototype_live_execution_acceptance.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

This is not another contract-only smoke loop.
P0218 must produce true flags.

Target path:

```text
context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact
```

## What 0218 does

0218 performs real local SQL write/read using a stdlib sqlite dev store.
0218 performs real local Qdrant create/upsert/query.
0218 extracts `payload.sql_ref` from Qdrant.
0218 reads the SQL record by `sql_ref`.
0218 rehydrates the response artifact.
0218 writes `prototype_live_response.json`.

`prototype_success` must be true only after the complete path succeeds.
prototype_success must be true only after the complete path succeeds.

## Boundary

0218:

- reads `prototype_live_execution_plan.json`,
- creates `prototype-live/`,
- writes a SQL dev record,
- creates/recreates the dedicated local Qdrant collection,
- upserts a Qdrant point,
- queries Qdrant,
- extracts `sql_ref`,
- reads the SQL record,
- rehydrates the response,
- writes `prototype_live_response.json`,
- writes `prototype_live_execution_acceptance.json`,
- closes Bloc H and the prototype cycle if successful.

0218 does not:

- call external network,
- call GitHub API,
- add a new SQL backend,
- add a new Qdrant backend,
- add a new inference path,
- rewrite runtime history,
- execute Scheduler.run,
- modify Scheduler.run,
- import runtime handler modules,
- write ControlProxy or RouteProxy frames.

Only localhost Qdrant is allowed.

## Required true flags

P0218 must produce true flags:

```text
sql_written_by_0218
qdrant_written_by_0218
qdrant_queried_by_0218
sql_record_read_by_0218
rehydration_executed_by_0218
response_artifact_written_by_0218
prototype_success
```

## Next

After a successful P0218 run, the next document is the server and Git
configuration runbook.
