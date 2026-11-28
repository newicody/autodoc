# Specialist message v2 and deep analysis

## Contract flow

```text
CorrelatedResearchWorkPackage
  -> DeepAnalysisRequest
  -> SpecialistLaboratoryMessageV2(kind=demand)
  -> Scheduler-owned future visit
  -> DeepAnalysisContribution
  -> SpecialistLaboratoryMessageV2(kind=analysis)
  -> completion | error
  -> output-fragment projection
  -> later SpecialistLiaisonSynthesis
```

## Versioning

The v1 contract remains the historical reader. The v2 contract is a companion
module because its public meaning changes:

- a conversation may span several visits and specialists;
- messages carry correlation and idempotency identities;
- payloads and artifacts are digest-backed;
- completion and error are explicit terminal kinds;
- cross-visit continuation is first-class.

No v1 field is reinterpreted.

## Specialist responsibility

The default specialist contribution is `domain_analysis`. A specialist can also
produce critique, validation, comparison, recommendation or a local synthesis
when the mission requests it. `global_synthesis` is never inferred from an
analysis response.

## Orchestration boundary

The contracts only describe exchange. A specialist can request context or
another specialist, but the existing Scheduler remains responsible for every
new visit. No direct specialist invocation or laboratory-owned Scheduler is
introduced.
