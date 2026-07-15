# Phase 0287-r7-r3 — Copilot advisory v1/v2 intake compatibility

## Objective

Extend the existing dual-artifact contract and read-only intake so historical
`missipy.github.copilot_advisory.v1` artifacts and new first-opinion
`missipy.github.copilot_advisory.v2` artifacts are both accepted explicitly.

## Reuse audit

Reused and extended:

- `src/context/github_dual_artifact_contract_0275.py`;
- `src/context/github_dual_artifact_source_candidate_intake_0275.py`;
- the existing dual-artifact manifest and correlation checks;
- the existing `SourceCandidate` authority boundary.

Not added:

- no new runner, provider, adapter, queue or prompt manager;
- no Scheduler or laboratory orchestration change;
- no SQL, Qdrant, OpenVINO, EventBus or GitHub mutation;
- no external Python dependency.

## Contract decision

The v1 class and public meaning remain unchanged. A separate immutable v2 class
owns the four first-opinion fields. A schema dispatcher selects one class or the
other; it never maps `summary` to `concrete_objective` or otherwise infers v2
meaning from v1 content.

The v2 mapping is strict. Missing or extra public fields, legacy analytical
fields, invalid authority flags, empty success criteria and unsupported schema
versions fail closed.

## Intake result

The existing read-only intake now:

- accepts v1 and v2 advisory bytes;
- preserves the original advisory mapping in the intake result;
- validates the same manifest digest and correlation boundaries;
- keeps the authoritative request as the only source of candidate title/body;
- records only `advisory_ref`, response digest and `advisory_schema` metadata;
- keeps `advisory_content_copied=false`;
- lets the unchanged 0281 run assembler carry v2 through the reused intake.

code_rule_review: done
code_rule_update_required: false
code_rule_reason: the existing public-version rule is applied through distinct
v1 and v2 contracts and a strict schema dispatcher.

live_path_status: transition

Validation: 9 targeted context/rule tests pass, including v1, v2, strict type
rejection and unchanged 0281 run-assembly delegation.

This closes local contract/intake compatibility only. Projection into the
operator/laboratory preview and controlled publication remain subsequent
patches; no end-to-end operational closure is claimed.
