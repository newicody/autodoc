from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "github_artifact_server_fetch.example.ini"
DATASET = ROOT / "src" / "context" / "github_artifact_server_dataset.py"
CONFIG_MODULE = ROOT / "src" / "context" / "github_artifact_server_fetch_config.py"
TOOL = ROOT / "tools" / "run_github_artifact_server_sync_once.py"
DOC = ROOT / "doc" / "architecture" / "GITHUB_ARTIFACT_SERVER_DATASET_SYNC_0167.md"
RULE = ROOT / "doc" / "code-rules" / "0167_github_artifact_server_dataset_sync_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0167_CHANGED_FILES.md"


def test_0167_files_exist() -> None:
    for path in [CONFIG, DATASET, CONFIG_MODULE, TOOL, DOC, RULE, MANIFEST]:
        assert path.exists()


def test_0167_context_is_server_dataset_contract_not_network_client() -> None:
    text = DATASET.read_text(encoding="utf-8") + CONFIG_MODULE.read_text(encoding="utf-8")

    for token in [
        "ServerDatasetLayout",
        "GitHubFetchedArtifactRecord",
        "AttachmentRecord",
        "ConversionQueueRecord",
        "conversion is queued only after complete sync",
        "server dataset",
    ]:
        assert token in text

    for forbidden in [
        "requests.",
        "urllib.",
        "http.client",
        "subprocess",
        "DbApiSqlContextStore(",
        "Qdrant",
        "OpenVINO",
        "fcrontab",
        "rc-service",
        "rc-update",
    ]:
        assert forbidden not in text


def test_0167_tool_syncs_local_artifact_only() -> None:
    text = TOOL.read_text(encoding="utf-8")

    for token in [
        "already fetched from GitHub Actions",
        "No GitHub API call",
        "vispy",
        "conversion_queue",
        "sync_artifact_directory",
    ]:
        assert token in text

    for forbidden in [
        "requests.",
        "urllib.",
        "http.client",
        "rc-service",
        "rc-update",
        "fcrontab",
        "DbApiSqlContextStore(",
        "Qdrant",
        "OpenVINO",
    ]:
        assert forbidden not in text


def test_0167_docs_lock_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")

    for token in [
        "GitHub Actions artifacts remain the source system",
        "server dataset configured by ConfigObj",
        "raw sync completes before conversion",
        "VisPy observation event",
        "do not store user artifacts in the development repository",
    ]:
        assert token in doc

    for token in [
        "Do not store user artifacts in Git",
        "Use the server dataset configured by ConfigObj",
        "Queue conversion only after complete raw sync",
        "Do not create a parallel artifact system",
    ]:
        assert token in rule


def test_0167_manifest_lists_limited_changes() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    for path in [
        "config/github_artifact_server_fetch.example.ini",
        "src/context/github_artifact_server_dataset.py",
        "src/context/github_artifact_server_fetch_config.py",
        "tools/run_github_artifact_server_sync_once.py",
        "tests/context/test_github_artifact_server_dataset_0167.py",
        "tests/tools/test_github_artifact_server_sync_once_0167.py",
        "tests/rules/test_github_artifact_server_dataset_sync_0167_rule.py",
        "doc/architecture/GITHUB_ARTIFACT_SERVER_DATASET_SYNC_0167.md",
        "doc/code-rules/0167_github_artifact_server_dataset_sync_rule.md",
        "doc/docs/architecture/runtime/167_github_artifact_server_dataset_sync.dot",
        "doc/CHANGELOG_0167_GITHUB_ARTIFACT_SERVER_DATASET_SYNC.md",
        "doc/manifests/MANIFEST_0167_CHANGED_FILES.md",
        "PHASE0167_TEST_REPORT.md",
    ]:
        assert path in text
