from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESOLUTION = ROOT / "src/context/love_actions_closed_loop_resolution_0287.py"
TOOL = ROOT / "tools/run_love_actions_closed_loop_0287.py"
PUBLISH_TOOL = ROOT / "tools/publish_love_final_deliverable_0287.py"
CONFIG = ROOT / "config/love_actions_closed_loop.example.ini"
CONTEXT_TEST = ROOT / "tests/context/test_love_actions_closed_loop_resolution_0287_r7_r15_r2_r1.py"
TOOL_TEST = ROOT / "tests/tools/test_run_love_actions_closed_loop_0287_r7_r15_r2.py"
REPORT = ROOT / "PHASE0287_R7_R15_R2_R1_AUTOMATIC_PROJECTV2_RUNTIME_RESOLUTION_REPORT.md"
ARCH = ROOT / "doc/architecture/AUTOMATIC_PROJECTV2_RUNTIME_RESOLUTION_0287_R7_R15_R2_R1.md"
DOT = ROOT / "doc/architecture/AUTOMATIC_PROJECTV2_RUNTIME_RESOLUTION_0287_R7_R15_R2_R1.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0287_R7_R15_R2_R1_AUTOMATIC_PROJECTV2_RUNTIME_RESOLUTION.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_R15_R2_R1_AUTOMATIC_PROJECTV2_RUNTIME_RESOLUTION.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
RULE_TEST = Path(__file__)


def test_corrective_bundle_is_complete_and_dot_is_source_only() -> None:
    for path in (
        RESOLUTION,
        TOOL,
        PUBLISH_TOOL,
        CONFIG,
        CONTEXT_TEST,
        TOOL_TEST,
        REPORT,
        ARCH,
        DOT,
        CHANGELOG,
        MANIFEST,
        INSTALLATION,
        RULE_TEST,
    ):
        assert path.is_file(), path
    assert not DOT.with_suffix(".svg").exists()


def test_resolution_contract_is_pure_typed_and_exact() -> None:
    text = RESOLUTION.read_text(encoding="utf-8")
    for required in (
        "LoveProjectV2TargetRequest",
        "ResolvedLoveProjectV2Target",
        "resolve_love_projectv2_target",
        "source Issue is not present exactly once",
        "configured ProjectV2 field cannot be resolved exactly",
        "project item and field overrides must be supplied together",
        "authoritative-request-and-project-config",
    ):
        assert required in text
    for forbidden in (
        "import subprocess",
        "import os",
        "import configparser",
        "import requests",
        "GitHubCli",
        "QdrantClient",
        "openvino",
    ):
        assert forbidden not in text


def test_short_operator_command_and_configuration_precedence_are_present() -> None:
    text = TOOL.read_text(encoding="utf-8")
    for required in (
        "LoveClosedLoopLocalSettings",
        "_resolve_local_settings",
        ".var/config/love_actions_closed_loop.ini",
        ".var/config/github_project_v2_query_only.ini",
        "AUTODOC_LOVE_RUNTIME_FACTORY",
        "resolve_project_target",
        'output["_r15_resolution"]',
        'parser.add_argument("--project-item-id", default="")',
        'parser.add_argument("--project-field-ref", default="")',
        'parser.add_argument("--project-owner")',
        'parser.add_argument("--project-number", type=int)',
    ):
        assert required in text
    assert 'parser.add_argument("--execute"' not in text
    assert 'parser.add_argument("--runtime-factory",\n        required=True' not in text


def test_existing_graphql_adapter_owns_read_only_target_resolution() -> None:
    text = PUBLISH_TOOL.read_text(encoding="utf-8")
    for required in (
        "_PROJECT_TARGET_QUERY",
        "def resolve_project_target(",
        "LoveProjectV2TargetRequest",
        "resolve_love_projectv2_target",
        '"issueNumber": request.issue_number',
        '"projectNumber": request.project_number',
    ):
        assert required in text
    assert "addProjectV2ItemById" not in text


def test_runtime_remains_explicit_without_discovery_or_dummy_fallback() -> None:
    tool = TOOL.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    for required in (
        "real runtime factory is not configured",
        "runtime factory must use module:function",
        "_load_runtime_factory",
    ):
        assert required in tool
    assert "factory =" in config
    for forbidden in (
        "pkgutil.iter_modules",
        "walk_packages",
        "DeterministicLoveProjectionPort",
        "dummy runtime",
    ):
        assert forbidden not in tool


def test_cumulative_installation_documents_the_short_preview_path() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    for required in (
        "love_actions_closed_loop.example.ini",
        "Preview final sans identifiants ProjectV2 manuels",
        "PROJECT_ITEM_ID",
        "python tools/run_love_actions_closed_loop_0287.py",
        "--candidate-decision promote",
        "Le preview ne réalise aucune mutation distante",
    ):
        assert required in text


def test_report_contains_mandatory_code_rule_review_fields() -> None:
    text = REPORT.read_text(encoding="utf-8")
    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: transition",
        "live_path_uses_real_backend: false",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "search_commands_bounded: n/a",
    ):
        assert required in text
