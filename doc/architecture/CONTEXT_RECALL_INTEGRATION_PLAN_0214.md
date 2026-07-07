# 0214 — Context recall integration plan

## Decision

0214 creates the context recall integration plan.

The input is context_recall_integration_audit.json.
The output is context_recall_integration_plan.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0214 does not execute recall.
0214 does not query Qdrant.
0214 does not read SQL records.
P0215 may execute controlled context recall integration acceptance.

## Why this exists

0213 found existing surfaces for context/query, recall/Qdrant, sql_ref
rehydration, and response/result artifacts. 0214 selects those surfaces and
records the controlled integration plan.

## Target path

```text
context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact
```

## Boundary

0214:

- reads `context_recall_integration_audit.json`,
- selects context/query surface,
- selects recall/Qdrant surface,
- selects sql_ref rehydrate surface,
- selects response/result artifact surface,
- selects projection/sql_ref surface,
- writes optional `context_recall_integration_plan.json`.

0214 does not:

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

If 0214 succeeds, P0215 may execute controlled context recall integration
acceptance and close Bloc G.
