# Phase 6.13 — SourceCandidate Projection Preview

Phase 6.13 adds a local projection preview generated from the operator report.

The preview is intended to make the future external project surface explicit before any external API is introduced.

## Scope

```text
operator_report payload
-> projection preview dataclass
-> projection_preview.json
```

## Out of scope

```text
external API
network
project tracker mutation
Qdrant
LLM/OpenVINO
Scheduler modification
```
