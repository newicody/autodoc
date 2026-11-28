# 0215 — Controlled context recall integration acceptance

## Decision

0215 closes Bloc G with controlled context recall integration acceptance.

The input is context_recall_integration_plan.json.
The output is controlled_context_recall_integration_acceptance.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0215 does not perform live Qdrant recall.
0215 does not query Qdrant.
0215 does not read SQL records.
The next recommended patch is P0216 prototype readiness audit.

## Why this exists

0214 selected existing surfaces for the target path. 0215 accepts that contract
by producing a controlled response artifact and controlled recall/rehydrate
records without touching live Qdrant or SQL.

## Accepted contract

```text
context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact
```

This remains controlled acceptance, not live inference or live Qdrant/SQL IO.

## Boundary

0215:

- reads `context_recall_integration_plan.json`,
- checks selected surfaces exist,
- builds a controlled context/query artifact,
- builds a controlled recall result containing `sql_ref`,
- builds a controlled rehydrate result requiring SQL authority,
- builds a controlled response artifact,
- writes `controlled_context_recall_integration_acceptance.json`,
- closes Bloc G if accepted.

0215 does not:

- perform live Qdrant recall,
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

Bloc H starts with P0216 prototype readiness audit.
