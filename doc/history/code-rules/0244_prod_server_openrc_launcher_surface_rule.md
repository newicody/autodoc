# Code rule 0244 - OpenRC launcher surface

Patch 0244 may define and validate the OpenRC launcher surface only.

Required:

```text
configtest/start/stop/status surface
configtest calls launcher --configtest
OpenRC uses supervise-daemon
OpenRC needs postgresql and qdrant
Scheduler remains runtime authority
EventBus remains observation path
GITHUB_TOKEN is not embedded in service text
```

Forbidden in this phase:

```text
installing /etc/init.d files
calling rc-service/openrc commands
starting launcher
creating Scheduler/EventBus instances
starting threads
publishing EventBus events
calling GitHub API
executing PostgreSQL DDL/DML
creating/upserting Qdrant collections or points
adding non-stdlib dependencies
```
