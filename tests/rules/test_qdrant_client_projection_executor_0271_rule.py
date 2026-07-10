from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXECUTOR = ROOT / "src/inference/qdrant_client_projection_executor.py"
REQUIREMENT = ROOT / "config/requirements-qdrant-client-0271.txt"
RULE = ROOT / "doc/code-rules/0271_qdrant_client_projection_executor_rule.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0271_QDRANT_CLIENT_PROJECTION_EXECUTOR_CHANGED_FILES.md"


def test_0271_r2_reuses_existing_protocol_and_declares_dependency() -> None:
    source = EXECUTOR.read_text(encoding="utf-8")
    assert "from inference.qdrant_projection_adapter import" in source
    assert "class QdrantClientProjectionExecutor" in source
    assert 'import_module("qdrant_client")' in source
    assert REQUIREMENT.read_text(encoding="utf-8").strip().endswith("qdrant-client==1.18.0")


def test_0271_r2_keeps_service_and_shm_boundaries() -> None:
    source = EXECUTOR.read_text(encoding="utf-8")
    forbidden = (
        "subprocess",
        "rc-service",
        "openrc",
        "Scheduler.run(",
        "RuntimeManager",
        "Orchestrator",
        "shared_memory",
        "mmap(",
        "RouteProxy",
        "ControlProxy",
    )
    for phrase in forbidden:
        assert phrase not in source
    assert "starts_qdrant" in source
    assert '"touches_shm": False' in source


def test_0271_r2_requires_effect_gate_and_sql_ref_payload() -> None:
    source = EXECUTOR.read_text(encoding="utf-8")
    assert "QdrantClientEffectGate" in source
    assert 'payload["sql_ref"] = point.sql_context_ref' in source
    assert 'payload["autodoc_point_ref"] = point.point_id' in source
    assert '"missing_sql_ref"' in source


def test_0271_r2_manifest_is_narrow_and_scheduler_free() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "src/inference/qdrant_client_projection_executor.py" in manifest
    assert "config/requirements-qdrant-client-0271.txt" in manifest
    assert "src/scheduler" not in manifest.lower()
    assert "Scheduler.run" not in manifest
    assert "official qdrant-client SDK" in RULE.read_text(encoding="utf-8")
