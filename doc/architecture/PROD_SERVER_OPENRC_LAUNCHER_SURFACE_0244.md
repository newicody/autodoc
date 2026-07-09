# OpenRC launcher surface - 0244

## Intent

This patch defines and validates the production server OpenRC launcher surface.

It validates the shape of the service file that will later live at:

```text
/etc/init.d/autodoc
```

No service is installed or started in this phase.

## Required surface

The OpenRC launcher surface must expose:

```text
configtest/start/stop/status
```

`configtest` calls the Autodoc launcher with `--configtest`. `start` is handled
by OpenRC/supervise-daemon after `start_pre` validates configuration. `stop` and
`status` remain OpenRC service operations.

## Runtime boundary

```text
OpenRC -> launcher -> Scheduler
```

OpenRC owns process supervision. Scheduler remains runtime authority once the
launcher is running. EventBus remains observation path.

## Dependencies

The initial service declares:

```text
need postgresql qdrant
use net
after firewall
```

GitHub token values must not be embedded in the service file. The service can
inherit environment prepared by the host, but `GITHUB_TOKEN` remains an external
secret.

## Boundary

This phase validates a local example service file only. It does not call OpenRC,
install files under `/etc/init.d`, start the launcher, create Scheduler/EventBus,
start threads, call GitHub, write PostgreSQL, or write Qdrant.
