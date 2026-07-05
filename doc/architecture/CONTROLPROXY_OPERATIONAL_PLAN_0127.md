# ControlProxy operational plan — 0127

0127 adds a registry contract for Qdrant collection roles. It does not add a new service, watcher, daemon, or runtime client.

The operational direction remains:

```text
Scheduler -> command orchestration
/dev/shm routes -> multitask data-plane interface
EventBus -> observation/statistics/paths
SQL -> durable authority
E5/OpenVINO -> embedding only behind adapter
Qdrant -> projection and recall only
GitHub -> artifact exchange only
```

The registry will let a later adapter ensure the local Qdrant collections exist without making Qdrant a source of truth.
