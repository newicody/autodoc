# Phase 0287-r7-r2-r4 — Copilot v2 producer-test rebase

## Status

Corrective sub-revision for the still-uncommitted `0287-r7-r2` working tree.
It replaces the failed r3 patch; r3 must not be applied.

## Observed failure

The active Copilot producer is v2 and the complete suite correctly exposed three
historical executable tests still feeding the v1 response shape. The first r3
migration patch was generated from truncated test fixtures and its hunks did not
match the real files.

## Decision

- keep production code unchanged;
- keep pure v1 reader tests unchanged;
- migrate only the three tests that invoke the active producer;
- replace complete test-function blocks instead of anchoring around stale line
  positions;
- reformat the 14-line dual-artifact test while preserving its behavior;
- do not infer v2 semantics from v1 fields.

## Reuse audit

Reused unchanged:

- `run_autodoc_copilot_advisory.py`;
- `build_autodoc_authoritative_request.py`;
- `build_autodoc_dual_manifest.py`;
- historical `extract_advisory()` coverage;
- authority and fail-closed boundaries.

No Scheduler, laboratory, SQL, Qdrant, OpenVINO, EventBus, ProjectV2 mutation,
new adapter, or installation change is introduced.

## Acceptance

The complete suite must show that:

1. direct v2 JSON produces `missipy.github.copilot_advisory.v2`;
2. JSONL assistant output produces the same v2 artifact;
3. the three-artifact workflow accepts the v2 advisory filename and authority
   boundary;
4. pure v1 extraction tests remain present;
5. no v1-to-v2 semantic conversion exists in production code.

code_rule_review: done
code_rule_update_required: false
live_path_status: transition
installation_update_required: false
