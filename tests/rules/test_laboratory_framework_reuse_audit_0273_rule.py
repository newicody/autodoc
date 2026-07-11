from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/LABORATORY_FRAMEWORK_REUSE_AUDIT_0273.md"
GRAPH = ROOT / "doc/docs/architecture/runtime/273_r1_laboratory_framework_reuse_audit.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0273_R1_LABORATORY_REUSE_AUDIT_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0273_R1_LABORATORY_REUSE_AUDIT_TEST_REPORT.md"


def test_audit_reuses_existing_authorities_and_surfaces() -> None:
    text = ARCH.read_text(encoding="utf-8")
    for marker in (
        "specialist_kernel_boundary.py",
        "server_oriented_deliberation_cycle.py",
        "scheduler_deliberation_route_contract.py",
        "scheduler_owned_runtime_registry_0257.py",
        "scheduler_runtime_bootstrap_registry_attachment_0258.py",
        "SQL remains the durable authority",
        "Qdrant remains a reconstructible projection",
        "EventBus remains observation-only",
        "PassiveSupervisor",
        "VisPy",
    ):
        assert marker in text


def test_audit_rejects_parallel_laboratory_authorities() -> None:
    text = ARCH.read_text(encoding="utf-8")
    for marker in (
        "a new `LaboratoryManager`",
        "a laboratory-owned Scheduler loop",
        "a laboratory-owned SQL/Qdrant authority",
        "a new EventBus or visualization bus",
        "changing `Scheduler.run()`",
    ):
        assert marker in text


def test_audit_defines_minimal_missing_seam_and_future_refs() -> None:
    text = ARCH.read_text(encoding="utf-8")
    for marker in (
        "`LaboratoryDescriptor`",
        "`LaboratoryVisitRequest`",
        "`LaboratoryVisitResult`",
        "Provider membrane",
        "Registry capability binding",
        "`origin_laboratory_ref`",
        "`target_laboratory_ref`",
        "`conversation_ref`",
        "`return_route_ref`",
    ):
        assert marker in text


def test_fake_provider_is_not_claimed_as_real_backend() -> None:
    text = ARCH.read_text(encoding="utf-8")
    assert "The fake is a tracer bullet, not a real laboratory validation." in text
    assert "live_path_uses_real_backend: false" in text
    assert "only then integrate a GenAI or partner laboratory" in text


def test_graph_preserves_existing_authority_flow() -> None:
    graph = GRAPH.read_text(encoding="utf-8")
    for marker in (
        "Scheduler -> Registry",
        "Registry -> Handler",
        "Handler -> Provider",
        "Deliberation -> SQL",
        "Deliberation -> EventBus",
        "EventBus -> Supervisor",
        "Supervisor -> Visual",
        "Rejected: LaboratoryManager / LaboratoryBus / parallel Scheduler / parallel registry",
    ):
        assert marker in graph


def test_phase_is_documentation_only_and_stdlib_neutral() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for marker in (
        "live_path_status: n/a",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "network_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
    ):
        assert marker in report


def test_manifest_lists_no_runtime_or_tool_change() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "- `src/" not in manifest
    assert "- `tools/" not in manifest
    assert "tests/rules/test_laboratory_framework_reuse_audit_0273_rule.py" in manifest
