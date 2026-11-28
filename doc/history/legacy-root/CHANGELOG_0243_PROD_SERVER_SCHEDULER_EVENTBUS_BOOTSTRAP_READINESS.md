# Changelog 0243 - Scheduler/EventBus bootstrap readiness

## r1

Added a readiness check for the Scheduler/EventBus bootstrap pair using the
validated production server INI and 0242 component registry.

The check verifies command/observation roles and dependency-order presence while
keeping factory references as data only.
