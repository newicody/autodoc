# 0217 — Prototype live execution plan

## Decision

0217 creates the prototype live execution plan.

The input is prototype_live_readiness_audit.json.
The output is prototype_live_execution_plan.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

This is the plan for a real controlled P0218 execution.
P0218 must produce true flags.

Target path:

```text
context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact
```

## Why this exists

P0216 established that the live controlled prototype can be planned. 0217 turns
that readiness into exact P0218 execution instructions: SQL JSONL dev store,
Qdrant collection, deterministic vector, Qdrant point payload, Qdrant search,
SQL read, rehydrate, and response artifact.

## Boundary

0217:

- reads `prototype_live_readiness_audit.json`,
- writes `prototype_live_execution_plan.json`,
- plans SQL dev record,
- plans Qdrant collection creation,
- plans Qdrant point upsert,
- plans Qdrant query,
- plans SQL read,
- plans rehydrate,
- plans response artifact.

0217 does not execute the prototype.
0217 does not write SQL or Qdrant.

0217 does not:

- create Qdrant collections,
- upsert Qdrant points,
- query Qdrant semantic results,
- read SQL records,
- add a new SQL backend,
- add a new Qdrant backend,
- add a new inference path,
- rewrite runtime history,
- execute Scheduler.run,
- modify Scheduler.run,
- import runtime handler modules,
- write ControlProxy or RouteProxy frames,
- call GitHub API,
- use network.

## P0218 required true flags

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

If 0217 succeeds, P0218 may execute the live controlled prototype and close the
cycle.
