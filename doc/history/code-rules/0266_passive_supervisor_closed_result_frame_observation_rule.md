# Code rule 0266 - PassiveSupervisor closed ResultFrame observation

Required:

```text
PassiveSupervisor closed ResultFrame observation
PassiveSupervisor observes only
EventBus facts remain facts, not commands
does not execute SQL, OpenVINO, or Qdrant
does not publish events
```

Forbidden:

```text
command path
EventBus publish
live bus subscription
runtime execution
SQL write
OpenVINO execution
Qdrant write or recall
new RuntimeManager
Scheduler.run modification
```

0267 may prepare GitHub scan-once handoff.
