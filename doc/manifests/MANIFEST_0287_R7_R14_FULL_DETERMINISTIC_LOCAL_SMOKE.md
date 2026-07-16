# Manifest — 0287-r7-r14 full deterministic local smoke

## Added files

- `src/context/love_full_deterministic_local_smoke_0287.py`
- `tests/context/test_love_full_deterministic_local_smoke_0287_r7_r14.py`
- `tests/rules/test_love_full_deterministic_local_smoke_0287_r7_r14_rule.py`
- `PHASE0287_R7_R14_FULL_DETERMINISTIC_LOCAL_SMOKE_REPORT.md`
- `doc/architecture/FULL_DETERMINISTIC_LOCAL_SMOKE_0287_R7_R14.md`
- `doc/architecture/FULL_DETERMINISTIC_LOCAL_SMOKE_0287_R7_R14.dot`
- `doc/CHANGELOG_0287_R7_R14_FULL_DETERMINISTIC_LOCAL_SMOKE.md`
- `doc/manifests/MANIFEST_0287_R7_R14_FULL_DETERMINISTIC_LOCAL_SMOKE.md`

## Runtime and authority declarations

- Scheduler reused; no Scheduler created and no run loop modified.
- Dispatcher registration surface reused.
- SQL authority exercised for analyses and synthesis revisions.
- Qdrant projection/recall exercised through injected local ports.
- OpenVINO/E5-384 query embedding contract reused.
- Two real specialist implementations exercised.
- Advisory remains hint-only; request remains authoritative.
- GitHub mutation not performed.
- ProjectV2 mutation not performed.
- Exact readback is simulated locally.
- No manager, queue, bus, registry or parallel orchestrator added.
- No dependency added.
- No SVG generated or versioned.

## Validation gates

- targeted compileall;
- targeted functional tests;
- targeted rule tests;
- `git apply --check`;
- Graphviz DOT parse;
- JSON metadata validation;
- archive integrity and absence of bytecode/binary patch hunks.

## Roadmap

The next unit is `0287-r7-r15 — real GitHub Actions closed-loop evidence`.
`0287-r7-r16` remains the recovery, installation and prototype closure step.
