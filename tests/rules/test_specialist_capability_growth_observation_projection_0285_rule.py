from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialist_capability_growth_observation_projection_0285.py"
REPORT = ROOT / "PHASE0285_R7_SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION_REPORT.md"
DOC = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION_0285.md"
DOT = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION_0285.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0285_R7_SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0285_R7_SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_r7_reuses_existing_observation_surfaces_without_new_authority() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "EventType.SPECIALIST_REVISION_SELECTION_RESULT" in text
    assert "class SpecialistCapabilityGrowthObservationEventBusPort(Protocol)" in text
    assert "async def publish(self, event: Event) -> None" in text
    assert "PassiveReadModel" in text
    assert "observation_only" in text
    assert "authoritative: bool = field(default=False, init=False)" in text
    for forbidden in (
        "from kernel.scheduler import",
        "import kernel.scheduler",
        "LaboratoryManager",
        "RuntimeManager",
        "QdrantClient",
        "openvino.runtime",
        "psycopg",
        "requests.",
        "gh api",
    ):
        assert forbidden not in text


def test_r7_contracts_are_immutable_and_stdlib_only_at_boundary() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert text.count("@dataclass(frozen=True, slots=True)") >= 5
    assert "MappingProxyType" in text
    assert "scheduler_dispatch_performed\": False" in text
    assert "laboratory_execution_performed\": False" in text
    assert "sql_write_performed\": False" in text
    assert "qdrant_write_performed\": False" in text
    assert "github_mutation_performed\": False" in text


def test_r7_systematic_delivery_files_exist_and_lock_next_phase() -> None:
    for path in (REPORT, DOC, DOT, MANIFEST, CHANGELOG):
        assert path.is_file(), path
    combined = "\n".join(path.read_text(encoding="utf-8") for path in (REPORT, DOC, MANIFEST))
    assert "Scheduler remains the only orchestration authority" in combined
    assert "SQL remains the durable authority" in combined
    assert "Qdrant remains projection/recall only" in combined
    assert "EventBus remains observation only" in combined
    assert "PassiveSupervisor remains observation only" in combined
    assert "0285-r8-specialist-capability-growth-closed-loop-smoke" in combined


def test_projects_installation_is_reviewed_without_brittle_version_freeze() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "Installation cumulative de `newicody/projects`" in text
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in text
    assert "--delete" in text
    report = REPORT.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "projects_installation_review: completed" in report
    assert "projects_installation_update_required: false" in report
    assert "INSTALLATION.md reviewed and unchanged" in manifest
