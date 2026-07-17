from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORRELATION = ROOT / "src/context/love_imported_actions_run_preview_0287.py"
RUNTIME = ROOT / "src/context/love_imported_actions_runtime_contract_0287.py"
TOOL = ROOT / "tools/run_love_actions_closed_loop_0287.py"
PUBLISH_TOOL = ROOT / "tools/publish_love_final_deliverable_0287.py"
CONTEXT_TEST = ROOT / "tests/context/test_love_imported_actions_run_preview_0287_r7_r15_r2.py"
RUNTIME_TEST = ROOT / "tests/context/test_love_imported_actions_runtime_contract_0287_r7_r15_r2.py"
TOOL_TEST = ROOT / "tests/tools/test_run_love_actions_closed_loop_0287_r7_r15_r2.py"
REPORT = ROOT / "PHASE0287_R7_R15_R2_IMPORTED_ACTIONS_RUN_PREVIEW_REPORT.md"
ARCH = ROOT / "doc/architecture/IMPORTED_ACTIONS_RUN_PREVIEW_0287_R7_R15_R2.md"
DOT = ROOT / "doc/architecture/IMPORTED_ACTIONS_RUN_PREVIEW_0287_R7_R15_R2.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0287_R7_R15_R2_IMPORTED_ACTIONS_RUN_PREVIEW.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_R15_R2_IMPORTED_ACTIONS_RUN_PREVIEW.md"
RULE_TEST = Path(__file__)


def test_r15_r2_bundle_is_complete_and_dot_is_source_only() -> None:
    for path in (
        CORRELATION,
        RUNTIME,
        TOOL,
        PUBLISH_TOOL,
        CONTEXT_TEST,
        RUNTIME_TEST,
        TOOL_TEST,
        REPORT,
        ARCH,
        DOT,
        CHANGELOG,
        MANIFEST,
        RULE_TEST,
    ):
        assert path.is_file(), path
    assert not DOT.with_suffix(".svg").exists()


def test_domain_contracts_are_transport_neutral() -> None:
    combined = CORRELATION.read_text(encoding="utf-8") + RUNTIME.read_text(
        encoding="utf-8"
    )
    for forbidden in (
        "import subprocess",
        "import os",
        "import urllib",
        "import requests",
        "GitHubCli",
        "QdrantClient(",
        "openvino.runtime",
        "DeterministicLoveProjectionPort",
        "DeterministicE5ShapeEmbedder",
        "ImportedActionsLocalScheduler",
    ):
        assert forbidden not in combined
    for required in (
        "GitHubActionsArtifactIdentity",
        "ImportedActionsRealBackendAttestation",
        "ImportedActionsRuntimePorts",
        "proof_digest",
        "plan_digest",
        "preview_required",
        "remote_mutation_performed",
    ):
        assert required in combined


def test_runtime_contract_requires_real_e5_qdrant_and_evidence() -> None:
    text = RUNTIME.read_text(encoding="utf-8")
    for required in (
        "openvino_e5_real",
        "qdrant_write_real",
        "qdrant_returns_references_only",
        "embedding_dimension != 384",
        "real runtime attestation requires evidence_refs",
        "runtime factory must return ImportedActionsRuntimePorts",
        "scheduler must implement the canonical SchedulerContract",
        "scheduler_lifecycle",
        "tool-bounded",
        "externally-managed",
        '_require_callable(self.scheduler, "emit")',
        '_require_callable(self.scheduler, "run")',
        '_require_callable(self.projection_port, "project")',
        '_require_callable(self.embedder, "embed_query")',
        '_require_callable(self.executor, "search_dense")',
    ):
        assert required in text
    for forbidden in (
        "false  # test",
        "deterministic-transition",
        "in-memory projection",
    ):
        assert forbidden not in text.lower()


def test_tool_reuses_r14_and_r15_r1_and_forbids_execute_surface() -> None:
    text = TOOL.read_text(encoding="utf-8")
    for required in (
        "run_love_full_deterministic_local_smoke",
        "execute_love_final_deliverable_remote_publication",
        "GitHubCliFinalDeliverablePublicationAdapter",
        '"run",\n                "download"',
        'parser.add_argument(\n        "--runtime-factory"',
        "_load_runtime_factory",
        "validate_imported_actions_runtime_ports",
        "_run_r14_on_existing_scheduler",
        "runtime.scheduler.run()",
        "runtime.scheduler.shutdown()",
        'runtime.scheduler_lifecycle == "externally-managed"',
        "asyncio.FIRST_COMPLETED",
        "GitHubDualArtifactRunAssemblyPolicy(allow_missing_advisory=False)",
        '--candidate-decision',
        "execute=False",
        "remote_mutation_allowed=False",
        "_write_json_atomic",
    ):
        assert required in text
    assert 'parser.add_argument("--execute"' not in text
    assert "AUTODOC_REMOTE_MUTATION_ALLOWED" not in text
    assert "build_imported_actions_local_runtime" not in text


def test_projection_receipts_are_cross_checked_against_attestation() -> None:
    text = CORRELATION.read_text(encoding="utf-8")
    for required in (
        'len(projection_receipts) != 2',
        'receipt.get("openvino_e5_used") is not True',
        'receipt.get("qdrant_write_performed") is not True',
        'int(projection.get("dimension", 0)) != 384',
        'projection.get("normalized") is not True',
        "command.runtime_attestation.qdrant_collection",
        'publication_preview.get("mode") != "preview"',
        'publication_preview.get("remote_mutation_performed") is not False',
    ):
        assert required in text


def test_exact_three_artifacts_and_preview_are_locked() -> None:
    tool = TOOL.read_text(encoding="utf-8")
    domain = CORRELATION.read_text(encoding="utf-8")
    for token in (
        "autodoc-authoritative-request",
        "autodoc-copilot-advisory",
        "autodoc-dual-artifact-manifest",
    ):
        assert token in tool
        assert token in domain
    assert '"live_path_status": "real-backend-preview"' in domain
    assert '"live_path_uses_real_backend": True' in domain


def test_missing_plan_now_has_operator_facing_error() -> None:
    text = PUBLISH_TOOL.read_text(encoding="utf-8")
    for token in (
        "def _load_plan_payload",
        "plan file not found",
        "run_love_actions_closed_loop_0287.py",
        'print(f"error: {exc}", file=sys.stderr)',
    ):
        assert token in text


def test_report_contains_mandatory_code_rule_review_fields() -> None:
    text = REPORT.read_text(encoding="utf-8")
    for token in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: transition",
        "live_path_uses_real_backend: false",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "network_added: true",
        "github_api_added: true",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "search_commands_bounded: n/a",
        "There is no fallback factory",
    ):
        assert token in text


def test_manifest_keeps_preview_and_remaining_roadmap() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    for token in (
        "Preview remains mandatory",
        "0287-r7-r15-r3",
        "0287-r7-r16",
        "No remote mutation",
        "No dummy runtime or fallback",
        "tool-bounded",
        "externally-managed",
    ):
        assert token in text
