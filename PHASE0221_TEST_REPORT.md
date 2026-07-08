# Phase 0221 Test Report - Bus-Direct Passive Supervisor Sink

Prepared as an update to the 0220 passive bus supervisor surface.

## Local sandbox validation

The patch was validated on a skeleton repository containing patch 0220 and
0220-r1 already applied:

- `git apply --check`: OK
- `git apply`: OK
- `python -m compileall -q src tests tools`: OK
- `python -m pytest -q tests/context tests/tools tests/rules`: OK when pytest is available in the target repository; not available in this sandbox.
- Manual smoke CLI with `--event-json`: OK
- Manual smoke CLI with `--events-jsonl`: OK

## Boundary checked

- No Scheduler.run call.
- Scheduler documented as upstream orchestration authority.
- EventBus documented as the canonical transport.
- Passive supervisor is downstream-only.
- `events.jsonl` is optional audit/replay only.
- No non-stdlib dependency.

## Real repository requirement

Run through the patch queue in `/home/eric/projet/git/autodoc` after 0220-r1 is
applied and the full suite is green.
