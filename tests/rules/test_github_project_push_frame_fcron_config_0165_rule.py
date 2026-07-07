from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "github_project_push_frame.example.ini"
FRAME = ROOT / "src" / "context" / "github_project_push_frame.py"
CONFIG_MODULE = ROOT / "src" / "context" / "github_project_push_frame_config.py"
TOOL = ROOT / "tools" / "run_github_project_push_frame_config_check.py"
DOC = ROOT / "doc" / "architecture" / "GITHUB_PROJECT_PUSH_FRAME_FCRON_CONFIG_0165.md"
RULE = ROOT / "doc" / "code-rules" / "0165_project_push_frame_fcron_config_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0165_CHANGED_FILES.md"


def test_0165_files_exist() -> None:
    for path in [CONFIG, FRAME, CONFIG_MODULE, TOOL, DOC, RULE, MANIFEST]:
        assert path.exists()


def test_0165_config_module_uses_configobj_and_idempotent_fcron_text() -> None:
    text = CONFIG_MODULE.read_text(encoding="utf-8")
    for token in ["ConfigObj", "token_env", "upsert_fcron_table", "build_fcron_entry", "development_repo_ingestion", "interval_minutes != 10", "history_mode", "append_only"]:
        assert token in text
    for forbidden in ["requests.", "urllib.", "http.client", "subprocess", "rc-service", "rc-update", "fcron start", "rc-update add fcron", "DbApiSqlContextStore(", "Qdrant", "OpenVINO"]:
        assert forbidden not in text


def test_0165_project_push_frame_contracts_group_artifact_family() -> None:
    text = FRAME.read_text(encoding="utf-8")
    for token in ["ProjectPushFrame", "ProjectPushFrameRevision", "CopilotPreliminaryOpinionArtifact", "LocalInferenceResponseArtifact", "UserArtifactDecision", "usable_as_hint", "usable_as_authority", "append-only", "build_origin_frame_id"]:
        assert token in text
    for forbidden in ["requests.", "urllib.", "http.client", "subprocess", "DbApiSqlContextStore(", "Qdrant", "OpenVINO"]:
        assert forbidden not in text


def test_0165_tool_does_not_manage_openrc_or_start_fcron() -> None:
    text = TOOL.read_text(encoding="utf-8")
    for token in ["load_github_artifact_scan_config", "upsert_fcron_table", "write_fcrontab", "started_fcron", "openrc_touched"]:
        assert token in text
    for forbidden in ["subprocess", "rc-service", "rc-update", "fcrontab ", "service fcron", "OpenRC"]:
        assert forbidden not in text


def test_0165_docs_lock_user_corrections() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    for token in ["do not start fcron", "edit the concerned fcron table", "without duplicates", "ConfigObj", "10 minutes", "ticket + column name + options", "Copilot preliminary opinion is advisory only", "append-only history", "reuse existing builders"]:
        assert token in doc
    for token in ["Do not start fcron", "Do not manage OpenRC", "Use ConfigObj", "No duplicate fcron entry", "Do not create a new GitHub adapter", "Copilot opinion is advisory only"]:
        assert token in rule


def test_0165_manifest_lists_limited_changes() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    for path in [
        "config/github_project_push_frame.example.ini",
        "src/context/github_project_push_frame.py",
        "src/context/github_project_push_frame_config.py",
        "tools/run_github_project_push_frame_config_check.py",
        "tests/context/test_github_project_push_frame_config_0165.py",
        "tests/tools/test_github_project_push_frame_config_check_0165.py",
        "tests/rules/test_github_project_push_frame_fcron_config_0165_rule.py",
        "doc/architecture/GITHUB_PROJECT_PUSH_FRAME_FCRON_CONFIG_0165.md",
        "doc/code-rules/0165_project_push_frame_fcron_config_rule.md",
        "doc/docs/architecture/runtime/165_project_push_frame_fcron_config.dot",
        "doc/CHANGELOG_0165_PROJECT_PUSH_FRAME_FCRON_CONFIG.md",
        "doc/manifests/MANIFEST_0165_CHANGED_FILES.md",
        "PHASE0165_TEST_REPORT.md",
    ]:
        assert path in text
