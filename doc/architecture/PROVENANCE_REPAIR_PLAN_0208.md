# 0208 — Provenance repair plan

## Decision

0208 creates a forward-only provenance repair plan.

The input is provenance_repair_audit.json.
The output is provenance_repair_plan.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0208 does not repair provenance.
0208 does not rewrite runtime history.
0208 does not write SQL or Qdrant.
P0209 may write the forward-only provenance repair acceptance.

## Why this exists

0207 proved that `source_baseline_ref` and `source_entry_digest` are missing
from the P0200 post-execution acceptance artifact, while candidate values exist
elsewhere in the runtime chain.

0208 selects those candidates and records the repair strategy without writing the
repair itself.

## Selected candidates

- `source_baseline_ref` comes from
  `controlled_dev_routeproxy_smoke_post_execution_acceptance.json` field
  `controlled_dev_baseline_ref`.
- `source_entry_digest` comes from
  `controlled_dev_routeproxy_smoke_registry.jsonl` field `entry_digest`.

## Boundary

0208:

- reads `provenance_repair_audit.json`,
- selects `source_baseline_ref` candidate,
- selects `source_entry_digest` candidate,
- records `forward_only_artifact` repair strategy,
- writes optional `provenance_repair_plan.json`.

0208 does not:

- repair `source_baseline_ref`,
- repair `source_entry_digest`,
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

If 0208 succeeds, P0209 may write `provenance_repair_acceptance.json` only.
