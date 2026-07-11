from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/laboratory_framework_contract_0273.py"
ARCH = ROOT / "doc/architecture/LABORATORY_FRAMEWORK_CONTRACT_0273.md"
GRAPH = ROOT / "doc/docs/architecture/runtime/273_r2_laboratory_framework_contract.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0273_R2_LABORATORY_FRAMEWORK_CONTRACT_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0273_R2_LABORATORY_FRAMEWORK_CONTRACT_TEST_REPORT.md"


def test_contract_uses_versioned_immutable_serializable_records() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        'LABORATORY_DESCRIPTOR_SCHEMA = "missipy.laboratory.descriptor.v1"',
        'LABORATORY_RESOURCE_BUDGET_SCHEMA = "missipy.laboratory.resource_budget.v1"',
        'LABORATORY_VISIT_REQUEST_SCHEMA = "missipy.laboratory.visit_request.v1"',
        'LABORATORY_VISIT_RESULT_SCHEMA = "missipy.laboratory.visit_result.v1"',
        "@dataclass(frozen=True, slots=True)",
        "def to_mapping(",
    ):
        assert marker in text


def test_contract_keeps_existing_scheduler_registry_boundary() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "context.scheduler_owned_runtime_registry_0257",
        "SchedulerOwnedRuntimeComponentRegistration",
        '"owner": self.owner',
        '"next_boundary": "Scheduler.emit()"',
        "ready_for_registry_attachment: bool = False",
        "provider_active: bool = False",
    ):
        assert marker in text


def test_contract_reserves_mediated_interlaboratory_refs() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "origin_laboratory_ref",
        "target_laboratory_ref",
        "conversation_ref",
        "parent_visit_ref",
        "return_route_ref",
        "cross-laboratory visit requires conversation_ref",
    ):
        assert marker in text


def test_contract_has_explicit_resource_bounds() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "max_duration_ms",
        "max_output_chars",
        "max_context_refs",
        "max_evidence_refs",
        "max_followup_requests",
        "max_specialist_messages",
        "max_external_calls",
        "allow_network",
    ):
        assert marker in text


def test_contract_does_not_import_runtime_or_external_backends() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "import openvino",
        "import qdrant",
        "import vispy",
        "import genai",
        "import requests",
        "import httpx",
        "from kernel.scheduler",
        "RouteRuntimeManager",
        "EventBus(",
        "Scheduler.run(",
    )
    for marker in forbidden:
        assert marker not in text


def test_documentation_keeps_provider_inactive_until_r3() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    graph = GRAPH.read_text(encoding="utf-8")
    for marker in (
        "0273-r3",
        "provider_active = false",
        "ready_for_registry_attachment = false",
        "fake provider",
        "GenAI",
        "Scheduler.run()",
        "EventBus",
        "VisPy",
    ):
        assert marker in architecture
    assert "ContractsR2 -> ExistingRegistry" in graph
    assert "ExistingRegistry -> ProviderR3" in graph


def test_manifest_and_report_keep_patch_clean() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    for marker in ("__pycache__", ".pyc", ".pyo", ".svg"):
        assert marker not in manifest
    for marker in (
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "provider_active: false",
        "network_added: false",
        "context_contract_version: missipy.laboratory.v1",
    ):
        assert marker in report
