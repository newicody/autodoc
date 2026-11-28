# Changelog — 0191 Isolated route pipeline artifact audit

## Added

- Artifact-only audit for `isolated_route_pipeline_smoke.json`.
- Verification that 0184 consumed `scheduler.route_requests.policy_scoped.jsonl`.
- Counter and artifact consistency checks for 0179 and 0184 through 0188.
- Frame path boundary checks under `isolated_runtime_root`.
- Optional `isolated_route_pipeline_artifact_audit.json` output.

## Not changed

- No runtime handler import.
- No handler execution.
- No RouteProxy runtime preparation.
- No frame write.
- No Scheduler.run modification.
