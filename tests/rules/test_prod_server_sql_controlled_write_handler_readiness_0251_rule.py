from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0251_sql_handler_readiness_does_not_execute_or_dispatch() -> None:
    source = (ROOT / "src/context/prod_server_sql_controlled_write_handler_readiness_0251.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "readiness_only" in source
    assert "connects_postgresql" in source
    assert "executes_sql" in source
    assert "writes_postgresql" in source
    assert "creates_eventbus" in source
    assert "publishes_events" in source
    assert "calls_scheduler_run" in source
    assert "dispatches_handler" in source
    assert "psycopg" not in lowered
    assert "subprocess.run" not in source
    assert "scheduler.run(" not in lowered
    assert ".publish(" not in lowered
    assert ".execute(" not in lowered
    assert ".upsert(" not in lowered


def test_0251_docs_lock_sql_handler_boundary() -> None:
    doc = (ROOT / "doc/architecture/PROD_SERVER_SQL_CONTROLLED_WRITE_HANDLER_READINESS_0251.md").read_text(
        encoding="utf-8"
    )

    assert "SQL controlled write handler readiness" in doc
    assert "No SQL is executed" in doc
    assert "Scheduler remains command authority" in doc
    assert "EventBus remains observation only" in doc
    assert "0252" in doc
