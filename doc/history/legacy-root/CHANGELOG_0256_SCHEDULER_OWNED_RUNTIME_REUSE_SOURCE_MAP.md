# Changelog 0256 - Scheduler-owned runtime reuse source map

## r1

Adds a filtered, read-only source map that narrows the broad 0255 reuse audit to
implementation paths under `src/`, `tools/`, and `tests/`.

The patch is aligned with 0254 and 0255: Scheduler owns runtime components,
existing surfaces must be reused first, and component-specific production CLIs
must not become the runtime API.
