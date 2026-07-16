# Manifest — 0287-r7-r15-r1 final deliverable remote publication adapter

## Added files

- `src/context/love_final_deliverable_remote_publication_0287.py`
- `tools/publish_love_final_deliverable_0287.py`
- `tests/context/test_love_final_deliverable_remote_publication_0287_r7_r15_r1.py`
- `tests/tools/test_publish_love_final_deliverable_0287_r7_r15_r1.py`
- `tests/rules/test_love_final_deliverable_remote_publication_0287_r7_r15_r1_rule.py`
- `PHASE0287_R7_R15_R1_FINAL_DELIVERABLE_REMOTE_PUBLICATION_ADAPTER_REPORT.md`
- `doc/architecture/FINAL_DELIVERABLE_REMOTE_PUBLICATION_ADAPTER_0287_R7_R15_R1.md`
- `doc/architecture/FINAL_DELIVERABLE_REMOTE_PUBLICATION_ADAPTER_0287_R7_R15_R1.dot`
- `doc/CHANGELOG_0287_R7_R15_R1_FINAL_DELIVERABLE_REMOTE_PUBLICATION_ADAPTER.md`
- `doc/manifests/MANIFEST_0287_R7_R15_R1_FINAL_DELIVERABLE_REMOTE_PUBLICATION_ADAPTER.md`

## Runtime and authority declarations

- The immutable r13 plan is reused and never recalculated.
- The exact r13 readback verifier is reused.
- Preview is the default.
- Remote execution requires operator approval, exact digest confirmation and
  all three mutation locks.
- Issue and ProjectV2 reads occur before mutation.
- Issue mutation precedes ProjectV2 mutation.
- Partial execution is explicit and recoverable by replay.
- Scheduler, laboratories, specialists, SQL, Qdrant and OpenVINO are untouched.
- No manager, orchestrator, queue, registry or dependency is added.
- No SVG is generated or versioned.

## Validation gates

- targeted compilation;
- domain functional tests;
- GitHub CLI adapter tests with mocked subprocess transport;
- rule tests;
- `git apply --check`;
- Graphviz DOT parse;
- JSON metadata validation;
- archive integrity and binary/bytecode exclusion.

## Roadmap

- `0287-r7-r15-r2`: imported real Actions run to approved local composition and
  publication execution bridge;
- `0287-r7-r15-r3`: actual Issue plus ProjectV2 closed-loop evidence and replay;
- `0287-r7-r16`: recovery, installation and prototype closure.
