# 0124 — Server-oriented deliberation cycle

0124 fixes the GitHub boundary and introduces the local server/specialist deliberation cycle.

Required lock phrases:

- GitHub artifact exchange only moves artifacts in and final artifacts out
- ServerOrientation drives specialist deliberation before publication
- Specialist preliminary opinions are recomposed into refined demands
- Specialist bus statistics feed passive supervision and VisPy, not GitHub
- Final GitHub publication happens only after local convergence
- Specialist proposals may be accepted as analysis signals without being validated as final solutions
- The server may ask for context influence, review, validation, or another specialist before production
- SQLContextStore is durable context authority
- Qdrant is vector projection and retrieval, not context authority
- OpenVINO produces embeddings behind adapter
- LLM is specialist producer, not context authority

## Correct flow

```text
GitHub artifact + Copilot orientation
-> local server fetch/import
-> ServerOrientation
-> SpecialistPreliminaryOpinion[]
-> RefinedSpecialistDemand[]
-> DeliberationRound[]
-> specialist production / liaison / synthesis
-> FinalArtifactEnvelope
-> later GitHub artifact exchange adapter
```

GitHub is not the place where the internal work happens. GitHub only exchanges artifacts and project status: one artifact enters, and a final artifact leaves after the local server has converged.

## Server orientation

The server reads the imported artifact and produces an orientation such as:

```text
Given the request, explore these axes, avoid these traps, ask these specialists, and produce this type of document.
```

That orientation is derived from local context, SQL authority, projections, and specialist boundaries. It is not a GitHub publication.

## Preliminary specialist opinions

Specialists answer individually before production starts. A preliminary opinion can be:

```text
possible / impossible / risky / better_alternative / needs_context / needs_specialist / analysis_signal
```

A specialist can ask for more context, another specialist, a validation artifact, a review, a different document type, or a context-delta proposal. The server recomposes these answers into a more precise demand.

## Bus statistics and visualization

Specialists can emit bus-ready observation refs about the path they used. These observations are facts. They are not commands and they are not posted to GitHub.

The statistics produced from those observations are for passive supervision, audit, replay, and future VisPy representation. They do not belong to GitHub Project by default.

## Publication boundary

A `FinalArtifactEnvelope` can be built only after local synthesis is marked final-publication-ready. Internal bus statistics, path traces, and specialist provenance remain local unless a later explicit adapter decides otherwise.

## Non-goals

0124 does not add:

- a GitHub client;
- HTTP, socket, or network calls;
- a live EventBus subscription;
- a watcher or service;
- a VisPy renderer;
- Scheduler, Dispatcher, Queue, PolicyEngine, EventBus, or RouteRuntimeManager changes.
