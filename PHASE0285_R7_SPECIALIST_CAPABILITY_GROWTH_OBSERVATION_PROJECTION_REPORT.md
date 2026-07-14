# Phase 0285-r7 — specialist capability growth observation projection

Status: implemented and targeted tests green.

## Goal

Project the approved and durably recorded specialist revision selected by 0285-r6
onto the existing EventBus, then derive a PassiveSupervisor read model. The path is
strictly observation-only.

## Reuse decision

Reused unchanged:

- the r6 `SchedulerApprovedSpecialistRevisionSelectionResult`;
- `EventType.SPECIALIST_REVISION_SELECTION_RESULT`, reserved by r6;
- the existing immutable `Event` contract;
- the existing EventBus `publish(Event)` boundary;
- the established PassiveSupervisor read-model pattern;
- the 0284 EventBus → Cell Lens bridge, which can already identify
  `specialist_ref`, `laboratory_ref`, `sql_ref` and lifecycle metadata.

No new Scheduler, EventBus, supervisor, registry or laboratory manager is created.

## Facts projected

1. evidence-backed proposal and portable revision;
2. authoritative operator approval;
3. SQL-authoritative durable history entry;
4. Scheduler-owned route selection without laboratory dispatch.

All four facts preserve the same specialist, revision, proposal, decision, history,
SQL and selection references.

## Authority boundaries

- Scheduler remains the only orchestration authority.
- SQL remains the durable authority.
- Qdrant remains projection/recall only.
- EventBus remains observation only.
- PassiveSupervisor remains observation only.
- GitHub Projects remains a workflow surface.
- r7 performs no laboratory dispatch or execution.

## Validation

- context and architecture tests: 14 passed;
- `compileall`: green;
- `git diff --check`: green;
- isolated `git apply --check`: green.

## Reviews

code_rule_review: completed

code_rule_update_required: false

Reason: existing rules already cover immutable messages, explicit authority,
observation-only EventBus/PassiveSupervisor and reuse of existing kernel surfaces.

projects_installation_review: completed

projects_installation_update_required: false

Reason: r7 adds no Projects workflow, form, field, secret, variable, Action or copy
procedure. `templates/github/projects-repository/INSTALLATION.md` was reviewed and
remains unchanged.

## Next

`0285-r8-specialist-capability-growth-closed-loop-smoke`
