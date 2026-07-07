# 0211 — SQL/Qdrant projection plan

## Decision

0211 creates the SQL/Qdrant projection plan.

The input is sql_qdrant_projection_readiness_audit.json.
The output is sql_qdrant_projection_plan.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0211 does not write SQL or Qdrant.
SQL remains durable authority.
Qdrant remains projection/search/recall only.
P0212 may execute controlled SQL/Qdrant projection acceptance.

## Why this exists

0210 proved that existing SQL, Qdrant, rehydrate, and provenance surfaces are
available. 0211 selects those surfaces and records a controlled projection plan
without writing SQL or Qdrant.

## Projection contract

- SQL is durable authority.
- Qdrant is projection/search/recall only.
- Qdrant payloads carry `sql_ref`.
- Qdrant recall rehydrates from SQL.
- Forward-only provenance repair acceptance is the chain repair proof.

## Boundary

0211:

- reads `sql_qdrant_projection_readiness_audit.json`,
- selects SQL authority surface,
- selects Qdrant projection surface,
- selects SQL rehydrate surface,
- selects provenance repair acceptance surface,
- writes optional `sql_qdrant_projection_plan.json`.

0211 does not:

- write SQL,
- write Qdrant,
- add a new SQL backend,
- add a new Qdrant backend,
- rewrite runtime history,
- execute Scheduler.run,
- modify Scheduler.run,
- import runtime handler modules,
- write ControlProxy or RouteProxy frames,
- call GitHub API,
- use network.

## Next

If 0211 succeeds, P0212 may execute controlled SQL/Qdrant projection acceptance
and close Bloc F.
