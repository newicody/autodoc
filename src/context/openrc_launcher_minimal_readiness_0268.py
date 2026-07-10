"""OpenRC launcher minimal readiness for the closed prototype path.

0268 prepares a local OpenRC/launcher readiness envelope.  It does not install
OpenRC services, does not call rc-service/rc-update, does not start PostgreSQL,
OpenVINO, Qdrant, or any Autodoc runtime component, and does not modify
Scheduler.run.

Boundary:
- OpenRC/system/admin starts external services.
- Scheduler owns Autodoc runtime objects that use those services.
- 0268 is readiness/rendering only, not service execution.
- local/server remains the authority.
- No RuntimeManager is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


OPENRC_READINESS_SCHEMA = "missipy.openrc_launcher_minimal_readiness.v1"
DEFAULT_SERVICE_NAME = "autodoc-local-runtime"
DEFAULT_COMMAND = "python tools/compose_scheduler_managed_closed_result_frame_0264.py --format summary"


@dataclass(frozen=True)
class OpenRcLauncherServiceSpec:
    """Rendered local OpenRC service spec, not installed by this patch."""

    service_name: str = DEFAULT_SERVICE_NAME
    description: str = "Autodoc local runtime readiness surface"
    command: str = DEFAULT_COMMAND
    command_user: str = "eric"
    pidfile: str = "/run/autodoc-local-runtime.pid"
    depends_need: tuple[str, ...] = ("localmount",)
    depends_after: tuple[str, ...] = ("postgresql", "qdrant")
    extra_environment: tuple[tuple[str, str], ...] = ()

    def to_mapping(self) -> dict[str, Any]:
        return {
            "service_name": self.service_name,
            "description": self.description,
            "command": self.command,
            "command_user": self.command_user,
            "pidfile": self.pidfile,
            "depends_need": list(self.depends_need),
            "depends_after": list(self.depends_after),
            "extra_environment": dict(self.extra_environment),
        }


@dataclass(frozen=True)
class OpenRcLauncherMinimalReadinessRequest:
    """Readiness request for rendering a local OpenRC launcher surface."""

    service_name: str = DEFAULT_SERVICE_NAME
    repository: str = "newicody/autodoc"
    policy_decision_id: str = ""
    install_service: bool = False
    start_service: bool = False
    enable_service: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "service_name": self.service_name,
            "repository": self.repository,
            "policy_decision_id": self.policy_decision_id,
            "install_service": self.install_service,
            "start_service": self.start_service,
            "enable_service": self.enable_service,
        }


@dataclass(frozen=True)
class OpenRcLauncherMinimalReadinessReport:
    """Serializable OpenRC/launcher readiness envelope."""

    valid: bool
    issues: tuple[str, ...]
    request: OpenRcLauncherMinimalReadinessRequest
    readiness_ref: str = ""
    service_spec: OpenRcLauncherServiceSpec = field(default_factory=OpenRcLauncherServiceSpec)
    rendered_openrc_script: str = ""
    source_reports: Mapping[str, str] = field(default_factory=dict)
    closed_frame_summary: Mapping[str, Any] = field(default_factory=dict)
    github_handoff_summary: Mapping[str, Any] = field(default_factory=dict)
    checks: Mapping[str, bool] = field(default_factory=dict)
    local_authority: bool = True
    readiness_only: bool = True
    openrc_admin_action_required: bool = True
    scheduler_owns_runtime_objects: bool = True
    external_services_started_by_openrc: bool = True
    installs_service: bool = False
    starts_service: bool = False
    enables_service: bool = False
    executes_runtime: bool = False
    starts_postgresql: bool = False
    starts_openvino: bool = False
    starts_qdrant: bool = False
    calls_rc_service: bool = False
    calls_rc_update: bool = False
    modifies_scheduler_run: bool = False
    creates_runtime_manager: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": OPENRC_READINESS_SCHEMA,
            "openrc_launcher_minimal_readiness": True,
            "valid": self.valid,
            "issues": list(self.issues),
            "request": self.request.to_mapping(),
            "readiness_ref": self.readiness_ref,
            "service_spec": self.service_spec.to_mapping(),
            "rendered_openrc_script": self.rendered_openrc_script,
            "source_reports": dict(self.source_reports),
            "closed_frame_summary": dict(self.closed_frame_summary),
            "github_handoff_summary": dict(self.github_handoff_summary),
            "checks": dict(self.checks),
            "local_authority": self.local_authority,
            "readiness_only": self.readiness_only,
            "openrc_admin_action_required": self.openrc_admin_action_required,
            "scheduler_owns_runtime_objects": self.scheduler_owns_runtime_objects,
            "external_services_started_by_openrc": self.external_services_started_by_openrc,
            "installs_service": self.installs_service,
            "starts_service": self.starts_service,
            "enables_service": self.enables_service,
            "executes_runtime": self.executes_runtime,
            "starts_postgresql": self.starts_postgresql,
            "starts_openvino": self.starts_openvino,
            "starts_qdrant": self.starts_qdrant,
            "calls_rc_service": self.calls_rc_service,
            "calls_rc_update": self.calls_rc_update,
            "modifies_scheduler_run": self.modifies_scheduler_run,
            "creates_runtime_manager": self.creates_runtime_manager,
        }


def validate_openrc_readiness_inputs(
    *,
    closed_frame: Mapping[str, Any],
    github_handoff: Mapping[str, Any],
    request: OpenRcLauncherMinimalReadinessRequest,
) -> tuple[str, ...]:
    """Validate readiness inputs without executing anything."""

    issues: list[str] = []
    if closed_frame.get("valid") is not True:
        issues.append("closed ResultFrame must be valid")
    if not str(closed_frame.get("sql_ref") or "").startswith("sql:"):
        issues.append("closed ResultFrame must expose a typed sql_ref")
    if closed_frame.get("missing_count", 0) != 0:
        issues.append("closed ResultFrame must have zero missing refs")
    if closed_frame.get("executes_runtime") is not False:
        issues.append("OpenRC readiness input must be non-runtime")
    if github_handoff.get("valid") is not True:
        issues.append("GitHub scan-once handoff must be valid")
    if github_handoff.get("scan_once") is not True:
        issues.append("GitHub handoff must be scan-once")
    if github_handoff.get("remote_mutation_allowed") is not False:
        issues.append("GitHub handoff must not allow remote mutation")
    if not request.service_name or "/" in request.service_name or " " in request.service_name:
        issues.append("service_name must be a simple OpenRC service name")
    if request.install_service:
        issues.append("install_service is forbidden in 0268")
    if request.start_service:
        issues.append("start_service is forbidden in 0268")
    if request.enable_service:
        issues.append("enable_service is forbidden in 0268")
    return tuple(issues)


def render_openrc_script(spec: OpenRcLauncherServiceSpec) -> str:
    """Render an OpenRC service file as text only."""

    need = " ".join(spec.depends_need)
    after = " ".join(spec.depends_after)
    environment = "\n".join(
        f'export {key}="{value}"' for key, value in spec.extra_environment
    )
    env_block = f"\n{environment}\n" if environment else ""
    return (
        "#!/sbin/openrc-run\n"
        f'description="{spec.description}"\n'
        f'command="{spec.command}"\n'
        f'command_user="{spec.command_user}"\n'
        'command_background="yes"\n'
        f'pidfile="{spec.pidfile}"\n'
        f"{env_block}"
        "depend() {\n"
        f"    need {need}\n"
        f"    after {after}\n"
        "}\n"
    )


def _readiness_ref(
    request: OpenRcLauncherMinimalReadinessRequest,
    closed_frame: Mapping[str, Any],
    github_handoff: Mapping[str, Any],
) -> str:
    digest = hashlib.sha256()
    digest.update(request.service_name.encode("utf-8"))
    digest.update(b"\0")
    digest.update(str(closed_frame.get("sql_ref") or "").encode("utf-8"))
    digest.update(b"\0")
    digest.update(str(github_handoff.get("handoff_ref") or "").encode("utf-8"))
    return "openrc-launcher-readiness:" + digest.hexdigest()[:16]


def build_openrc_launcher_minimal_readiness(
    *,
    closed_frame: Mapping[str, Any],
    github_handoff: Mapping[str, Any],
    request: OpenRcLauncherMinimalReadinessRequest,
    source_reports: Mapping[str, str],
) -> OpenRcLauncherMinimalReadinessReport:
    """Build a readiness-only OpenRC launcher envelope."""

    issues = validate_openrc_readiness_inputs(
        closed_frame=closed_frame,
        github_handoff=github_handoff,
        request=request,
    )
    spec = OpenRcLauncherServiceSpec(service_name=request.service_name)
    checks = {
        "closed_frame_valid": closed_frame.get("valid") is True,
        "github_handoff_valid": github_handoff.get("valid") is True,
        "github_scan_once": github_handoff.get("scan_once") is True,
        "remote_mutation_disabled": github_handoff.get("remote_mutation_allowed") is False,
        "scheduler_run_unchanged": True,
        "no_service_start": not request.start_service,
        "no_service_enable": not request.enable_service,
        "no_service_install": not request.install_service,
    }
    return OpenRcLauncherMinimalReadinessReport(
        valid=not issues,
        issues=issues,
        request=request,
        readiness_ref="" if issues else _readiness_ref(request, closed_frame, github_handoff),
        service_spec=spec,
        rendered_openrc_script=render_openrc_script(spec),
        source_reports=source_reports,
        closed_frame_summary={
            "sql_ref": closed_frame.get("sql_ref", ""),
            "embedding_ref": closed_frame.get("embedding_ref", ""),
            "hydrated_count": closed_frame.get("hydrated_count", 0),
            "missing_count": closed_frame.get("missing_count", 0),
        },
        github_handoff_summary={
            "handoff_ref": github_handoff.get("handoff_ref", ""),
            "repository": github_handoff.get("request", {}).get("repository", "")
            if isinstance(github_handoff.get("request"), Mapping)
            else "",
            "scan_once": github_handoff.get("scan_once", False),
            "remote_mutation_allowed": github_handoff.get("remote_mutation_allowed", True),
        },
        checks=checks,
    )


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def write_report(output: Path, payload: Mapping[str, Any]) -> None:
    """Write a JSON report."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
