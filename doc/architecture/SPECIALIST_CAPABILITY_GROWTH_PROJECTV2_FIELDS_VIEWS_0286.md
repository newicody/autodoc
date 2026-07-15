# Specialist capability-growth ProjectV2 fields and views — 0286-r4

## Decision

Reuse the existing versioned Projects configuration and reconciler. Do not add
a second ProjectV2 client or a specialist registry.

The nine fields mirror the immutable r2 projection exactly. Text fields carry
typed references and digests. Single-select fields carry stable machine values
so later publication and readback phases can compare exact values without
translation drift.

## Authority boundary

```text
local proposal/revision/operator gate
  -> SQL durable history
  -> Scheduler selection
  -> immutable r2 review projection
  -> r4 ProjectV2 field declaration
  -> later operator-authorized publication

GitHub Projects = review/workflow surface
SQL             = durable authority
Scheduler       = orchestration authority
Qdrant          = projection/recall only
```

The r4 configuration performs no mutation by itself. Installation uses the
existing preview, exact plan digest and two explicit environment locks.

## Next phase

`0286-r5-specialist-capability-growth-projects-publication-plan` composes the
Issue comment and ProjectV2 field values into one deterministic, non-executing
publication plan.
