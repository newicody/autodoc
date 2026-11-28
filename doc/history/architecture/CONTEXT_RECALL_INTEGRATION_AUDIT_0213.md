# 0213 — Context recall integration audit

## Decision

0213 opens Bloc G with context recall integration audit.

The input is controlled_sql_qdrant_projection_acceptance.json.
The output is context_recall_integration_audit.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0213 does not execute recall.
0213 does not query Qdrant.
0213 does not read SQL records.

The target path is:

```text
context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact
```

## Why this exists

Bloc F accepted the SQL/Qdrant projection contract, but did not execute real
recall. Bloc G now audits existing surfaces for the first controlled
context/recall/rehydrate path.

## Boundary

0213:

- reads `controlled_sql_qdrant_projection_acceptance.json`,
- verifies Bloc F is accepted,
- scans existing repository surfaces by file reads only,
- records context/query surfaces,
- records recall/Qdrant surfaces,
- records sql_ref rehydrate surfaces,
- records response/result artifact surfaces,
- writes optional `context_recall_integration_audit.json`.

0213 does not:

- execute recall,
- query Qdrant,
- read SQL records,
- write SQL,
- write Qdrant,
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

## Next

If 0213 succeeds, P0214 may plan context recall integration.
