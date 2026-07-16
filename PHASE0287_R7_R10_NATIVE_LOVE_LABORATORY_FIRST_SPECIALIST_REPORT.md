# Phase 0287-r7-r10 — native love laboratory and first specialist

## Objective

Turn the r9 declaration into one executable local laboratory surface and run the
first real multitask specialist against supplied text.

The phase must:

- reuse the Scheduler-owned runtime registry;
- reuse `LABORATORY_VISIT_REQUEST` and the existing Dispatcher handler surface;
- keep Scheduler as the only orchestration authority;
- execute `specialist:love-concept-and-affect-analyst`;
- produce content-dependent evidence and a versioned analysis;
- keep SQL, Qdrant, EventBus, ControlProxy and GitHub outside this unit.

## Reuse audit

The implementation reuses:

- `LaboratoryDescriptor`, `LaboratoryVisitRequest` and
  `LaboratoryVisitResult` from 0273;
- the historical `LaboratoryProvider` protocol from the fake-provider module;
- `SchedulerOwnedRuntimeComponentRegistration` and
  `SchedulerOwnedRuntimeRegistry` from 0257;
- the generic multitask request/result contracts from r8-r1;
- the love-study request and first-analysis contracts from r9;
- `LABORATORY_VISIT_REQUEST`, `SchedulerContract` and the existing Dispatcher
  registration surface from the 0274 binding pattern.

No LaboratoryManager, RuntimeManager, Scheduler, queue, EventBus or parallel
registry is created.

## Concrete provider

```text
laboratory:love-studies-local
provider_kind = autodoc_native
execution_boundary = in_process
availability = ready
enabled = true
network_allowed = false
```

The provider receives an injected `LoveLaboratoryInputResolver`. The initial
in-memory resolver is used by tests and local compositions. A later SQL resolver
can implement the same protocol without changing the provider.

## First real specialist

```text
specialist:love-concept-and-affect-analyst
```

Implemented capabilities:

- `love.evidence_extraction`;
- `love.concept_analysis`;
- `love.affect_mapping`;
- `analysis.local_synthesis`.

The initial backend is `stdlib_lexical_v1`. It is simple but not fake: it splits
the supplied text into sentences, creates digest-backed evidence references and
computes findings from the actual words in the request. Two different texts
produce different evidence and analysis references.

The backend does not claim OpenVINO use. The existing OpenVINO boundary is not
reimplemented; later task handlers may replace or enrich this backend through
the same provider/task contracts.

## Scheduler path

```text
Scheduler.emit()
→ PolicyEngine.decide()
→ PriorityQueue
→ Scheduler.run()
→ Dispatcher
→ NativeLoveLaboratoryVisitRequestHandler
→ NativeLoveLaboratoryProvider.execute()
```

The r10 binding only builds, registers and submits through this existing path.
It never starts or owns the Scheduler.

## Authority boundaries

- the study request remains authoritative;
- the task request must match the visit and its authorized contexts/evidence;
- the provider owns no persistence or vector index;
- no model or specialist may create follow-up tasks directly;
- the second specialist remains disabled until r11;
- global synthesis remains the later liaison step;
- no GitHub mutation or publication occurs.

## Closure status

The native provider, immutable Scheduler-owned registration, Dispatcher handler,
existing-Scheduler submit helper, first specialist backend, evidence extraction,
concept/affect analysis and optional local synthesis are implemented and tested.

The next unit is `0287-r7-r11`: enable the relational-dynamics specialist,
transport the first analysis through the v2 message/artifact contracts and
coordinate the second visit exclusively through the existing Scheduler.
