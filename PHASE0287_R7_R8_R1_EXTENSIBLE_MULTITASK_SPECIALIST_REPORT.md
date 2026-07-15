# Phase 0287-r7-r8-r1 — extensible multitask specialist model

## Decision

The existing portable specialist, specialist/laboratory message v2 and deep
analysis contracts remain unchanged. This phase adds a generic task model above
them so one specialist can expose several capabilities and task types without
becoming an orchestrator.

## Reuse audit

Reused surfaces:

- `PortableSpecialistDescriptor` and `SpecialistCapabilityContract`;
- `SpecialistArtifactReference` and `SpecialistExchangeError`;
- `DeepAnalysisRequest` and `DeepAnalysisContribution`;
- the existing Scheduler authority and laboratory boundaries;
- the already implemented OpenVINO runtime surfaces by typed reference only.

No new global registry, Scheduler, queue, worker, bus, laboratory manager,
inference backend or model loader is introduced.

## Public contracts

- `missipy.specialist.task_type.v1`;
- `missipy.specialist.task_execution_binding.v1`;
- `missipy.specialist.task_request.v1`;
- `missipy.specialist.task_dependency.v1`;
- `missipy.specialist.task_plan.v1`;
- `missipy.specialist.followup_task_proposal.v1`;
- `missipy.specialist.task_result.v1`;
- `missipy.specialist.multitask_definition.v1`.

## Multitask rules

- one task invokes one explicit capability;
- one plan contains tasks for one portable specialist identity;
- dependencies must form an acyclic graph;
- independent tasks may be reported as ready, but only Scheduler may execute
  them;
- follow-up tasks and specialist interventions are proposals requiring a later
  Scheduler decision;
- task state, artifacts and results remain immutable and replay-identifiable.

## OpenVINO boundary

`SpecialistTaskExecutionBinding` records an existing backend, operation, runtime
contract, model/tokenizer identities and device preferences. It does not load a
model or import OpenVINO. A binding beginning with `openvino:` explicitly reports
that the existing OpenVINO backend is reused and that no backend implementation
was created by this phase.

## Deep-analysis compatibility

The r8 deep-analysis request remains the public domain-analysis contract. Pure
bridge functions wrap it as `specialist-task-type:analysis.deep` and preserve
its contribution inside the generic task-result envelope. No detail is lost and
no global synthesis is inferred.

## Boundaries

```text
Scheduler modified: false
new orchestrator: false
new global registry: false
laboratory runtime created: false
specialist executed: false
OpenVINO reimplemented: false
SQL/Qdrant write: false
ControlProxy modified: false
GitHub mutation: false
INSTALLATION.md changed: false
```

## Validation

```text
code_rule_review: done
code_rule_update_required: false
installation_update_required: false
live_path_status: n/a
```

## Code-rule alignment

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: immutable stdlib-only contracts extend existing specialist boundaries
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
```
