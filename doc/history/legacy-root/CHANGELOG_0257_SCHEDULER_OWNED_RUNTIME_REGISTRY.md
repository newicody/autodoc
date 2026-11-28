# Changelog 0257 - Scheduler-owned runtime registry

## r1

Adds a Scheduler-owned runtime registry plan derived from the 0256 source map.

The registry references existing implementation surfaces for EventBus,
PassiveSupervisor, SQLContextStore, OpenVINO/E5, Qdrant, and GitHub artifacts.
It does not create a RuntimeManager, does not instantiate components, and does
not turn component smoke tools into the runtime API.
