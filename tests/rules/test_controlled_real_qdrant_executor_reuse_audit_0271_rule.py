from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "src/context/controlled_real_qdrant_executor_reuse_audit_0271.py"
TOOL = ROOT / "tools/audit_controlled_real_qdrant_executor_reuse_0271.py"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0271_CONTROLLED_REAL_QDRANT_EXECUTOR_REUSE_AUDIT_CHANGED_FILES.md"


def test_0271_is_a_passive_source_audit_only() -> None:
    combined = CORE.read_text(encoding="utf-8") + TOOL.read_text(encoding="utf-8")
    forbidden = (
        "import qdrant_client",
        "from qdrant_client",
        "urllib.request",
        "http.client",
        "import requests",
        "import httpx",
        "subprocess",
        "rc-service",
        "Scheduler.run" + "(",
    )
    for token in forbidden:
        assert token not in combined


def test_0271_reuses_existing_protocol_and_forbids_manager_growth() -> None:
    text = CORE.read_text(encoding="utf-8")
    assert "QdrantProjectionExecutor" in text
    assert "runtime_manager_created: bool = False" in text
    assert "existing_protocol_must_be_reused: bool = True" in text
    assert "sql_remains_authority: bool = True" in text
    assert "qdrant_remains_projection_recall_only: bool = True" in text


def test_0271_manifest_does_not_modify_scheduler_or_existing_runtime_modules() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    assert "src/kernel/scheduler.py" not in text
    assert "src/inference/qdrant_projection_adapter.py" not in text
    assert "scheduler_managed_embedding_qdrant_projection_usage_0262.py" not in text
    assert "scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263.py" not in text
