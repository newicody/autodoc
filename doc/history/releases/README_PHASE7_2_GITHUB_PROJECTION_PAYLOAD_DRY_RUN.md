# Phase 7.2 — GitHub Projection Payload Dry-Run

Phase 7.2 adapts the target-neutral external projection contract into a
GitHub-shaped dry-run payload.

The payload is local only:

```text
dry_run: true
remote_mutation: false
```

This phase does not contact GitHub. It only serializes the operations that a
future adapter may later validate and gate.
