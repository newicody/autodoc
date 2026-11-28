# Code rule 0268 - OpenRC launcher minimal readiness

Required:

```text
OpenRC launcher minimal readiness
OpenRC/system/admin starts external services
Scheduler owns Autodoc runtime objects
readiness/rendering only
validate outputs 0264, 0265, 0266 and 0267
validate phase-0260 SQLite presence by metadata only
SQLite is not opened, queried or written
does not install, enable, or start services
```

Forbidden:

```text
rc-service call
rc-update call
service installation
service start
service enable
PostgreSQL daemon start
OpenVINO service start
Qdrant daemon start
OpenVINO execution
SQL write
Qdrant call
GitHub call
runtime execution
new RuntimeManager
Scheduler.run modification
```

0269 may run the prototype production smoke.
