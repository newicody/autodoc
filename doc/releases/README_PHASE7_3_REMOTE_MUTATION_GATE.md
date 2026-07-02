# Phase 7.3 — Remote Mutation Gate

Phase 7.3 adds a local gate for future remote write eligibility.

The gate is closed by default:

```text
remote_mutation_enabled: false
operator_confirmed: false
allowed_repositories: empty
```

A future adapter must not apply remote changes unless this gate passes.

This phase does not contact any external service.
