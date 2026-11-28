# 0216 — Prototype live readiness audit

## Decision

0216 opens Bloc H with prototype live readiness audit.

The input is controlled_context_recall_integration_acceptance.json.
The output is prototype_live_readiness_audit.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

This is not another contract-only smoke loop.
P0218 must produce true flags.

Target path:

```text
context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact
```

## Why this exists

Bloc G proved the integration contract, but did not execute live Qdrant or SQL.
Bloc H must prepare a real controlled prototype execution. P0216 records the live
requirements and keeps the boundary safe.

## Boundary

0216:

- reads `controlled_context_recall_integration_acceptance.json`,
- verifies Bloc G is complete,
- checks selected surfaces exist,
- defines `runtime/dev-controlled/prototype-live`,
- records local Qdrant and dev SQL requirements,
- records P0218 required true flags,
- may optionally probe localhost Qdrant,
- writes optional `prototype_live_readiness_audit.json`.

0216 does not write SQL or Qdrant.
0216 may optionally probe localhost Qdrant.

0216 does not:

- perform live Qdrant recall,
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
- use external network.

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

If 0216 succeeds, P0217 may plan live prototype execution.
