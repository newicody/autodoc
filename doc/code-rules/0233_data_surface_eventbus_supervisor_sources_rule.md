# 0233 data-surface EventBus supervisor sources rule

Data-surface supervision must extend the existing passive bus supervisor module.

Allowed:

```text
EventBus-compatible GitHub artifact event -> PassiveSupervisorSink
EventBus-compatible SourceCandidate event -> PassiveSupervisorSink
EventBus-compatible SQL event -> PassiveSupervisorSink
EventBus-compatible Qdrant event -> PassiveSupervisorSink
EventBus-compatible rehydration event -> PassiveSupervisorSink
EventBus-compatible pushback event -> PassiveSupervisorSink
```

Forbidden:

```text
new EventBus
new supervisor runtime
GitHub API mutation
SourceCandidate promotion/rejection
SQL write/read by the supervisor
Qdrant query/upsert by the supervisor
rehydration execution by the supervisor
pushback execution by the supervisor
Scheduler.run()
proxy or SHM mutation
policy decision
events.jsonl as the normal runtime path
```

All helpers must remain stdlib-only and data-only.
