# Code rule addendum — 0137 local vector-indexing test readiness

Before adding a local vector-indexing runner, run tools/plan_local_vector_indexing_smoke.py and document the result.

The smoke path must reuse existing RouteProxyRuntime, Scheduler route handler, OpenVINO/E5 membrane, Qdrant projection adapter, and SQLContextStore.

Do not create a new scheduler, runtime, OpenVINO adapter, Qdrant adapter, or orchestrator for the smoke test.

Allowed 0137 scope:

```text
read-only inventory tool
documentation
tests
rules
```

Forbidden 0137 scope:

```text
new runtime daemon
new adapter
new scheduler
new orchestrator
backend process launch
network client
```
