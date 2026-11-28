# 0123-r2 — Specialist Liaison Synthesis

0123-r2 replaces the rejected GitHub publication review direction. The system must not expose a DOT/GitHub review as the main output of specialist work. The work of specialists is linked, normalized, and synthesized locally first.

Required lock phrases:

- SpecialistLiaisonSynthesis unifies specialist work before any final publication
- Specialist path observations are bus-ready facts, not commands
- VisPy can represent specialist paths from bus observations later
- No GitHub/DOT publication review in 0123-r2
- End-user synthesis hides specialist provenance by default
- Specialists may request context influence, review, or validation without posting to GitHub directly
- SQLContextStore is durable context authority
- Qdrant is vector projection and retrieval, not context authority
- OpenVINO produces embeddings behind adapter
- LLM is specialist producer, not context authority

## Corrected flow

```text
specialist outputs of many natures
-> SpecialistOutputFragment[]
-> SpecialistLiaisonSynthesis
-> local end-user synthesis
-> optional FinalSynthesisPacket
-> future GitHub/local adapter only at the end
```

Specialist outputs may be thermal analysis, material analysis, validation notes, audit notes, context-delta proposals, or review requests. The end user should not need to reason about which specialist produced which detail unless a debugging or audit view explicitly asks for it.

## Bus and visualization boundary

Specialists can communicate the paths they took by producing bus-ready observations. These are facts. They are not scheduler commands and they are not policy decisions.

A later VisPy representation can consume these observations and show the work path. 0123-r2 does not create a watcher, subscribe to a bus, or render a live graph.

## Context influence

A specialist can influence the context by returning typed refs such as `ctx-result:*`, `ctx:*`, or `sql:*`. Those refs remain local context material until the liaison/synthesis stage decides how to present them. They do not go straight to GitHub.

Validation can also come from different provenance, including video or external artifacts, but this layer abstracts that source as `artifact:*` refs so the end-user synthesis is not polluted by backend provenance.

## Non-goals

0123-r2 does not add:

- a GitHub client;
- a GitHub publication review module;
- a DOT file for GitHub review;
- a live EventBus subscription;
- a watcher or service;
- Scheduler, Dispatcher, Queue, PolicyEngine, EventBus, or RouteRuntimeManager changes.
