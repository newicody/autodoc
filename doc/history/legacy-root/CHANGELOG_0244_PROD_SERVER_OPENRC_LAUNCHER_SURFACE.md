# Changelog 0244 - OpenRC launcher surface

## r1

Added a validation-only OpenRC launcher surface for the production server.

The patch includes an example `openrc-run` service file and a validator that
checks configtest/start/stop/status shape, supervise-daemon usage, PostgreSQL and
Qdrant dependencies, and absence of embedded GitHub token values.
