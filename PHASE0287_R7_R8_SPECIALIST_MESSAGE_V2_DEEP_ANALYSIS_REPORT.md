# Phase 0287-r7-r8 — specialist message v2 and deep analysis

## Objective

Version the existing specialist/laboratory exchange boundary without changing
`missipy.specialist.laboratory_message.v1`, then define a generic specialist
mission/result contract for deep domain analysis.

## Reuse audit

Reused unchanged:

- `specialist_laboratory_message_contract_0284.py` as the historical v1 reader;
- `correlated_research_work_package_0287.py` as the research-package input;
- `specialist_liaison_synthesis.py` as the later synthesis boundary;
- the existing Scheduler as the only orchestration authority.

A companion v2 module is justified because changing the public v1 fields or
conversation semantics in place would violate the versioning rule in
`code_rule.md`.

## Added public contracts

```text
missipy.specialist.artifact_reference.v1
missipy.specialist.exchange_error.v1
missipy.specialist.laboratory_message.v2
missipy.specialist.laboratory_conversation.v2
missipy.specialist.deep_analysis_request.v1
missipy.specialist.deep_analysis_finding.v1
missipy.specialist.deep_analysis_contribution.v1
missipy.specialist.output_fragment_projection.v1
```

## Exchange guarantees

- canonical SHA-256 digest for every message payload;
- SHA-256 and storage reference for every exchanged artifact;
- stable `correlation_ref` and deterministic `idempotency_key`;
- ordered append-only conversation with unique messages and keys;
- explicit continuation from one visit to another;
- normalized completion and error messages;
- no direct specialist-to-specialist execution;
- no transport, persistence or scheduling side effect in the contracts.

## Analysis guarantees

Specialists primarily produce rich domain analyses. Contributions preserve:

- evidence-linked findings;
- observed, inferred and unresolved status;
- uncertainties and contradictions;
- limitations and recommendations;
- requested context and specialist follow-ups;
- digest-backed artifact references;
- a deterministic projection for the existing liaison fragment boundary.

A local or global synthesis is accepted only when the request explicitly asks
for that contribution kind. The default remains `domain_analysis`; global
mutualization happens later through `SpecialistLiaisonSynthesis`.

## Boundaries

```text
Scheduler modified: no
new orchestrator: no
transport created: no
SQL/Qdrant write: no
OpenVINO call: no
GitHub mutation: no
external dependency added: no
```

## Verification

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing versioning, immutable contract and Scheduler rules apply
live_path_status: n/a
```
