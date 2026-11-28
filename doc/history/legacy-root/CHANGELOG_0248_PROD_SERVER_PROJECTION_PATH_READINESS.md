# Changelog 0248 - projection path readiness

## r1

Added production projection path readiness that composes PostgreSQL, OpenVINO,
and Qdrant readiness into a future Qdrant point shape.

The patch remains read-only and does not connect to PostgreSQL, run OpenVINO, or
call Qdrant.
