# Manifest 0287-r7-r15-r3-r9

## Modified

- `src/inference/qdrant_client_projection_executor.py`

## Added

- `src/context/love_qdrant_hybrid_query_adapter_0287.py`
- `tests/context/test_love_qdrant_hybrid_query_adapter_0287_r7_r15_r3_r9.py`
- `tests/rules/test_love_qdrant_hybrid_query_adapter_0287_r7_r15_r3_r9_rule.py`
- `PHASE0287_R7_R15_R3_R9_QDRANT_NAMED_HYBRID_QUERY_ADAPTER_REPORT.md`
- `doc/CHANGELOG_0287_R7_R15_R3_R9_QDRANT_NAMED_HYBRID_QUERY_ADAPTER.md`
- `doc/architecture/QDRANT_NAMED_HYBRID_QUERY_ADAPTER_0287_R7_R15_R3_R9.md`
- `doc/architecture/QDRANT_NAMED_HYBRID_QUERY_ADAPTER_0287_R7_R15_R3_R9.dot`
- `doc/manifests/MANIFEST_0287_R7_R15_R3_R9_QDRANT_NAMED_HYBRID_QUERY_ADAPTER.md`

## Locked boundaries

- existing qdrant-client executor reused;
- named dense and sparse search only;
- search gate retained;
- no Qdrant write;
- no collection creation;
- reference-only hits;
- SQL remains durable authority;
- no Scheduler, OpenVINO or SQL-store construction.
