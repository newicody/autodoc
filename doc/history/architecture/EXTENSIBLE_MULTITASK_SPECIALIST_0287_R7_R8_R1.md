# Extensible multitask specialist architecture

## Purpose

A specialist is one portable identity with several versioned capabilities. It
can perform different task types without requiring one class per operation and
without owning a private scheduler.

## Composition

```text
PortableSpecialistDescriptor
  + SpecialistTaskType[]
  = ExtensibleMultitaskSpecialistDefinition

Scheduler-approved mission
  -> SpecialistTaskPlan
     -> SpecialistTaskRequest A (capability X)
     -> SpecialistTaskRequest B (capability Y)
     -> dependency edges
  -> concrete laboratory handler
  -> SpecialistTaskResult[]
  -> later evidence/memory/liaison synthesis
```

## Responsibilities

The specialist model owns:

- task-type declarations;
- accepted and produced contracts;
- capability matching;
- immutable task and result envelopes;
- follow-up proposals;
- validation of task-plan coherence.

The Scheduler owns:

- task authorization;
- dependency release;
- priority and parallelism decisions;
- retries, cancellation and timeout;
- requests for another specialist or laboratory;
- consequences of later context revisions.

The laboratory owns:

- the concrete execution environment;
- handler and model-session availability;
- resource enforcement;
- returning results to the Scheduler route.

## Execution backends

A task may reference an execution binding:

```text
python:deterministic
openvino:embedding.e5-small
openvino:genai.local
pytorch:training-laboratory       future development only
transformers:model-preparation    future adapter only
```

The binding is metadata, not an implementation. Existing OpenVINO runtimes are
reused. No model is loaded by the contract module.

## Deep analysis

The current deep-analysis contract is the first extension:

```text
DeepAnalysisRequest
  -> SpecialistTaskRequest(capability=analysis.deep)
  -> existing handler later
  -> DeepAnalysisContribution
  -> SpecialistTaskResult
  -> SpecialistOutputFragment
  -> SpecialistLiaisonSynthesis
```

Analysis, critique, comparison, validation, recommendation and local synthesis
can be added as task types. Global synthesis remains a later explicit mission by
default.

## Context and storage continuation

This phase deliberately does not assign semantic knowledge to ControlProxy.
Upcoming boundaries keep the separation:

```text
SQL          authority, identities, revisions, relations and provenance
ZFS          large durable content
OpenVINO     local embeddings and inference
Qdrant       reconstructible projections and reference recall
EventBus     observation and change facts
Scheduler    impact and execution decisions
ControlProxy fast authorized transport and route lifecycle
```
