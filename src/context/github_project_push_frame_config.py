"""ConfigObj-backed project push frame and fcron table contract.

This module reads non-secret config, validates the external repository boundary,
and renders an idempotent fcron table block. It does not install or start fcron;
it only edits the target table text when an operator explicitly asks the tool to
write a file.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Mapping


_CONFIG_SCHEMA = "missipy.github_project.project_push_frame_fcron_config.v1"
_DEFAULT_SCAN_COMMAND = "tools/run_github_artifact_scan_once.py"
_DEFAULT_ARTIFACT_PREFIX = "autodoc-ticket-artifact-"
_MARKER_PREFIX = "AUTODOC-GITHUB-ARTIFACT-SCAN"


@dataclass(frozen=True, slots=True)
class GithubArtifactScanConfig:
    config_path: Path
    token_env: str
    api_url: str
    project_url: str
    project_owner: str
    project_number: int
    external_repository: str
    development_repository: str
    workflow_name: str
    artifact_name_prefix: str
    trigger_source: str
    scan_mode: str
    interval_minutes: int
    working_directory: Path
    python_executable: str
    scan_command: str
    state_path: Path
    inbox_dir: Path
    fcron_table_path: Path
    allowed_repositories: tuple[str, ...]
    context_option_names: tuple[str, ...]
    copilot_preliminary_opinion: bool
    history_mode: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _CONFIG_SCHEMA,
            "config_path": str(self.config_path),
            "github": {"token_env": self.token_env, "api_url": self.api_url},
            "project": {"url": self.project_url, "owner": self.project_owner, "number": self.project_number},
            "artifact_source": {
                "repository": self.external_repository,
                "workflow_name": self.workflow_name,
                "artifact_name_prefix": self.artifact_name_prefix,
                "trigger_source": self.trigger_source,
            },
            "scan": {
                "mode": self.scan_mode,
                "interval_minutes": self.interval_minutes,
                "working_directory": str(self.working_directory),
                "python_executable": self.python_executable,
                "scan_command": self.scan_command,
                "state_path": str(self.state_path),
                "inbox_dir": str(self.inbox_dir),
                "fcron_table_path": str(self.fcron_table_path),
            },
            "safety": {
                "development_repository": self.development_repository,
                "allowed_repositories": list(self.allowed_repositories),
                "read_only_scan": True,
                "allow_workflow_dispatch": False,
                "allow_remote_mutation": False,
                "allow_sql_write": False,
                "allow_qdrant_write": False,
            },
            "pipeline": {
                "context_option_names": list(self.context_option_names),
                "copilot_preliminary_opinion": self.copilot_preliminary_opinion,
                "history_mode": self.history_mode,
            },
        }


def load_github_artifact_scan_config(path: Path) -> GithubArtifactScanConfig:
    payload = _load_configobj_mapping(path)
    return build_github_artifact_scan_config(path, payload)


def build_github_artifact_scan_config(path: Path, payload: Mapping[str, Any]) -> GithubArtifactScanConfig:
    github = _section(payload, "github")
    project = _section(payload, "project")
    artifact = _section(payload, "artifact_source")
    scan = _section(payload, "scan")
    safety = _section(payload, "safety")
    pipeline = _section(payload, "pipeline")

    repositories = _list_value(artifact.get("repositories") or artifact.get("repository"))
    allowed_repositories = tuple(_list_value(safety.get("allowed_repositories")) or repositories)
    if len(repositories) != 1:
        raise ValueError("0165 expects exactly one external repository in artifact_source.repositories")
    external_repository = repositories[0]

    config = GithubArtifactScanConfig(
        config_path=path,
        token_env=str(github.get("token_env", "")).strip(),
        api_url=str(github.get("api_url", "https://api.github.com")).strip(),
        project_url=str(project.get("url", "")).strip(),
        project_owner=str(project.get("owner", "")).strip(),
        project_number=int(project.get("number", 0)),
        external_repository=external_repository,
        development_repository=str(safety.get("development_repository", "")).strip(),
        workflow_name=str(artifact.get("workflow_name", "")).strip(),
        artifact_name_prefix=str(artifact.get("artifact_name_prefix", _DEFAULT_ARTIFACT_PREFIX)).strip(),
        trigger_source=str(artifact.get("trigger_source", "github_action_on_ticket_event")).strip(),
        scan_mode=str(scan.get("mode", "fcron")).strip(),
        interval_minutes=int(scan.get("interval_minutes", 10)),
        working_directory=Path(str(scan.get("working_directory", "."))).expanduser(),
        python_executable=str(scan.get("python_executable", "python")).strip(),
        scan_command=str(scan.get("scan_command", _DEFAULT_SCAN_COMMAND)).strip(),
        state_path=Path(str(scan.get("state_path", ".var/github/artifacts/state/index.json"))),
        inbox_dir=Path(str(scan.get("inbox_dir", ".var/github/artifacts/inbox"))),
        fcron_table_path=Path(str(scan.get("fcron_table_path", ".var/fcron/autodoc-github-artifact-scan.fcrontab"))),
        allowed_repositories=allowed_repositories,
        context_option_names=tuple(_list_value(pipeline.get("context_option_names")) or ("include_current_ticket",)),
        copilot_preliminary_opinion=_bool_value(pipeline.get("copilot_preliminary_opinion", True)),
        history_mode=str(pipeline.get("history_mode", "append_only")).strip(),
    )
    validation = validate_github_artifact_scan_config(config, raw_payload=payload)
    if not validation["allowed"]:
        details = ", ".join(issue["code"] for issue in validation["issues"])
        raise ValueError(f"github artifact scan config rejected: {details}")
    return config


def validate_github_artifact_scan_config(config: GithubArtifactScanConfig, *, raw_payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not config.token_env:
        issues.append(_issue("token_env_missing", "github.token_env is required"))
    if _looks_like_secret_value(config.token_env):
        issues.append(_issue("token_env_secret_value", "token_env must name an environment variable, not contain a token value"))
    if raw_payload is not None and _contains_forbidden_secret_key(raw_payload):
        issues.append(_issue("secret_literal_forbidden", "config must not contain token, secret, authorization or credential keys"))
    if not _is_owner_name(config.external_repository):
        issues.append(_issue("external_repository_format", "external repository must use owner/name form"))
    if not _is_owner_name(config.development_repository):
        issues.append(_issue("development_repository_format", "development repository must use owner/name form"))
    if config.external_repository == config.development_repository:
        issues.append(_issue("development_repo_ingestion", "external repository must not equal development repository"))
    if config.external_repository not in config.allowed_repositories:
        issues.append(_issue("repository_allowlist", "external repository must appear in safety.allowed_repositories"))
    if config.scan_mode != "fcron":
        issues.append(_issue("scan_mode", "scan.mode must be fcron for 0165"))
    if config.interval_minutes <= 0:
        issues.append(_issue("interval_minutes", "scan.interval_minutes must be positive"))
    if config.interval_minutes != 10:
        issues.append(_issue("interval_not_10", "0165 locks default scan interval to 10 minutes"))
    if config.trigger_source != "github_action_on_ticket_event":
        issues.append(_issue("trigger_source", "artifact_source.trigger_source must be github_action_on_ticket_event"))
    if config.history_mode != "append_only":
        issues.append(_issue("history_mode", "pipeline.history_mode must be append_only"))
    return {"allowed": not issues, "issues": issues}


def build_fcron_entry(config: GithubArtifactScanConfig) -> str:
    marker = build_fcron_marker(config)
    schedule = f"*/{config.interval_minutes} * * * *"
    command = f"cd {config.working_directory} && {config.python_executable} {config.scan_command} --config {config.config_path}"
    return "\n".join([f"# BEGIN {marker}", "# managed by Autodoc; edit configobj config, not this block", schedule + " " + command, f"# END {marker}", ""])


def build_fcron_marker(config: GithubArtifactScanConfig) -> str:
    digest = hashlib.sha256(f"{config.project_url}\0{config.external_repository}\0{config.scan_command}".encode("utf-8")).hexdigest()[:16]
    return f"{_MARKER_PREFIX} {digest}"


def upsert_fcron_table(existing_text: str, entry_block: str, marker: str) -> str:
    begin = f"# BEGIN {marker}"
    end = f"# END {marker}"
    output: list[str] = []
    in_block = False
    for line in existing_text.splitlines():
        stripped = line.strip()
        if stripped == begin:
            in_block = True
            continue
        if stripped == end:
            in_block = False
            continue
        if in_block or marker in line:
            continue
        output.append(line)
    while output and not output[-1].strip():
        output.pop()
    if output:
        output.append("")
    output.extend(entry_block.rstrip("\n").splitlines())
    return "\n".join(output).rstrip() + "\n"


def render_config_check(config: GithubArtifactScanConfig) -> str:
    validation = validate_github_artifact_scan_config(config)
    lines = [
        "# GitHub artifact scan config check",
        "",
        f"status: `{'ok' if validation['allowed'] else 'blocked'}`",
        f"project_url: `{config.project_url}`",
        f"external_repository: `{config.external_repository}`",
        f"development_repository: `{config.development_repository}`",
        f"scan_mode: `{config.scan_mode}`",
        f"interval_minutes: `{config.interval_minutes}`",
        f"fcron_table_path: `{config.fcron_table_path}`",
        f"copilot_preliminary_opinion: `{config.copilot_preliminary_opinion}`",
        f"history_mode: `{config.history_mode}`",
        "",
        "## Issues",
        "",
    ]
    if validation["issues"]:
        lines.extend(f"- `{issue['code']}`: {issue['message']}" for issue in validation["issues"])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _load_configobj_mapping(path: Path) -> Mapping[str, Any]:
    """Load a ConfigObj-style INI file without importing external packages.

    The 0165 contract keeps the operator-facing syntax compatible with
    ConfigObj-style section/key files, but this core context module remains
    stdlib-only under the project code rules. A future dependency patch may add
    a dedicated external ConfigObj loader at an approved boundary if needed.
    """
    return _load_ini_fallback(path)


def _load_ini_fallback(path: Path) -> dict[str, dict[str, str]]:
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


def _list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (tuple, list)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).replace("\n", ",").split(",") if item.strip()]


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
        if any(part in key_lower for part in forbidden) and key_lower != "token_env":
            return True
        if isinstance(value, Mapping) and _contains_forbidden_secret_key(value):
            return True
    return False


def _is_owner_name(repository: str) -> bool:
    if repository.count("/") != 1:
        return False
    owner, name = repository.split("/", 1)
    return bool(owner.strip()) and bool(name.strip())


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}
