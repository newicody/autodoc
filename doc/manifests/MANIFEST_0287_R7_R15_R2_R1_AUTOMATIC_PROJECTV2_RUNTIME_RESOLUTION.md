# Manifest — 0287-r7-r15-r2-r1 automatic ProjectV2/runtime resolution

## Added files

- `src/context/love_actions_closed_loop_resolution_0287.py`
- `config/love_actions_closed_loop.example.ini`
- `tests/context/test_love_actions_closed_loop_resolution_0287_r7_r15_r2_r1.py`
- `tests/rules/test_love_actions_closed_loop_resolution_0287_r7_r15_r2_r1_rule.py`
- `PHASE0287_R7_R15_R2_R1_AUTOMATIC_PROJECTV2_RUNTIME_RESOLUTION_REPORT.md`
- `doc/architecture/AUTOMATIC_PROJECTV2_RUNTIME_RESOLUTION_0287_R7_R15_R2_R1.md`
- `doc/architecture/AUTOMATIC_PROJECTV2_RUNTIME_RESOLUTION_0287_R7_R15_R2_R1.dot`
- `doc/CHANGELOG_0287_R7_R15_R2_R1_AUTOMATIC_PROJECTV2_RUNTIME_RESOLUTION.md`
- `doc/manifests/MANIFEST_0287_R7_R15_R2_R1_AUTOMATIC_PROJECTV2_RUNTIME_RESOLUTION.md`

## Modified files

- `tools/run_love_actions_closed_loop_0287.py`
- `tools/publish_love_final_deliverable_0287.py`
- `tests/tools/test_run_love_actions_closed_loop_0287_r7_r15_r2.py`
- `templates/github/projects-repository/INSTALLATION.md`

## Invariants

- preview remains mandatory;
- no remote mutation is available in the imported-run command;
- ProjectV2 resolution is read-only and exact;
- the authoritative request remains the source-Issue authority;
- existing ProjectV2 configuration remains the project authority;
- the real runtime factory remains explicit and installation-owned;
- no dummy fallback, module scan, Scheduler, manager or backend is added;
- SQL, Qdrant and OpenVINO/E5 authority boundaries are unchanged;
- diagnostic overrides remain validated against remote readback;
- no external dependency, binary or generated SVG is added.

## Roadmap

- `0287-r7-r15-r3`: concrete installed factory, mandatory live preview,
  controlled publication, exact remote readback and replay proof;
- `0287-r7-r16`: recovery, installation and prototype closure.
