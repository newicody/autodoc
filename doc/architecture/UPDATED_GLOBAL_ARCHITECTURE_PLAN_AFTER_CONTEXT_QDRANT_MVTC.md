# Updated Global Architecture Plan After Context, Qdrant and MVTC Reframing

```text
contract: missipy.updated_global_architecture_plan.v1
```

## Core correction

Use:

```text
no event-to-action shortcut
```

Do not use:

```text
no event-to-command shortcut
```

Events may feed the existing intent system. Events may produce proposals. Only validated typed commands may reach the Scheduler.

## Runtime split

```text
Observation:
Component / Worker / Expert / Scheduler / System Adapter
→ ComponentEvent
→ EventBus
→ VolumeFilter
→ Recorder
→ Journal
→ Cell Lens

Intent:
EventBus
→ existing intent system
→ security / locks / policy / budgets
→ controlled action or CommandProposal
→ Scheduler

External command:
CLI / D-Bus command / future GitHub / operator tool
→ Command Intake Gateway
→ token check
→ zone check
→ scope check
→ typed command validation
→ Scheduler
```

The Command Intake Gateway guards external input. It is not a scheduler.

## Context runtime

```text
ProjectRequest / InferenceRequest
→ Scheduler
→ TaskContext v1
→ WorkerPlan
→ Workers / Experts / Model workers / MVTC
→ ContextPatchProposal
→ ContextGate
→ TaskContext vN+1
```

The context is mobile but versioned. Workers and experts propose patches. They do not mutate the context directly.

## MVTC corrected role

MVTC is a context variation and testing engine.

```text
TaskContext
→ MVTC
→ ContextVariants
→ test / compare / reduce
→ ContextPatchProposal
→ ContextGate
```

MVTC may also emit RiskSignal, BudgetAdvice, ZonePolicySuggestion, SearchAxisScore, and ExpertNeed. Risk policy is only one output of MVTC. The lowercase rule phrase is: risk policy is only one output of MVTC.

MVTC must not command the Scheduler directly.

## Qdrant role

Qdrant is vector memory and similarity search. Qdrant stores projections.

It is not source of truth, EventBus, Scheduler, intent system, MVTC, or context authority.

First instance layout:

```text
qdrant_core
  stable knowledge, docs, contracts, code, norms, validated projects

qdrant_work
  live task context, temporary hypotheses, MVTC variants, intermediate results

qdrant_lab
  geometry vectors, math vectors, experimental embeddings, expert prototypes
```

Use multiple instances for lifecycle/load/experiment isolation, not one instance per worker.

## Vector-oriented direction

Use specialized vector spaces when justified:

```text
semantic_vector
material_vector
geometry_vector
safety_vector
manufacturing_vector
risk_vector
history_vector
```

The project may become more vector-oriented, but should not become mathematical everywhere.

## Language models

Language models are workers or experts. They may summarize, extract constraints, classify context, produce expert findings, propose ContextPatchProposal, or help generate code.

They must not own context, command Scheduler directly, bypass zones/tokens, or replace the existing intent system.

## Worker metrics

Workers are components. Lifecycle events are kept. Scoring increments become summaries by default:

```text
many increments
→ local accumulator
→ WorkerMetricSummary
→ EventBus
→ Recorder
```

## Security

Runtime tokens and zones constrain boundaries.

Minimal scopes:

```text
emit.events
submit.scheduler.commands
admin.scheduler
read.zone
admin.zone
```

Zone rights are initially file-based:

```text
/etc/autodoc/security/admins/<admin_id>/zones/<zone_name>
```

## Non-goals

```text
no scheduler clone
no model-driven scheduler decision path
no journal-as-bus
no browser command channel
no Qdrant-as-context-authority
no MVTC direct action
no TPM per event
no systemd dependency in core
```
