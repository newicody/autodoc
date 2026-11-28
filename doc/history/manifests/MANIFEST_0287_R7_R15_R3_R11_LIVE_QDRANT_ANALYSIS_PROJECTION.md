# Manifest 0287-r7-r15-r3-r11

## Modified

- `src/inference/qdrant_client_projection_executor.py`

## Added

- `src/context/love_qdrant_live_analysis_projection_0287.py`
- `tests/context/test_qdrant_client_named_hybrid_projection_0287_r7_r15_r3_r11.py`
- `tests/context/test_love_qdrant_live_analysis_projection_0287_r7_r15_r3_r11.py`
- `tests/rules/test_love_qdrant_live_analysis_projection_0287_r7_r15_r3_r11_rule.py`
- phase report, changelog, architecture Markdown/DOT and this manifest.

## Boundaries

- SQL remains durable authority;
- Qdrant payload is reference-only;
- exact existing sparse query algorithm reused;
- existing qdrant-client executor extended, not replaced;
- one point per call, explicit write gate;
- no collection or alias mutation;
- no Scheduler or event-loop construction.
