from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0255_reuse_audit_is_read_only_and_searches_existing_surfaces() -> None:
    source = (ROOT / "tools/audit_scheduler_owned_runtime_reuse_0255.py").read_text(
        encoding="utf-8"
    )

    assert "reuse_existing_surfaces_before_new_runtime_code" in source
    assert "Scheduler" in source
    assert "EventBus" in source
    assert "DbApiSqlContextStore" in source
    assert "OpenVINO" in source
    assert "Qdrant" in source
    assert "ProjectPushFrame" in source
    assert "importlib" not in source
    assert "Scheduler.run(" not in source
    assert ".upsert(" not in source


def test_0255_docs_lock_no_reinventing_wheel_boundary() -> None:
    doc = (ROOT / "doc/architecture/SCHEDULER_OWNED_RUNTIME_REUSE_AUDIT_0255.md").read_text(
        encoding="utf-8"
    )

    assert "reuse existing surfaces before new runtime code" in doc
    assert "Scheduler owns runtime components" in doc
    assert "no CLI per component" in doc
    assert "audit first, adapt second" in doc
