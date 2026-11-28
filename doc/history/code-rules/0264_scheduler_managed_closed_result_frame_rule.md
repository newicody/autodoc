# Code rule 0264 - Scheduler-managed closed ResultFrame

Required:

```text
Scheduler-managed closed ResultFrame
0260 -> 0261 -> 0262 -> 0263
does not execute SQL, OpenVINO, or Qdrant
SQL remains the durable authority
Qdrant remains projection/recall only
```

Forbidden:

```text
runtime execution
SQL write
OpenVINO execution
Qdrant write or recall
new RuntimeManager
Scheduler.run modification
PostgreSQL daemon start
OpenVINO service start
Qdrant daemon start
EventBus command path
```

0265 may add EventBus observation-only facts.
