from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "src/context/specialist_multitask_model_0287.py"
PORTABLE = ROOT / "src/context/portable_specialist_contract_0284.py"
MESSAGE_V2 = ROOT / "src/context/specialist_laboratory_message_v2_0287.py"
DEEP_ANALYSIS = ROOT / "src/context/specialist_deep_analysis_contract_0287.py"
CURRENT = ROOT / "doc/README_CURRENT.md"
REPORT = ROOT / "PHASE0287_R7_R8_R1_EXTENSIBLE_MULTITASK_SPECIALIST_REPORT.md"
ARCHITECTURE = (
    ROOT
    / "doc/architecture/EXTENSIBLE_MULTITASK_SPECIALIST_0287_R7_R8_R1.md"
)
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_multitask_public_schemas_are_explicit_and_versioned() -> None:
    source = MODEL.read_text(encoding="utf-8")
    for marker in (
        "missipy.specialist.task_type.v1",
        "missipy.specialist.task_execution_binding.v1",
        "missipy.specialist.task_request.v1",
        "missipy.specialist.task_dependency.v1",
        "missipy.specialist.task_plan.v1",
        "missipy.specialist.followup_task_proposal.v1",
        "missipy.specialist.task_result.v1",
        "missipy.specialist.multitask_definition.v1",
    ):
        assert marker in source


def test_existing_specialist_message_and_analysis_contracts_are_reused() -> None:
    model = MODEL.read_text(encoding="utf-8")
    portable = PORTABLE.read_text(encoding="utf-8")
    message = MESSAGE_V2.read_text(encoding="utf-8")
    analysis = DEEP_ANALYSIS.read_text(encoding="utf-8")

    assert "PortableSpecialistDescriptor" in model
    assert "SpecialistCapabilityContract" in model
    assert "SpecialistArtifactReference" in model
    assert "DeepAnalysisRequest" in model
    assert "DeepAnalysisContribution" in model
    assert "project_deep_analysis_request_to_task" in model
    assert "project_deep_analysis_contribution_to_task_result" in model
    assert "missipy.specialist.descriptor.v1" in portable
    assert "missipy.specialist.laboratory_message.v2" in message
    assert "missipy.specialist.deep_analysis_request.v1" in analysis


def test_scheduler_owns_plans_and_specialists_only_propose_followups() -> None:
    source = MODEL.read_text(encoding="utf-8")
    for marker in (
        "scheduler_owned",
        "scheduler_submission_required",
        "specialist_self_scheduling",
        "specialist_can_launch_followups",
        "scheduler_approval_required",
        "task_created",
        "followups_executed",
        "scheduler_command_emitted",
        "dependencies must be acyclic",
    ):
        assert marker in source


def test_openvino_is_reused_without_a_parallel_backend() -> None:
    source = MODEL.read_text(encoding="utf-8")
    assert "reuses_existing_openvino_backend" in source
    assert "backend_implementation_created" in source
    assert "openvino_reimplemented" in source
    forbidden = (
        "import openvino",
        "from openvino",
        "CompiledModel",
        "InferRequest",
        "class OpenVINOBackend",
        "class ModelPool",
    )
    for marker in forbidden:
        assert marker not in source


def test_contract_module_creates_no_parallel_runtime_or_storage_authority() -> None:
    source = MODEL.read_text(encoding="utf-8")
    forbidden = (
        "class LaboratoryManager",
        "class SpecialistManager",
        "class SpecialistRegistry",
        "Scheduler(",
        "import qdrant",
        "import psycopg",
        "subprocess.",
        "requests.",
        "urllib.request",
        "mmap.",
        "/dev/shm",
    )
    for marker in forbidden:
        assert marker not in source


def test_roadmap_separates_sql_qdrant_scheduler_and_controlproxy() -> None:
    current = CURRENT.read_text(encoding="utf-8")
    architecture = ARCHITECTURE.read_text(encoding="utf-8")
    for marker in (
        "0287-r7-r8-r1 — extensible multitask specialist model",
        "0287-r7-r8-r2",
        "0287-r7-r8-r3",
        "0287-r7-r8-r4",
        "0287-r7-r8-r5",
        "0287-r7-r8-r6",
        "ControlProxy transport of authorized notifications",
    ):
        assert marker in current
    for marker in (
        "SQL          authority",
        "Qdrant       reconstructible projections",
        "Scheduler    impact and execution decisions",
        "ControlProxy fast authorized transport",
    ):
        assert marker in architecture


def test_report_locks_code_rule_and_installation_boundaries() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for marker in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "code_rule_reason:",
        "live_path_status: n/a",
        "live_path_uses_real_backend: n/a",
        "context_contract_version: n/a",
        "context_contract_changed: false",
        "search_commands_bounded: n/a",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "installation_update_required: false",
    ):
        assert marker in report
    assert INSTALLATION.exists()
