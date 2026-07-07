# 0172 runtime activity graph / VisPy contract rule

0172 locks DOT as an architectural/support representation for runtime activity
views, not as a runtime authority.

Rules:

- DOT may describe activity, titles, navigation, zoom, modes, scores, failures,
  successes, and population/life/death states.
- DOT must not command runtime components.
- DOT must not replace Scheduler/policy/zone authority.
- DOT must not replace event.bus/context.bus facts.
- VisPy/browser views must read from the existing bus visualization adapter or
  an extension of that adapter.
- Do not create a parallel bus for graph display.
- Do not write directly to VisPy from GitHub artifact/dataset tools.
- Reuse `runtime.shm_runtime_schema` for event.bus/context.bus message schemas.
- Reuse existing scheduler route adapter/handler/handshake surfaces before
  adding any new runtime module.
- `doc/docs/architecture/00_global.dot` must be patched only from exact local
  state after audit; stale global graph patches are forbidden.

Required state vocabulary for activity graph views:

`planned`, `born`, `discovered`, `fetched`, `synced`, `validated`, `queued`,
`running`, `succeeded`, `failed`, `blocked`, `dead`, `superseded`, `retrying`,
`stale`.


Additional lock:

- `doc/docs/architecture/00_global.dot` must be patched only from exact local state after audit; stale global graph patches are forbidden.
