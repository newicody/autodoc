# Phase 0287-r7-r9 — love-study contracts and specialist descriptors

## Objective

Declare the first concrete product domain without attaching a runtime:

- one local native laboratory descriptor;
- two portable and extensible multitask specialists;
- one authoritative request contract;
- attributable findings;
- two distinct deep-analysis outputs;
- one result index for the later liaison synthesis and final artifact.

## Reuse audit

The phase extends existing surfaces instead of creating parallel abstractions:

- `LaboratoryDescriptor` from `laboratory_framework_contract_0273.py`;
- `PortableSpecialistDescriptor` and capability/binding contracts from 0284;
- `ExtensibleMultitaskSpecialistDefinition` and `SpecialistTaskType` from r8-r1;
- the existing Scheduler-owned laboratory registry boundary planned for r10;
- the existing message-v2, context-revision, memory and liaison-synthesis paths.

No provider, handler registry, model runtime or orchestration loop is added.

## Declared product surface

```text
laboratory:love-studies-local
├── specialist:love-concept-and-affect-analyst
└── specialist:love-relational-dynamics-analyst
```

The laboratory is `autodoc_native`, `in_process`, network-disabled, declared and
disabled. It becomes executable only in r10.

## Specialist roles

The first specialist declares evidence extraction, concept analysis, affect
mapping, comparison, critique and optional local synthesis.

The second declares relational dynamics, reciprocity, communication, critique,
validation and bounded recommendation tasks. It can consume an authorized
analysis produced by the first specialist but never invokes that specialist
directly.

Global synthesis is not a default specialist output. It remains a later liaison
step after both detailed domain analyses and evidence validation.

## Public contracts

```text
missipy.love.study_request.v1
missipy.love.analysis_finding.v1
missipy.love.concept_affect_analysis.v1
missipy.love.relational_dynamics_analysis.v1
missipy.love.study_result.v1
missipy.love.prototype_definition.v1
```

Every finding is attributable and evidence-linked unless it explicitly records
an absent element. The second analysis requires a source analysis reference.
A result can claim `synthesized` only when both the liaison synthesis and final
artifact references exist.

## Boundaries

- Scheduler remains the only orchestration authority.
- SQL remains the durable context authority.
- Qdrant remains projection and recall only.
- OpenVINO is reused and not reimplemented.
- ControlProxy remains transport-only.
- No runtime is attached in r9.
- Global synthesis remains a later liaison step.
- No GitHub or ProjectV2 mutation occurs.

## Installation documentation

`templates/github/projects-repository/INSTALLATION.md` is not modified. This
phase adds no workflow, service, secret, token, environment variable or deploy
command.

## Verification

Targeted tests cover immutable request semantics, the disabled native laboratory,
multitask catalogs, evidence attribution, inter-analysis dependency, explicit
local synthesis and the final liaison/final-artifact requirement.
