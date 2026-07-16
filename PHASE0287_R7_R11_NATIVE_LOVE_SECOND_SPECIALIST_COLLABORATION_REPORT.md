# Phase 0287-r7-r11 — Native love second specialist collaboration

## Objective

Close the first real two-specialist collaboration inside
`laboratory:love-studies-local` without introducing a second Scheduler,
laboratory manager, queue, EventBus or registry.

## Reuse audit

The phase reuses:

- the r10 native provider for the first specialist;
- `LaboratoryVisitRequest` and `LaboratoryVisitResult`;
- `SpecialistTaskRequest` and digest-backed `SpecialistArtifactReference`;
- `SpecialistLaboratoryMessageV2` and ordered v2 conversations;
- the existing `SchedulerContract`, Dispatcher event and Request reply path;
- the existing r10 Scheduler-owned registration identity, upgraded in place;
- the r9 relational-dynamics analysis contract and specialist descriptor.

The r10 provider is not modified. Its registry component is upgraded in place,
not duplicated. It remains historical evidence that r10
allowed only `specialist:love-concept-and-affect-analyst`.

## Implemented path

```text
first Scheduler visit
-> r10 first specialist implementation
-> concept/affect analysis
-> canonical SHA-256 artifact reference
-> v2 completion message
-> second task and visit prepared without execution
-> second Scheduler visit
-> relational-dynamics specialist
-> second digest-backed artifact
-> closed two-visit v2 conversation
```

The second specialist performs content-dependent analysis of reciprocity,
communication, commitment, boundaries, asymmetry, conflict, distance and trust.
It records the first analysis as explicit provenance but does not merely summarize
it and does not produce global synthesis.

## Authority boundaries

- Scheduler remains the only orchestration authority.
- The laboratory does not submit the follow-up visit automatically.
- The first specialist never calls the second specialist.
- Artifact identity is content-addressed and checked before execution.
- The in-memory resolver is a runtime test/input membrane, not durable authority.
- SQL, Qdrant, OpenVINO, EventBus, ControlProxy and GitHub are unchanged.
- Global liaison synthesis remains the next integration phase.

## Installation audit

`templates/github/projects-repository/INSTALLATION.md` was reviewed and is
unchanged. This phase adds no workflow, secret, token, OpenRC service, fcron
entry, remote mutation or Projects deployment command.

`doc/README_CURRENT.md` was also reviewed and left unchanged because the active
roadmap already contains the r11 second-specialist and r12 liaison-synthesis
markers consumed by the executable documentation rules.

## Validation

The targeted tests cover:

- the collaborative descriptor and both real specialists;
- preservation of the r10 first-only provider boundary;
- content-dependent second analysis;
- exact first-analysis artifact digest and metadata validation;
- refusal when the first artifact is unavailable;
- preparation without direct follow-up execution;
- two separate visits through the same Scheduler instance;
- four ordered v2 messages across two visits;
- explicit first-analysis provenance in the second result;
- absence of global synthesis and direct specialist invocation.

## Live-path status

`local_executable_two_specialist_chain = true`

`durable_sql_memory_connected = false`

`liaison_synthesis_connected = false`

`github_publication_connected = false`

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing Scheduler/Dispatcher/provider/message boundaries are reused
live_path_status: green
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```

The stdlib relational backend is content-dependent and non-dummy for the local
prototype. It remains behind the native laboratory provider and does not become
a kernel dependency.
