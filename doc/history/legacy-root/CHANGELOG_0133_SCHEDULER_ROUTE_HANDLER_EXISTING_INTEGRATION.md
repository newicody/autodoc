# Changelog 0133 — Scheduler route handler existing integration

Changed existing handler surface instead of creating a new runtime/worker module.

Added to `src/runtime/scheduler_route_handler_minimal.py`:

- `SchedulerRouteHandlerReadbackResult`
- `ExistingRouteHandlerIntegrationDecision`
- `read_scheduler_route_handler_result_frames()`
- `handle_scheduler_route_command_with_readback()`
- `describe_existing_scheduler_route_handler_integration()`

Added rule/doc/test coverage for the anti-duplication decision.
