from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/github_research_love_openrc_scheduler_service_0287.py"
TOOL = ROOT / "tools/run_github_research_love_openrc_scheduler_0287.py"
OPENRC = ROOT / "templates/openrc/autodoc-github-research-scheduler"
CONF = ROOT / "templates/openrc/conf.d/autodoc-github-research-scheduler"
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_OPENRC_SCHEDULER_SERVICE_0287_R16_R57.md"
RULE = ROOT / "doc/code-rules/0287_r16_r57_openrc_scheduler_service_rule.md"


def test_r16_r57_locks_openrc_process_and_single_scheduler_boundaries() -> None:
    module = MODULE.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")
    openrc = OPENRC.read_text(encoding="utf-8")
    conf = CONF.read_text(encoding="utf-8")
    combined = (
        ARCHITECTURE.read_text(encoding="utf-8")
        + "\n"
        + RULE.read_text(encoding="utf-8")
    )

    for token in (
        "OpenRC possède le processus",
        "Scheduler canonique unique",
        "PostgreSQL",
        "Qdrant",
        "ControlFS",
        "/dev/shm",
        "stockage interne JSON",
        "file JSONL",
        "observation-only",
    ):
        assert token in combined

    assert "asyncio.create_task" in module
    assert "self.scheduler.shutdown()" in module
    assert "await scheduler_task" in module
    assert "SchedulerCanonicalCycleBound" in module
    assert "module:function" in tool
    assert "SIGTERM" in tool
    assert "need localmount postgresql-18 qdrant" in openrc
    assert "AUTODOC_ENV_FILE" in conf
    assert "AUTODOC_POSTGRES_PASSWORD=" not in conf

    for forbidden in (
        "threading.Thread",
        "RuntimeManager",
        "LaboratoryManager",
        "jsonlines",
    ):
        assert forbidden not in module
