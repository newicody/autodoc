from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/portable_specialist_contract_0284.py"
ARCHITECTURE = ROOT / "doc/architecture/PORTABLE_SPECIALIST_CONTRACT_0284.md"
GRAPH = ROOT / "doc/architecture/PORTABLE_SPECIALIST_CONTRACT_0284.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0284_R2_PORTABLE_SPECIALIST_CONTRACT.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0284_R2_PORTABLE_SPECIALIST_CONTRACT.md"
REPORT = ROOT / "PHASE0284_R2_PORTABLE_SPECIALIST_CONTRACT_REPORT.md"


def test_contract_is_immutable_effect_free_and_first_class() -> None:
    source = MODULE.read_text(encoding="utf-8")
    for required in (
        "class PortableSpecialistDescriptor",
        "class SpecialistCapabilityContract",
        "class SpecialistExecutionProfile",
        "class SpecialistLaboratoryBinding",
        "@dataclass(frozen=True, slots=True)",
        "validate_portable_specialist_visit_contract",
        '"specialist_ref"',
        '"laboratory_ref"',
        '"accepted_input_contract_refs"',
        '"produced_output_contract_refs"',
    ):
        assert required in source
    for forbidden in (
        "Scheduler(",
        "EventBus(",
        "ControlProxy(",
        "qdrant_client",
        "sqlite3",
        "import openvino",
        "Core(",
        "subprocess.",
        "urlopen(",
        "requests.",
        "httpx.",
        "github.com",
        "from context.laboratory_framework_contract_0273",
        "from context.scheduler_deliberation_route_contract",
    ):
        assert forbidden not in source


def test_contract_cannot_attach_a_provider_or_runtime() -> None:
    source = MODULE.read_text(encoding="utf-8")
    assert "provider_bound: bool = field(default=False, init=False)" in source
    assert "runtime_attached: bool = field(default=False, init=False)" in source
    assert '"provider_instantiated": False' in source
    assert '"scheduler_remains_orchestrator": True' in source
    assert '"eventbus_observation_only": True' in source
    assert '"sql_remains_authority": True' in source
    assert '"qdrant_projection_recall_only": True' in source


def test_phase_documents_lock_the_portable_specialist_boundary() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, GRAPH, MANIFEST, CHANGELOG, REPORT)
    )
    for required in (
        "portable_specialist_contract_added: true",
        "stable_specialist_identity: true",
        "existing_laboratory_contract_reused: true",
        "existing_specialist_route_frames_reused: true",
        "provider_attached: false",
        "runtime_attached: false",
        "scheduler_modified: false",
        "new_scheduler_added: false",
        "new_laboratory_manager_added: false",
        "eventbus_observation_only: true",
        "sql_remains_authority: true",
        "qdrant_projection_recall_only: true",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_report_uses_code_rule_fields_and_names_r3() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: n/a",
        "live_path_uses_real_backend: n/a",
        "context_contract_version: missipy.specialist.descriptor.v1",
        "context_contract_changed: true",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "sql_write_performed: false",
        "llm_or_openvino_added: false",
        "0284-r3-specialist-laboratory-message-contract",
    ):
        assert required in report
