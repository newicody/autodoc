# Phase 7.1 — External Projection Contract v1

Phase 7.1 adds a target-neutral external projection contract.

The contract is built from the local handoff dry-run bundle:

```text
handoff_manifest.json
projection_preview.json
projection_gate_report.json
```

and produces a generic payload describing what may be projected outside the
local SourceCandidate chain.

This phase is intentionally not GitHub-specific. GitHub projection payloads come
later and must adapt this generic contract instead of leaking GitHub concepts
into the local core.
