# Native love laboratory and first specialist — 0287-r7-r10

## Runtime composition

```text
Scheduler-owned runtime registry
└── laboratory_provider_love_studies_local
    └── NativeLoveLaboratoryProvider
        ├── injected LoveLaboratoryInputResolver
        └── love-concept-and-affect specialist backend
```

## Visit path

```text
SpecialistTaskRequest + LoveStudyRequest
→ LaboratoryVisitRequest
→ existing Scheduler
→ existing Dispatcher
→ NativeLoveLaboratoryVisitRequestHandler
→ NativeLoveLaboratoryProvider
→ sentence evidence
→ LoveConceptAffectAnalysis or SpecialistTaskResult
→ LaboratoryVisitResult
→ Scheduler reply
```

## Implemented tasks

```text
love.evidence_extraction
love.concept_analysis
love.affect_mapping
analysis.local_synthesis
```

`analysis.local_synthesis` is explicit. The provider never creates a global
synthesis and does not enable the second specialist.

## Boundaries

```text
Scheduler       execution authority
provider        bounded specialist execution
resolver        input resolution only
SQL             not written in r10
Qdrant          not called in r10
OpenVINO        existing boundary preserved, not used by stdlib backend
EventBus        no command role
ControlProxy    unchanged
GitHub          unchanged
```
