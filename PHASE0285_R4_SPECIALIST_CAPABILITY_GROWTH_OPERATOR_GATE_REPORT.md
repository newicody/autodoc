# Phase 0285-r4 — specialist capability growth operator gate report

Date: 2026-07-14

Patch: `0285-r4-specialist-capability-growth-operator-gate`

## Objective

Insert the explicit operator authority boundary after the r2 proposal and r3 immutable
candidate revision, without adding persistence, runtime selection or orchestration.

## Result

The phase adds:

- `SpecialistCapabilityGrowthDecision` for approve/reject/defer outcomes;
- `SpecialistCapabilityGrowthOperatorGate` for pure policy evaluation;
- deterministic policy and decision SHA-256 digests;
- correlation to proposal, candidate revision, base lineage and operator identity;
- rejection of approvals carrying policy issues;
- explicit flags proving that approval does not write SQL or dispatch the Scheduler.

The gate accepts only `operator:` identities. Specialist, laboratory and Copilot
references cannot authorize capability growth through this contract.

## Architecture boundary

- Scheduler remains the only orchestration authority.
- SQL remains the durable authority; r4 performs no write.
- Qdrant remains projection and recall only.
- EventBus remains observation only.
- no global specialist registry or LaboratoryManager;
- no backend, network, GitHub mutation, OpenVINO call or external dependency.

## Validation

- immutable gate and decision contracts: covered;
- approve/reject/defer semantics: covered;
- proposal/revision/lineage correlation: covered;
- evidence and operator policies: covered;
- deterministic digests: covered;
- architecture rules: covered.

## Next phase

`0285-r5-specialist-capability-growth-durable-history`

## Required phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing immutable contract, explicit authority and side-effect boundary rules cover r4
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: 0285.r4
context_contract_changed: true
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
sql_write_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
INSTALLATION reviewed: yes
INSTALLATION modified: no
INSTALLATION reason: no Projects deployment surface changes in 0285-r4
```
