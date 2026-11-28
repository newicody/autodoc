# GitHub real closed-loop closure matrix — 0281-r8

This test-only phase closes the already-running 0281-r7 verification matrix.

```text
0281-r2 assembly:
  advisory absent allowed/refused by explicit policy
  duplicate request/advisory/manifest rejected

0281-r7 dataset boundary:
  optional advisory absence accepted
  duplicate imported filename rejected
  SHA-256 mismatch rejected

0281-r6 publication plan:
  create -> replay -> collision
  GitHub mutation remains disabled
```

```text
runtime_source_modified: false
new_runtime_module_added: false
new_cli_added: false
scheduler_modified: false
network_added: false
github_api_added: false
github_mutation_performed: false
projects_repository_change_required: false
external_dependencies_added: false
```

The existing Scheduler remains the sole orchestrator. No laboratory manager,
parallel scheduler, queue, event bus, persistence adapter or publication
adapter is introduced.
