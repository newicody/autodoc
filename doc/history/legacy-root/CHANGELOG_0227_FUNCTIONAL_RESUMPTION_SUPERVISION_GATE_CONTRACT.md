# Changelog — 0227 functional resumption supervision gate contract

## Added

- Documented the acceptance gate required before resuming functional supervisor/EventBus implementation.
- Locked the requirement to audit and reuse existing EventBus, Scheduler, passive-supervisor, proxy, SHM, and policy surfaces before adding runtime code.
- Added explicit no-go rules for parallel bridges, mandatory `events.jsonl`, status-file-first paths, new buses, Scheduler wrappers, and hidden policy/proxy/SHM control.
- Added a DOT diagram for the functional resumption gate and its forbidden bypasses.
- Added a rule test covering the gate vocabulary and forbidden paths.

## Not changed

- No runtime code.
- No new EventBus.
- No Scheduler changes.
- No `Scheduler.run()` usage.
- No proxy/SHM/policy control.
- No SQL/Qdrant/GitHub mutation.
- No VisPy dependency.
