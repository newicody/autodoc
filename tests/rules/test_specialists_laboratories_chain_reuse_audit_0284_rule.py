from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/context/"
    "specialists_laboratories_chain_reuse_audit_0284.py"
)
TOOL = (
    ROOT
    / "tools/"
    "run_specialists_laboratories_chain_reuse_audit_0284.py"
)
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "SPECIALISTS_LABORATORIES_CHAIN_REUSE_AUDIT_0284.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0284_R1_SPECIALISTS_LABORATORIES_CHAIN_REUSE_AUDIT.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0284_R1_SPECIALISTS_LABORATORIES_CHAIN_REUSE_AUDIT.md"
)
REPORT = (
    ROOT
    / "PHASE0284_R1_SPECIALISTS_LABORATORIES_CHAIN_REUSE_AUDIT_REPORT.md"
)


def test_audit_is_source_only_and_reuses_existing_chain() -> None:
    source = MODULE.read_text(encoding="utf-8")

    for required in (
        "laboratory_framework_contract_0273.py",
        "deterministic_fake_laboratory_provider_0273.py",
        "scheduler_laboratory_visit_binding_0274.py",
        "scheduler_deliberation_route_contract.py",
        "fake_laboratory_deliberation_composition_0274.py",
        "fake_laboratory_closed_local_handoff_0274.py",
        "fake_laboratory_recall_closed_result_frame_0274.py",
        "fake_laboratory_existing_scheduler_closed_loop_smoke_0274.py",
        "github_dual_artifact_laboratory_smoke_0275.py",
        "github_operator_laboratory_advisory_projection_0281.py",
        "scheduler_managed_qdrant_projection_binding_0283.py",
        "scheduler_managed_qdrant_recall_binding_0283.py",
    ):
        assert required in source

    for forbidden in (
        "import context.laboratory_framework_contract_0273",
        "from context.laboratory_framework_contract_0273",
        "subprocess.",
        "urlopen(",
        "requests.",
        "httpx.",
        "sqlite3",
        "qdrant_client",
    ):
        assert forbidden not in source


def test_required_future_refs_are_preserved() -> None:
    source = MODULE.read_text(encoding="utf-8")

    for required in (
        '"laboratory_ref"',
        '"origin_laboratory_ref"',
        '"target_laboratory_ref"',
        '"visit_ref"',
        '"specialist_ref"',
        '"conversation_ref"',
        '"context_refs"',
        '"return_route_ref"',
    ):
        assert required in source


def test_tool_only_reads_source_and_writes_report() -> None:
    source = TOOL.read_text(encoding="utf-8")

    assert "path.read_text" in source
    assert "audit_specialists_laboratories_chain_reuse" in source
    assert "_write_json_atomic" in source
    for forbidden in (
        "subprocess.",
        "sqlite3",
        "qdrant_client",
        "Scheduler(",
        "ControlProxy(",
        "EventBus(",
    ):
        assert forbidden not in source


def test_phase_documents_locked_architecture() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )

    for required in (
        "architecture_preserved: true",
        "existing_laboratory_contract_reused: true",
        "existing_fake_provider_reused: true",
        "existing_scheduler_visit_binding_reused: true",
        "existing_specialist_route_frames_reused: true",
        "existing_handoff_recall_smoke_reused: true",
        "existing_qdrant_chain_reused: true",
        "portable_specialist_contract_missing: true",
        "new_laboratory_manager_justified: false",
        "new_scheduler_justified: false",
        "scheduler_modified: false",
        "eventbus_observation_only: true",
        "sql_remains_authority: true",
        "qdrant_projection_recall_only: true",
        "dev_shm_fast_route_plane: true",
        "control_proxy_lateral_only: true",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_report_versions_contract_and_names_r2() -> None:
    report = REPORT.read_text(encoding="utf-8")

    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: existing_chain_reuse_confirmed",
        "context_contract_version: "
        "missipy.specialists_laboratories.chain_reuse_audit.v1",
        "context_contract_changed: true",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "0284-r2-portable-specialist-contract",
    ):
        assert required in report
