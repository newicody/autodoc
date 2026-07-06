# 0134-r1 — OpenVINO doc phrase fix

Small rule-test phrase fix for 0134.

This patch only removes inline backticks around exact contractual phrases that `tests/rules/test_openvino_existing_embedding_path_0134_rule.py` expects verbatim.

It does not change runtime logic, Scheduler, OpenVINO, Qdrant, RouteProxy, or adapters.

Apply on top of the already-applied but failing `0134-extend_existing_openvino_embedding_path` working tree.
