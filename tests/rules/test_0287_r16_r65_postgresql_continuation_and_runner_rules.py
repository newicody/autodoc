from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "src/context/github_research_love_postgresql_continuation_store_0287.py"
RUNNER = ROOT / "src/context/github_research_love_transactional_step_runner_0287.py"
CONFIG = ROOT / "config/github_research_love_externally_managed_durable_ports.example.env"


def test_factories_are_installed_and_execution_provider_stays_fail_closed() -> None:
    text = CONFIG.read_text(encoding="utf-8")
    assert "POSTGRESQL_CONTINUATION_STORE_FACTORY=\"context." in text
    assert "TRANSACTIONAL_STEP_RUNNER_FACTORY=\"context." in text
    assert "EXTERNALLY_MANAGED_EXECUTION_COMPONENT_FACTORY=\"\"" in text


def test_continuation_uses_normalized_sql_without_json_storage() -> None:
    text = STORE.read_text(encoding="utf-8").lower()
    assert "scheduler_task_graph_members" in text
    assert "scheduler_task_graph_promotion_transactions" in text
    assert "json.dumps" not in text
    assert "open(\"" not in text
    assert ".jsonl" not in text
    assert "pickle" not in text


def test_runner_reuses_canonical_services_and_transactions() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "SchedulerTaskLaunchPreparationService" in text
    assert "SchedulerHandlerInstanceLifecycleService" in text
    assert "SchedulerHandlerExecutionService" in text
    assert "commit_outcome" in text
    assert "return outcome" in text


def test_no_parallel_orchestration_or_backend_is_created() -> None:
    combined = STORE.read_text(encoding="utf-8") + RUNNER.read_text(encoding="utf-8")
    forbidden = (
        "Scheduler(",
        "Dispatcher(",
        "EventBus(",
        "psycopg.connect",
        "sqlite3.connect",
        "threading.Thread",
        "multiprocessing.Process",
    )
    for token in forbidden:
        assert token not in combined
