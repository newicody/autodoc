# Code rule — 0222 Scheduler EventBus upstream contract

Any Scheduler supervision integration must preserve the following rule:

```text
Scheduler is the upstream orchestration authority.
EventBus is the canonical observation transport.
PassiveSupervisorSink is downstream-only.
```

A compliant patch may add observation events from existing Scheduler surfaces to
an existing EventBus.

A compliant patch must not introduce a new EventBus, a Scheduler replacement, a
parallel runtime loop, or a mandatory file-status path.

A compliant patch must not call, wrap, replace, or modify `Scheduler.run()` unless
a separate reviewed exception explicitly authorizes that change.

A compliant patch must not let the passive supervisor dispatch handlers, make
policy decisions, control proxies, write SHM, write SQL, write Qdrant, or mutate
GitHub.

Before adding runtime code, the patch must audit existing Scheduler and EventBus
modules and reuse or extend them whenever possible.
