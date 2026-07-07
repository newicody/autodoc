# SUPERSEDED — do not apply

This generated patch was extracted but intentionally not applied.

Reason:

- It introduced a GitHub attachment fetch path before auditing the existing
  runtime bus / Scheduler / VisPy integration.
- The repository already has an existing event.bus/context.bus observation path.
- VisPy/browser views must read through the existing bus visualization adapter.
- Tools must not create a parallel VisPy notification path.
- Scheduler/policy/zone remain the authority.

Canonical next step:

- Replace this attempt with a runtime bus/scheduler integration audit patch.
- Reuse or extend existing surfaces instead of creating a parallel path:
  - src/runtime/bus_visualization_adapter.py
  - src/runtime/scheduler_route_adapter.py
  - src/runtime/scheduler_route_handler_minimal.py
  - src/runtime/scheduler_route_handshake.py
  - src/runtime/shm_runtime_schema.py

This directory is kept only as development history for human/AI review.
Git commits and tracked source files remain the canonical source of truth.
