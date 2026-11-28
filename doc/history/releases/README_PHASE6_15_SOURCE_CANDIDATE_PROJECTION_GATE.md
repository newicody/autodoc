# Phase 6.15 — SourceCandidate Projection Gate

Phase 6.15 adds a local validation gate for projection bundles.

The gate validates:

```text
manifest schema
preview schema
manifest/preview item count consistency
optional non-empty item requirement
optional audit-present requirement
```

It prepares a future handoff boundary without contacting any external system.
