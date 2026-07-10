# Code rule 0265 - Closed ResultFrame EventBus observation

Required:

```text
Closed ResultFrame EventBus observation
EventBus observation only
Events are facts, not commands
event.request is None
does not execute SQL, OpenVINO, or Qdrant
```

Forbidden:

```text
command event
reply/request channel
runtime execution
SQL write
OpenVINO execution
Qdrant write or recall
new RuntimeManager
Scheduler.run modification
```

0266 may attach PassiveSupervisor observation.
