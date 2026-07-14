# Phase 0285-r6 — Scheduler-approved specialist revision selection

Status: implemented and targeted tests green.

## Goal

Extend the existing Scheduler event path so it can select exactly one portable
specialist revision that is:

- already operator-approved by 0285-r4;
- already recorded by a durable SQL-authoritative 0285-r5 adapter;
- the latest entry of the correlated append-only history;
- compatible with the requested capability, contracts, laboratory and execution
  boundary.

The phase performs selection only. It does not dispatch or execute a laboratory
visit.

## Reuse decision

Reused unchanged:

- `PortableSpecialistDescriptor` and laboratory bindings from 0284-r2;
- `PortableSpecialistRevision` from 0285-r3;
- operator authorization from 0285-r4;
- SQL-addressed history result from 0285-r5;
- the existing immutable `Event`, central Scheduler, Dispatcher and Handler path.

No second Scheduler, registry, laboratory manager or orchestration loop was added.
The two new event enum members are appended after existing members so previously
assigned `auto()` values remain stable.

## Authority boundaries

- Scheduler remains the only orchestration authority.
- SQL remains the durable authority for approved specialist history.
- Qdrant remains projection/recall only.
- EventBus remains observation only.
- GitHub Projects remains a workflow surface.
- The r6 result has `scheduler_dispatch_performed=false` and
  `laboratory_execution_performed=false`.

## Validation

- new context tests: 22 passed;
- new rule tests: targeted green;
- cumulative 0285-r2 through r6 targeted suite: 101 passed;
- `compileall`: green;
- `git diff --check`: green;
- isolated `git apply --check`: green.

## Reviews

code_rule_review: completed

code_rule_update_required: false

Reason: the existing rules already require immutable contracts, explicit policy,
Scheduler centrality, effects at adapters, EventBus observation-only behavior and
reuse of the real runtime path. This phase conforms to those rules without changing
them.

projects_installation_review: completed

projects_installation_update_required: false

Reason: r6 adds no Projects workflow, form, field, secret, variable, Action or copy
procedure. The cumulative `INSTALLATION.md` remains at `0284-r9`, with Copilot
disabled by default and synchronization without `--delete`.

## Next

`0285-r7-specialist-capability-growth-observation-projection`
