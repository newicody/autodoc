# Phase 7.5 — GitHub Export Bundle

Phase 7.5 creates a local GitHub export bundle for operator inspection.

The bundle contains:

```text
manifest.json
external_projection_contract.json
github_projection_payload.json
remote_mutation_gate.json
github_adapter_dry_run.json
```

The bundle is local-only. It does not contact GitHub and it does not perform
remote mutation.
