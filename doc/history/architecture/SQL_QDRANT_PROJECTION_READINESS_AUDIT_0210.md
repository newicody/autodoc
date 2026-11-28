# 0210 — SQL/Qdrant projection readiness audit

## Decision

0210 opens Bloc F with SQL/Qdrant projection readiness audit.

The input is provenance_repair_acceptance.json.
The output is sql_qdrant_projection_readiness_audit.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0210 does not write SQL or Qdrant.
SQL remains durable authority.
Qdrant remains projection/search/recall only.
P0211 may plan SQL/Qdrant projection.

## Why this exists

Bloc E repaired the missing provenance chain using a forward-only artifact. Bloc F
can now audit whether existing SQL/Qdrant surfaces are ready for a projection
plan without introducing new backends.

## Boundary

0210:

- reads `provenance_repair_acceptance.json`,
- verifies Bloc E is accepted,
- scans existing repository surfaces by file reads only,
- records SQL/sql_ref surfaces,
- records Qdrant/vector surfaces,
- records rehydrate surfaces,
- writes optional `sql_qdrant_projection_readiness_audit.json`.

0210 does not:

- write SQL,
- write Qdrant,
- add a new SQL backend,
- add a new Qdrant backend,
- rewrite runtime history,
- execute Scheduler.run,
- modify Scheduler.run,
- import runtime handler modules,
- call runtime handler modules,
- write ControlProxy or RouteProxy frames,
- call GitHub API,
- use network.

## Projection contract

- SQL remains durable authority.
- Qdrant remains projection/search/recall only.
- Qdrant payloads must carry `sql_ref`.
- Query results must be rehydrated from SQL.
- Provenance repair acceptance is used as chain repair proof.

## Next

If 0210 succeeds, P0211 may plan SQL/Qdrant projection.
