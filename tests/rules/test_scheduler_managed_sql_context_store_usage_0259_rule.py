from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0259_sql_usage_keeps_scheduler_and_external_service_boundaries() -> None:
    source = (ROOT / "src/context/scheduler_managed_sql_context_store_usage_0259.py").read_text(
        encoding="utf-8"
    )

    assert "Scheduler owns the Autodoc runtime object usage" in source
    assert "does not start PostgreSQL" in source
    assert "No RuntimeManager is created" in source
    assert "No Scheduler.run modification is made" in source
    assert "sql.context.write" in source
    assert "sql.context.rehydrate" in source
    assert "DbApiSqlContextStore" in source
    assert "subprocess.run" not in source
    assert "Scheduler.run(" not in source
    assert "RuntimeManager(" not in source
    assert "requests." not in source


def test_0259_docs_lock_sql_usage_axis() -> None:
    doc = (ROOT / "doc/architecture/SCHEDULER_MANAGED_SQL_CONTEXT_STORE_USAGE_0259.md").read_text(
        encoding="utf-8"
    )

    assert "Scheduler-managed SQLContextStore usage" in doc
    assert "Scheduler does not start PostgreSQL" in doc
    assert "Scheduler uses an existing SQLContextStore object" in doc
    assert "sql.context.write resolves to sql_context_store" in doc
    assert "execute requires policy_decision_id" in doc
    assert "no CLI per component" in doc
    assert "0260 can bind the real DbApiSqlContextStore constructor" in doc
