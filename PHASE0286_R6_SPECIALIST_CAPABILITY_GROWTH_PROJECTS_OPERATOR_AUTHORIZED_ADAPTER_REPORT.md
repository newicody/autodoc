# Phase 0286-r6 report

Status: contract complete.

The r5 publication plan is now executable only through an explicitly supplied
existing GitHub boundary. Preview is the default. Remote mutation requires a
local `approve` decision, `execute=True`, and an exact confirmation of the
immutable `plan_digest`.

No HTTP client, Scheduler, registry, queue or durable store is introduced.
GitHub Projects remains a workflow projection; SQL remains authoritative.
