from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/scheduler_approved_specialist_revision_selection_0285.py"
EVENTS = ROOT / "src/contracts/event.py"
REPORT = ROOT / "PHASE0285_R6_SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_REPORT.md"
ARCHITECTURE = (
    ROOT
    / "doc/architecture/SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_0285.md"
)
GRAPH = (
    ROOT
    / "doc/architecture/SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_0285.dot"
)
CHANGELOG = (
    ROOT
    / "doc/CHANGELOG_0285_R6_SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/MANIFEST_0285_R6_SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION.md"
)
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_r6_systematic_deliverables_exist() -> None:
    for path in (
        SOURCE,
        REPORT,
        ARCHITECTURE,
        GRAPH,
        CHANGELOG,
        MANIFEST,
    ):
        assert path.is_file(), path


def test_event_types_extend_existing_enum_without_renumbering_old_members() -> None:
    text = EVENTS.read_text(encoding="utf-8")
    shutdown = text.index("SHUTDOWN = auto()")
    selection = text.index("SPECIALIST_REVISION_SELECTION = auto()")
    result = text.index("SPECIALIST_REVISION_SELECTION_RESULT = auto()")
    assert shutdown < selection < result


def test_r6_uses_existing_scheduler_dispatcher_handler_path() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    required = (
        "from contracts.event import Event, EventType",
        "class SchedulerApprovedSpecialistRevisionSelectionHandler",
        "async def handle(",
        "EventType.SPECIALIST_REVISION_SELECTION",
        "dispatcher.register(EventType.SPECIALIST_REVISION_SELECTION, handler)",
        "dest=\"scheduler\"",
        "requires_existing_scheduler",
    )
    for token in required:
        assert token in text


def test_r6_does_not_create_parallel_runtime_authority() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "class Scheduler(",
        "class LaboratoryManager",
        "class SpecialistRegistry",
        "from kernel.scheduler import Scheduler",
        "from kernel.registry import Registry",
        "import qdrant",
        "import openvino",
        "import sqlalchemy",
        "import psycopg",
        "github.com",
        "api.github.com",
    )
    for token in forbidden:
        assert token not in text
    for token in (
        '"new_scheduler_created": False',
        '"parallel_orchestrator_created": False',
        '"scheduler_dispatch_performed": False',
        '"laboratory_execution_performed": False',
        '"sql_write_performed": False',
        '"qdrant_write_performed": False',
        '"eventbus_observation_published": False',
        '"github_mutation_performed": False',
    ):
        assert token in text


def test_r6_requires_durable_latest_operator_approved_history() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    required = (
        "durable_write_performed",
        "snapshot.latest_entry.entry_ref",
        "snapshot.latest_entry.entry_digest",
        "revision_authorized",
        "expected_snapshot_digest_sha256",
        "descriptor.availability != \"ready\"",
        "entry.sql_ref",
    )
    for token in required:
        assert token in text


def test_r6_validates_capability_contract_laboratory_and_execution_boundary() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    required = (
        "descriptor.capabilities",
        "accepted_input_contract_refs",
        "produced_output_contract_refs",
        "descriptor.laboratory_bindings",
        "required_laboratory_capabilities",
        "preferred_execution_boundaries",
        "available_execution_boundaries",
    )
    for token in required:
        assert token in text


def test_r6_contracts_are_immutable_stdlib_first() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert text.count("@dataclass(frozen=True, slots=True)") >= 3
    assert "MappingProxyType" in text
    assert "requests" not in text
    assert "pydantic" not in text
    assert "numpy" not in text


def test_report_records_code_rule_and_projects_installation_reviews() -> None:
    report = REPORT.read_text(encoding="utf-8")
    required = (
        "code_rule_review: completed",
        "code_rule_update_required: false",
        "Scheduler remains the only orchestration authority",
        "projects_installation_review: completed",
        "projects_installation_update_required: false",
        "0285-r7-specialist-capability-growth-observation-projection",
    )
    for token in required:
        assert token in report


def test_projects_installation_safe_invariants_remain_current() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide :" in text
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in text
    assert "Ne pas utiliser `--delete`" in text
