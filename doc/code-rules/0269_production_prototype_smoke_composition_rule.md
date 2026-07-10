# Code rule 0269 - Production prototype smoke composition

Required:

```text
0260 -> 0261 -> 0262 -> 0263 -> 0264 -> 0265 -> 0266 -> 0267 -> 0268
reuse existing phase tools
immutable Command / Policy / Step / Result contracts
process effects remain in the CLI adapter
execute requires policy_decision_id
current execute path requires explicit demo_qdrant
in-memory EventBus publication requires explicit demo_eventbus
OpenVINO remains explicit
SQL remains the durable authority
Qdrant remains projection / recall with payload.sql_ref
EventBus remains observation only
PassiveSupervisor remains observation only
GitHub remote mutation remains forbidden
OpenRC/OS/admin owns external service processes
final report requires sql_ref, embedding_ref, handoff_ref, readiness_ref
final report locks observation-only, no-mutation, SQLite, and no-service-start checks
no non-stdlib dependency
```

Forbidden:

```text
new RuntimeManager
new service manager
reimplementation of phases 0260-0268
implicit backend selection
implicit demo backend
rc-service or rc-update calls
PostgreSQL, Qdrant, or OpenVINO daemon start
GitHub API call or remote mutation
EventBus command path
PassiveSupervisor command path
Scheduler.run modification
```

`Scheduler.run is not modified` by 0269. The new CLI is justified because it is
the requested one-shot operator surface; the existing P1 smoke targets the
older 0145/0148/0151 path and is not a compatible subcommand host.
