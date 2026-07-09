from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0260_binding_reuses_existing_db_api_store_without_external_service_lifecycle() -> None:
    source = (ROOT / "src/context/scheduler_managed_db_api_sql_context_store_binding_0260.py").read_text(
        encoding="utf-8"
    )

    assert "replaces the 0259 demo store" in source
    assert "existing DbApiSqlContextStore" in source
    assert "Scheduler does not start PostgreSQL" in source
    assert "does not create a new SQL store" in source
    assert "sql.context.write" in source
    assert "RuntimeManager(" not in source
    assert "Scheduler.run(" not in source
    assert "subprocess.run" not in source
    assert "requests." not in source


def test_0260_docs_lock_binding_axis() -> None:
    doc = (ROOT / "doc/architecture/SCHEDULER_MANAGED_DB_API_SQL_CONTEXT_STORE_BINDING_0260.md").read_text(
        encoding="utf-8"
    )

    assert "Scheduler-managed DbApiSqlContextStore binding" in doc
    assert "replaces the 0259 demo store" in doc
    assert "Scheduler does not start PostgreSQL" in doc
    assert "does not create a new SQL store" in doc
    assert "uses existing DbApiSqlContextStore" in doc
    assert "0261 can project the resulting sql_ref toward OpenVINO" in doc
