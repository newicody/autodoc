# Changelog — 0286-r5

- added an immutable combined Issue/ProjectV2 publication plan;
- added deterministic append-only comment rendering and idempotency marker;
- added create, replay and collision detection for existing comments;
- added exact set/replay plans for the nine r4 ProjectV2 fields;
- bound comment and field intents under one SHA-256 `plan_digest`;
- blocked all ProjectV2 writes when the marked comment collides;
- preserved SQL, Scheduler, Qdrant and GitHub authority boundaries;
- added context tests, architecture rules, report, architecture note, DOT graph
  and manifest;
- reviewed `INSTALLATION.md`; no deployable Projects change was required.

```text
code_rule_review: done
live_path_status: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
```

Next: `0286-r6-specialist-capability-growth-projects-operator-authorized-adapter`.
