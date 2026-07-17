# 0285-r6 — Scheduler-approved specialist revision selection

Apply this patch after `0285-r5-specialist-capability-growth-durable-history`.

It extends the existing Scheduler/Dispatcher/Handler event path with an immutable
selection command, policy, result and handler. Selection requires the latest durable
SQL-authoritative, operator-approved specialist revision. It validates capability,
contract envelope, target laboratory and execution boundary, but does not dispatch or
execute a laboratory visit.

The patch modifies `src/contracts/event.py` only to append two event members after all
existing members, preserving earlier `auto()` values.

`templates/github/projects-repository/INSTALLATION.md` was reviewed and is not
modified because this phase changes no Projects deployment surface.
