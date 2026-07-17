# 0285-r7 — Specialist capability growth observation projection

Apply this patch after `0285-r6-scheduler-approved-specialist-revision-selection`.

It reuses the existing EventBus publication boundary and the event type reserved by
r6 to publish four immutable, correlated observation facts: proposed revision,
operator approval, durable SQL history entry and Scheduler selection. It also derives
an observation-only PassiveSupervisor read model from that event.

The patch performs no laboratory dispatch or execution, no SQL or Qdrant write, no
GitHub mutation and creates no Scheduler, EventBus, supervisor, registry or parallel
orchestrator.

`templates/github/projects-repository/INSTALLATION.md` was reviewed and is not
modified because this phase changes no Projects deployment surface.
