# Code rule 0270 — Operational documentation consolidation

Required:

```text
update existing canonical documentation instead of creating a competing index
show 0260 -> 0261 -> 0262 -> 0263 -> 0264 -> 0265 -> 0266 -> 0267 -> 0268 -> 0269
SQL remains durable authority
Qdrant remains projection / recall with payload.sql_ref
OpenVINO/E5 remains explicit
EventBus remains observation only
PassiveSupervisor remains observation only
GitHub remains a review/workflow surface
remote mutation remains forbidden without a separate explicit gate
OpenRC/OS/admin owns external service processes
next runtime work begins with an existing-surface audit
no non-stdlib dependency
```

Forbidden:

```text
new runtime module
new RuntimeManager or Orchestrator
new service manager
new handler or adapter
service start or rc-service call
GitHub API call or remote mutation
SQL write, Qdrant call or OpenVINO execution
Scheduler.run modification
removal of historical phase documentation
```

`Scheduler.run is not modified` by 0270. This phase is documentation and graph
consolidation only.
