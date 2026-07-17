# Manifest 0287-r7-r15-r3-r10

## Modified

- `config/love_installed_runtime.example.ini`
- `src/context/love_manual_runtime_configuration_0287.py`
- `src/context/love_manual_runtime_readiness_0287.py`

## Added

- `src/context/love_qdrant_named_collection_control_0287.py`
- `src/inference/qdrant_client_named_collection_admin_0287.py`
- `tools/control_love_qdrant_named_collection_0287.py`
- `tests/context/test_love_qdrant_named_collection_control_0287_r7_r15_r3_r10.py`
- `tests/context/test_qdrant_client_named_collection_admin_0287_r7_r15_r3_r10.py`
- `tests/rules/test_love_qdrant_named_collection_control_0287_r7_r15_r3_r10_rule.py`
- `PHASE0287_R7_R15_R3_R10_QDRANT_NAMED_COLLECTION_CONTROL_REPORT.md`
- `doc/CHANGELOG_0287_R7_R15_R3_R10_QDRANT_NAMED_COLLECTION_CONTROL.md`
- `doc/architecture/QDRANT_NAMED_COLLECTION_CONTROL_0287_R7_R15_R3_R10.md`
- `doc/architecture/QDRANT_NAMED_COLLECTION_CONTROL_0287_R7_R15_R3_R10.dot`
- `doc/manifests/MANIFEST_0287_R7_R15_R3_R10_QDRANT_NAMED_COLLECTION_CONTROL.md`

## Locked boundaries

- existing Qdrant projection/query executor remains unchanged;
- new module is limited to collection lifecycle I/O;
- creation is digest-confirmed and operator-authorized;
- no delete operation;
- no alias mutation;
- no point write;
- SQL remains authoritative.
## r10-r1 correction

All r10 artifacts are staged together after the initial global-suite failure.
