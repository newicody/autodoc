# Specialist capability-growth request-form audit progression rule fix

The 0286 reuse audit is intentionally progressive. Its result changes when a
new phase marker appears in the repository. A rule attached to an earlier phase
must therefore prove a monotonic invariant rather than freeze the repository at
the exact next patch that was current when the rule was introduced.

The corrected invariant is:

```text
r2 completed
AND (
    r3 is next
    OR r3 is completed
)
```

This remains valid while r4, r5, r6, r7, and r8 are added. The dedicated tests
of each newer phase remain responsible for checking their own immediate next
recommendation.

Authority boundaries are unchanged: Scheduler is the only orchestrator, SQL is
the durable authority, Qdrant is projection/recall only, EventBus is
observation only, and GitHub Projects remains a workflow/review surface.

`templates/github/projects-repository/INSTALLATION.md` was reviewed. No update
is required because this fix changes no deployed Projects asset.
