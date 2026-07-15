# Changelog — 0287-r7-r8-r1

## Added

- generic versioned specialist task type, request, dependency, plan, follow-up
  proposal and result contracts;
- immutable multitask definition over the existing portable descriptor;
- typed execution-backend binding that reuses existing OpenVINO surfaces;
- deterministic task, plan and idempotency reference helpers;
- bridges from the existing deep-analysis request/contribution contracts;
- acyclic dependency validation and pure ready-task calculation;
- context, rule, architecture, report and manifest evidence.

## Preserved

- portable specialist identity and capability contracts;
- message v1 and v2 schemas;
- deep-analysis public schemas and semantics;
- Scheduler as the only orchestration authority;
- SQL as durable authority and Qdrant as projection/recall;
- existing OpenVINO implementation;
- `INSTALLATION.md` and all deployment surfaces.
