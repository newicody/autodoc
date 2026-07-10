# Code rule 0268 - OpenRC launcher minimal readiness

Required:

```text
OpenRC launcher minimal readiness
OpenRC/system/admin starts external services
Scheduler owns Autodoc runtime objects
readiness/rendering only
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
runtime execution
new RuntimeManager
Scheduler.run modification
```

0269 may run the prototype production smoke.
