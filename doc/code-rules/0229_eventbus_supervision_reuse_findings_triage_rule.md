# Code rule 0229 — EventBus supervision reuse findings triage

The 0229 triage is a read-only gate over the 0228 reuse audit report.

It must not call Scheduler.run.

It must not create a new EventBus.

It must not turn events.jsonl into the live path.

It must not control RouteProxy or ControlProxy.

It must not mutate SHM, SQL, Qdrant, GitHub, or policy state.

It may classify evidence from doc, tests, patch, phase reports, and `.var` outputs as non-runtime trace evidence.

It must mark findings in `src/` and `tools/` as requiring runtime review before the functional EventBus -> PassiveSupervisorSink implementation resumes.
