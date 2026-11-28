# 0209 — Forward-only provenance repair acceptance

## Decision

0209 closes Bloc E with forward-only provenance repair acceptance.

The input is provenance_repair_plan.json.
The output is provenance_repair_acceptance.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0209 writes only the forward-only repair acceptance artifact.
0209 does not rewrite runtime history.
0209 does not write SQL or Qdrant.
The next recommended patch is P0210 SQL/Qdrant projection readiness audit.

## Why this exists

0208 selected canonical provenance candidates without writing the repair.
0209 records those values in a new forward-only acceptance artifact.

It does not mutate P0200 and does not rewrite the runtime chain.

## Accepted repair

The repaired fields are:

- `source_baseline_ref`,
- `source_entry_digest`.

The repair is expressed as a new `provenance_repair_acceptance.json` artifact.

## Boundary

0209:

- reads `provenance_repair_plan.json`,
- validates the source artifact still carries the expected baseline candidate,
- validates the registry still carries the expected entry digest,
- writes `provenance_repair_acceptance.json`,
- closes Bloc E if accepted.

0209 does not:

- rewrite `controlled_dev_routeproxy_smoke_post_execution_acceptance.json`,
- rewrite runtime history,
- write SQL,
- write Qdrant,
- execute Scheduler.run,
- modify Scheduler.run,
- import runtime handler modules,
- call mark_route_frame_stale,
- write ControlProxy or RouteProxy frames,
- call GitHub API,
- use network.

## Next

Bloc F starts with P0210 SQL/Qdrant projection readiness audit.
