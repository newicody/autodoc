# Phase 0285-r2 — Specialist capability growth proposal contract

Patch: `0285-r2-specialist-capability-growth-proposal-contract`

## Result

The phase adds the immutable, evidence-backed proposal boundary identified by the
0285-r1 reuse audit:

```text
evidence references
→ non-authoritative capability-growth proposal
→ future explicit operator decision
```

`SpecialistCapabilityEvidenceRef` binds a typed evidence reference to a stable
specialist identity, one capability claim and a lowercase SHA-256 digest.
`SpecialistCapabilityGrowthProposal` aggregates those references without
approving them, mutating a descriptor, writing durable state or allowing a
Scheduler dispatch.

The proposal may be authored by an operator, specialist, laboratory, system or
Copilot surface. None of those proposer identities receives authorization from
this contract. The explicit operator decision belongs to 0285-r4.

## Architecture boundary

- Scheduler remains the only orchestration authority.
- SQL remains the durable authority.
- Qdrant remains projection and recall only.
- EventBus remains observation only.
- GitHub Projects and Copilot remain workflow/advisory surfaces.
- No global specialist registry is introduced.
- No specialist, laboratory or Copilot self-authorization is permitted.
- No runtime, backend, storage port or network adapter is introduced.

## Validation

- immutable dataclasses: covered;
- deterministic canonical mapping and digest: covered;
- mismatched specialist/capability evidence: rejected;
- duplicate evidence references: rejected;
- non-deprecation contract envelopes: required;
- deprecation without new contract envelopes: accepted;
- architecture rules: covered.

## Next phase

`0285-r3-portable-specialist-revision-lineage-contract`

That phase will model stable specialist identity and immutable revision lineage.
It will not decide or persist a proposal.

## Required phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing immutable contract, stdlib-first, typed-reference and explicit-authority rules already cover this phase
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
INSTALLATION reviewed: yes
INSTALLATION modified: no
INSTALLATION reason: no Projects deployment surface changes in 0285-r2
```
