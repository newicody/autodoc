from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "src/context/github_research_love_externally_managed_postgresql_execution_core_0287.py"
COMPOSITION = ROOT / "src/context/github_research_love_externally_managed_durable_component_composition_0287.py"
CONFIG = ROOT / "config/github_research_love_externally_managed_durable_ports.example.env"
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_POSTGRESQL_EXECUTION_CORE_0287_R16_R64.md"
RULE = ROOT / "doc/code-rules/0287_r16_r64_postgresql_execution_core_rule.md"
REPORT = ROOT / "PHASE0287_R16_R64_TEST_REPORT.md"


def test_r16_r64_documents_authority_and_process_boundaries() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, RULE, REPORT)
    )
    for marker in (
        "Scheduler canonique",
        "PostgreSQL",
        "Qdrant",
        "OpenVINO E5",
        "384",
        "OpenRC",
        "stockage métier JSON",
        "file JSONL",
        "échoue fermé",
    ):
        assert marker in combined


def test_r16_r64_core_reuses_shared_sql_transactions() -> None:
    source = CORE.read_text(encoding="utf-8")
    for marker in (
        "adapter_port.build_adapter",
        'required_connection_methods=("cursor", "commit", "rollback")',
        "foundation.task_launch_transaction",
        "foundation.handler_execution_transaction",
        '("load_snapshot", "commit_promotion")',
        '("commit_launch",)',
        '("commit_outcome",)',
        '("run_ready_task",)',
    ):
        assert marker in source
    for forbidden in (
        "open_love_postgresql_authority",
        "Scheduler(",
        "Dispatcher(",
        "EventBus(",
        "json.dumps",
        ".jsonl",
        "subprocess",
        "threading",
    ):
        assert forbidden not in source


def test_r16_r64_composition_rejects_execution_object_replacement() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")
    for marker in (
        "build_github_research_love_postgresql_execution_core",
        "execution_core.adapter_port is not postgresql.adapter_port",
        "provided.continuation_store is not execution_core.continuation_store",
        "provided.step_runner_builder is not execution_core.step_runner_builder",
        "execution_core.task_launch_transaction is not",
        "execution_core.handler_execution_transaction is not",
    ):
        assert marker in source


def test_r16_r64_configuration_exposes_three_fail_closed_factories() -> None:
    text = CONFIG.read_text(encoding="utf-8")
    for marker in (
        "AUTODOC_GITHUB_RESEARCH_POSTGRESQL_CONTINUATION_STORE_FACTORY",
        "AUTODOC_GITHUB_RESEARCH_TRANSACTIONAL_STEP_RUNNER_FACTORY",
        "AUTODOC_GITHUB_RESEARCH_EXTERNALLY_MANAGED_EXECUTION_COMPONENT_FACTORY",
    ):
        assert marker in text
