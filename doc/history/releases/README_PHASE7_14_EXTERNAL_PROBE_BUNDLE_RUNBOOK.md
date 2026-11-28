# Phase 7.14 — External Probe Bundle Runbook

Phase 7.14 adds an operator runbook for the local external probe bundle path.

The runbook documents the safe sequence:

```text
operator review report
read-only probe request
read-only probe result
CLI dry-run
CLI apply
local bundle validation
```

It does not add runtime behavior.
