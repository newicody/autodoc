from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/inference/qdrant_sql_authority_scope.py"
TOOL = ROOT / "tools/check_qdrant_sql_authority_scope_0271.py"
DOC = ROOT / "doc/architecture/QDRANT_SQL_AUTHORITY_SCOPE_STRICT_GRPC_0271.md"
RULE = ROOT / "doc/code-rules/0271_qdrant_sql_authority_scope_strict_grpc_rule.md"


def test_0271_r4_reuses_existing_executor_protocol() -> None:
    text = MODULE.read_text(encoding="utf-8")
    assert "QdrantProjectionExecutor" in text
    assert "class SqlAuthorityScopedQdrantExecutor" in text
    assert "RuntimeManager" not in text
    assert "Orchestrator" not in text


def test_0271_r4_has_no_network_or_service_control() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in (MODULE, TOOL, DOC, RULE)
    )
    for forbidden in (
        "subprocess",
        "rc-service",
        "socket.",
        "urllib.request",
        "requests.",
        "QdrantClient(",
        "sqlite3.connect",
        "Scheduler.run(",
    ):
        assert forbidden not in combined


def test_0271_r4_preserves_authority_and_shm_boundaries() -> None:
    combined = DOC.read_text(encoding="utf-8") + RULE.read_text(encoding="utf-8")
    for phrase in (
        "SQL remains the durable authority",
        "payload.sql_authority_ref",
        "REST administration",
        "gRPC data operations",
        "SHM remains unchanged",
    ):
        assert phrase in combined


def test_0271_r4_tool_is_readiness_only() -> None:
    text = TOOL.read_text(encoding="utf-8")
    assert '"network_used": False' in text
    assert '"qdrant_called": False' in text
    assert '"touches_shm": False' in text
    assert '"starts_qdrant": False' in text
