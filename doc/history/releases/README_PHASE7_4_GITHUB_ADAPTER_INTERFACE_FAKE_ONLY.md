# Phase 7.4 — GitHub Adapter Interface Fake-Only

Phase 7.4 introduces the GitHub projection adapter interface and a fake local
implementation.

The adapter surface is separated into:

```text
plan
dry_run
apply
```

The only implementation in this phase is fake-only. It records local apply
simulations only when the remote mutation gate passes.

No GitHub API is contacted.
