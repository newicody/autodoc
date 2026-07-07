"""Config loader for server-side GitHub artifact dataset sync.

The config is ConfigObj-style but loaded with a small stdlib parser to satisfy
core code rules. The actual token value is never stored here; only token_env is
kept for the future fetch client boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .github_artifact_server_dataset import ServerDatasetLayout


@dataclass(frozen=True, slots=True)
class GitHubArtifactServerFetchConfig:
    config_path: Path
    token_env: str
    api_url: str
    project_url: str
    external_repository: str
    development_repository: str
    workflow_name: str
    artifact_name_prefix: str
    dataset: ServerDatasetLayout
    allowed_repositories: tuple[str, ...]
    allowed_attachment_kinds: tuple[str, ...]
    max_attachment_bytes: int
    queue_after_complete_sync: bool
    skip_already_processed: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": "missipy.github_artifact.server_fetch_config.v1",
            "config_path": str(self.config_path),
            "github": {"token_env": self.token_env, "api_url": self.api_url},
            "project": {"url": self.project_url},
            "artifact_source": {
                "repository": self.external_repository,
                "workflow_name": self.workflow_name,
                "artifact_name_prefix": self.artifact_name_prefix,
            },
            "server_dataset": self.dataset.to_json_dict(),
            "attachments": {
                "allowed_kinds": list(self.allowed_attachment_kinds),
                "max_attachment_bytes": self.max_attachment_bytes,
            },
            "conversion": {
                "queue_after_complete_sync": self.queue_after_complete_sync,
                "skip_already_processed": self.skip_already_processed,
            },
            "safety": {
                "development_repository": self.development_repository,
                "allowed_repositories": list(self.allowed_repositories),
                "read_only_fetch": True,
                "allow_remote_mutation": False,
                "allow_sql_write": False,
                "allow_qdrant_write": False,
            },
        }


def load_github_artifact_server_fetch_config(path: Path) -> GitHubArtifactServerFetchConfig:
    payload = _load_ini(path)
    return build_github_artifact_server_fetch_config(path, payload)


def build_github_artifact_server_fetch_config(path: Path, payload: Mapping[str, Any]) -> GitHubArtifactServerFetchConfig:
    github = _section(payload, "github")
    project = _section(payload, "project")
    artifact = _section(payload, "artifact_source")
    dataset_section = _section(payload, "server_dataset")
    if not dataset_section:
        dataset_section = _section(payload, "dataset")
    attachments = _section(payload, "attachments")
    conversion = _section(payload, "conversion")
    safety = _section(payload, "safety")

    repositories = _list_value(artifact.get("repositories") or artifact.get("repository"))
    if len(repositories) != 1:
        raise ValueError("0167 expects exactly one external repository")
    external_repository = repositories[0]
    allowed_repositories = tuple(_list_value(safety.get("allowed_repositories")) or repositories)

    dataset = ServerDatasetLayout(
        root=Path(str(dataset_section.get("root", ".var/server_datasets/github_artifacts"))).expanduser(),
        raw_dir=str(dataset_section.get("raw_dir", "raw")),
        index_dir=str(dataset_section.get("index_dir", "index")),
        history_dir=str(dataset_section.get("history_dir", "history")),
        conversion_queue_dir=str(dataset_section.get("conversion_queue_dir", "conversion_queue")),
        converted_dir=str(dataset_section.get("converted_dir", "converted")),
        vispy_events_dir=str(dataset_section.get("vispy_events_dir", "vispy_events")),
        state_file=str(dataset_section.get("state_file", "index/fetch_state.json")),
    )

    config = GitHubArtifactServerFetchConfig(
        config_path=path,
        token_env=str(github.get("token_env", "")).strip(),
        api_url=str(github.get("api_url", "https://api.github.com")).strip(),
        project_url=str(project.get("url", "")).strip(),
        external_repository=external_repository,
        development_repository=str(safety.get("development_repository", "")).strip(),
        workflow_name=str(artifact.get("workflow_name", "")).strip(),
        artifact_name_prefix=str(artifact.get("artifact_name_prefix", "autodoc-ticket-artifact-")).strip(),
        dataset=dataset,
        allowed_repositories=allowed_repositories,
        allowed_attachment_kinds=tuple(_list_value(attachments.get("allowed_kinds")) or ("image", "audio", "video", "pdf", "archive", "text", "binary")),
        max_attachment_bytes=int(attachments.get("max_attachment_bytes", 524288000)),
        queue_after_complete_sync=_bool_value(conversion.get("queue_after_complete_sync", True)),
        skip_already_processed=_bool_value(conversion.get("skip_already_processed", True)),
    )
    validation = validate_github_artifact_server_fetch_config(config, raw_payload=payload)
    if not validation["allowed"]:
        details = ", ".join(issue["code"] for issue in validation["issues"])
        raise ValueError(f"github artifact server fetch config rejected: {details}")
    return config


def validate_github_artifact_server_fetch_config(config: GitHubArtifactServerFetchConfig, *, raw_payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not config.token_env:
        issues.append(_issue("token_env_missing", "github.token_env is required"))
    if _looks_like_secret_value(config.token_env):
        issues.append(_issue("token_env_secret_value", "token_env must name an environment variable, not contain a token value"))
    if raw_payload is not None and _contains_forbidden_secret_key(raw_payload):
        issues.append(_issue("secret_literal_forbidden", "config must not contain token, secret, authorization or credential keys"))
    if config.external_repository == config.development_repository:
        issues.append(_issue("development_repo_ingestion", "external repository must not equal development repository"))
    if config.external_repository not in config.allowed_repositories:
        issues.append(_issue("repository_allowlist", "external repository must appear in safety.allowed_repositories"))
    if not str(config.dataset.root):
        issues.append(_issue("dataset_root_missing", "server_dataset.root is required"))
    if not config.queue_after_complete_sync:
        issues.append(_issue("conversion_gate", "conversion must be queued only after complete sync"))
    return {"allowed": not issues, "issues": issues}


def _load_ini(path: Path) -> dict[str, dict[str, str]]:
    current: str | None = None
    result: dict[str, dict[str, str]] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            result.setdefault(current, {})
            continue
        if "=" in line and current:
            key, value = line.split("=", 1)
            result[current][key.strip()] = value.strip()
    return result


def _section(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, Mapping) else {}


def _list_value(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (tuple, list)):
        return [str(item).strip() for item in value if str(item).strip()]
    normalized = str(value).replace("\\n", ",").replace("\n", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]

def _bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "yes", "true", "on"}


def _looks_like_secret_value(value: str) -> bool:
    stripped = value.strip()
    lowered = stripped.lower()
    if lowered.startswith(("ghp_", "github_pat_", "gho_", "ghu_", "ghs_", "ghr_")):
        return True
    if len(stripped) >= 40 and "_" not in stripped and stripped.upper() != stripped:
        return True
    return False


def _contains_forbidden_secret_key(payload: Mapping[str, Any]) -> bool:
    forbidden = ("token", "secret", "authorization", "credential", "password")
    for key, value in payload.items():
        key_lower = str(key).lower()
        if key_lower != "token_env" and any(part in key_lower for part in forbidden):
            return True
        if isinstance(value, Mapping) and _contains_forbidden_secret_key(value):
            return True
    return False


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}
