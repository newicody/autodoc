# Phase 0287 R7 R15 R2 R2 R3 — Python 3.14 dynamic tool import compatibility fix

## Status

Closed as a narrow test-infrastructure compatibility correction.

## Failure reproduced

The full suite passed all rule tests, then failed twelve tests while dynamically
loading `tools/run_love_actions_closed_loop_0287.py`.  The helper created a
module with `module_from_spec()` and executed it directly, but did not register
that module in `sys.modules` before `exec_module()`.

On Python 3.14, the dataclass decorator resolves postponed string annotations
through the defining module.  Because the helper had not installed that module,
`sys.modules.get(cls.__module__)` returned `None`.

## Correction

The test helper now follows the standard programmatic-import sequence:

1. create the module from its spec;
2. save any previous entry using the same synthetic name;
3. register the new module in `sys.modules`;
4. execute the module;
5. restore or remove the entry only when execution fails.

The production CLI, runtime contracts, Scheduler lifecycle, artifact selection,
ProjectV2 resolution and publication preview are unchanged.

## Boundary

This patch fixes the invalid test loader instead of weakening the production
module by removing annotations or adding self-registration side effects.
