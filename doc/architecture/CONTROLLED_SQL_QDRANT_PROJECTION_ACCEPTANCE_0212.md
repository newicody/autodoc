# 0212 — Controlled SQL/Qdrant projection acceptance

## Decision

0212 closes Bloc F with controlled SQL/Qdrant projection acceptance.

The input is sql_qdrant_projection_plan.json.
The output is controlled_sql_qdrant_projection_acceptance.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0212 writes no SQL rows and no Qdrant points.
Qdrant payloads carry sql_ref.
SQL remains durable authority.
The next recommended patch is P0213 context recall integration audit.

## Why this exists

0211 selected existing SQL, Qdrant, rehydrate, and provenance surfaces. 0212
accepts the projection contract by writing a bounded acceptance artifact. It does
not touch live SQL or Qdrant.

## Accepted contract

- SQL is durable authority.
- Qdrant is projection/search/recall only.
- Qdrant payload carries `sql_ref`.
- Qdrant recall must rehydrate from SQL.
- Existing surfaces are reused before any new code.

## Boundary

0212:

- reads `sql_qdrant_projection_plan.json`,
- checks selected surfaces exist,
- builds a bounded projection record,
- checks `qdrant_payload.sql_ref`,
- writes `controlled_sql_qdrant_projection_acceptance.json`,
- closes Bloc F if accepted.

0212 does not:

- write SQL rows,
- write Qdrant points,
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

Bloc G starts with P0213 context recall integration audit.
