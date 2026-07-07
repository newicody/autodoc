# 0207 — Provenance repair audit

## Decision

0207 opens Bloc E with a provenance repair audit.

The input is controlproxy_routeproxy_coherence_acceptance.json.
The output is provenance_repair_audit.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0207 does not repair provenance.
0207 does not rewrite runtime history.
0207 does not write SQL or Qdrant.
P0208 may plan a forward-only provenance repair.

## Why this exists

Earlier controlled dev acceptance preserved a known warning:

```text
source_baseline_ref or source_entry_digest missing from P0200 acceptance
```

This is not a runtime failure, but it must be audited before SQL/Qdrant
provenance repair is planned.

## Boundary

0207:

- reads `controlproxy_routeproxy_coherence_acceptance.json`,
- verifies Bloc D is accepted,
- inspects the runtime artifact chain,
- detects missing `source_baseline_ref`,
- detects missing `source_entry_digest`,
- collects candidate provenance refs from existing artifacts,
- writes optional `provenance_repair_audit.json`.

0207 does not:

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

If 0207 succeeds, P0208 may plan a forward-only provenance repair artifact.
