# Code rule — 0234 all-surfaces passive supervisor smoke

The all-surfaces smoke is a downstream-only verification surface.

It may instantiate canonical supervision events and feed them to the existing
PassiveSupervisorSink. It must not create a new EventBus, call Scheduler.run,
control proxies, mutate SHM, decide policy, call GitHub, write SQL, write or
query Qdrant, execute rehydration, execute pushback, or introduce non-stdlib
dependencies.

Snapshot and audit outputs remain optional inspection artifacts. They are not
the runtime backbone.
