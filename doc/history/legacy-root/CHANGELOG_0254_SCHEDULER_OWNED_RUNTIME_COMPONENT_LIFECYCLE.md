# Changelog 0254 - Scheduler-owned runtime component lifecycle

## r2

Pivots the production sequence from component readiness tooling toward
Scheduler-owned runtime objects.

The patch states that OpenRC supervises the process, the launcher is
bootstrap-only, and the Scheduler owns runtime components and lifecycle.

It also explicitly closes the wrong direction of one production CLI per
component as the runtime API.
