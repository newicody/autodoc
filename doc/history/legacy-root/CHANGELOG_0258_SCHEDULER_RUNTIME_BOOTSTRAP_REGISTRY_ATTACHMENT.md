# Changelog 0258 - Scheduler runtime bootstrap registry attachment

## r1

Adds a Scheduler-owned runtime bootstrap registry attachment helper.

The helper attaches the validated 0257 registry metadata to an existing
Scheduler object without creating a RuntimeManager, without changing
Scheduler.run, and without instantiating or starting components.
