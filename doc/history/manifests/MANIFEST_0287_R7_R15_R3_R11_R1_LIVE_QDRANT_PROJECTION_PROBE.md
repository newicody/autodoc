# Manifest 0287-r7-r15-r3-r11-r1

## Modified

- `src/inference/qdrant_client_projection_executor.py`

## Added

- `src/context/love_live_qdrant_projection_probe_0287.py`
- `tools/probe_love_live_qdrant_projection_0287.py`
- `tests/context/test_love_live_qdrant_projection_probe_0287_r7_r15_r3_r11_r1.py`
- `tests/context/test_qdrant_client_reference_point_readback_0287_r7_r15_r3_r11_r1.py`
- `tests/rules/test_love_live_qdrant_projection_probe_0287_r7_r15_r3_r11_r1_rule.py`
- `PHASE0287_R7_R15_R3_R11_R1_LIVE_QDRANT_PROJECTION_PROBE_REPORT.md`
- `doc/CHANGELOG_0287_R7_R15_R3_R11_R1_LIVE_QDRANT_PROJECTION_PROBE.md`
- `doc/architecture/LIVE_QDRANT_PROJECTION_PROBE_0287_R7_R15_R3_R11_R1.md`
- `doc/architecture/LIVE_QDRANT_PROJECTION_PROBE_0287_R7_R15_R3_R11_R1.dot`
- `doc/manifests/MANIFEST_0287_R7_R15_R3_R11_R1_LIVE_QDRANT_PROJECTION_PROBE.md`

## Locked boundaries

- preview performs SQL reads only;
- execution requires environment, operator approval and exact plan digest;
- one object and one Qdrant point only;
- readback uses `with_vectors=False`;
- no collection, alias or delete operation;
- SQL remains durable authority;
- no Scheduler or parallel orchestrator.
