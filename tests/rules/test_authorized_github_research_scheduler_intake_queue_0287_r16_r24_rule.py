from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/authorized_route_request_queue.py"
TOOL = ROOT / "tools/queue_authorized_github_research_scheduler_intake_0287.py"
ARCH = ROOT / "doc/architecture/GITHUB_RESEARCH_AUTHORIZED_INTAKE_LOCAL_QUEUE_0287.md"
RULE = ROOT / "doc/code-rules/0287_r16_r24_authorized_intake_local_queue_rule.md"
README = ROOT / "templates/github/projects-repository/README_INSTALLATION.md"


def test_r16_r24_reuses_existing_queue_without_runtime_execution() -> None:
    source = MODULE.read_text(encoding="utf-8")
    for token in [
        "append_authorized_github_research_scheduler_intake",
        "SchedulerRouteRequest.from_mapping",
        "scheduler.route_requests.jsonl",
        "exactly one GitHub research Scheduler intake result is required",
        "request_id collision with a different queued payload",
        "os.fsync",
        'dispatcher_used=False',
        'eventbus_used=False',
        'scheduler_started=False',
    ]:
        assert token in source

    for forbidden in [
        "from kernel.scheduler import Scheduler",
        "from kernel.dispatcher import Dispatcher",
        "from kernel.event_bus import EventBus",
        "dispatch_authorized_research_through_existing_scheduler(",
        "handle_scheduler_route_request(",
    ]:
        assert forbidden not in source


def test_r16_r24_cli_is_local_handoff_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "--input",
        "--runtime-root",
        "--policy-decision-id",
        "--repository",
        "--run-id",
        "append_authorized_github_research_scheduler_intake",
    ]:
        assert token in source
    for forbidden in [
        "import requests",
        "from requests",
        "urllib",
        "asyncio",
        "Scheduler(",
        "Dispatcher(",
    ]:
        assert forbidden not in source


def test_r16_r24_docs_lock_canonical_scheduler_boundary() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    for token in [
        "un seul Scheduler local canonique",
        "Dispatcher du noyau reste un routeur mécanique interne",
        "scheduler.route_requests.jsonl",
        "EventBus reste une surface d’observation",
        "Le consommateur serveur fera l’objet de l’unité suivante",
    ]:
        assert token in architecture
    for token in [
        "Ne jamais démarrer un Scheduler tool-bounded",
        "Ne pas appeler le Dispatcher",
        "Exiger `repository`, `run_id` et `policy_decision_id`",
        "Rejouer sans dupliquer un `request_id` identique",
    ]:
        assert token in rule
    assert "Remise locale au Scheduler canonique — r16-r24" in readme
