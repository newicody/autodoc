"""OpenRC launcher surface validation for phase 0244.

This module validates a proposed OpenRC init script for the production server
launcher. It checks that the service exposes configtest/start/stop/status shape
without installing the service, calling OpenRC, starting the launcher, or
creating runtime components.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from context.prod_server_scheduler_eventbus_bootstrap_readiness_0243 import (
    build_bootstrap_readiness,
)


OPENRC_LAUNCHER_SURFACE_VERSION = "0244.r1"


OPENRC_LAUNCHER_SURFACE_BOUNDARY: dict[str, bool] = {
    "validation_only": True,
    "uses_bootstrap_readiness": True,
    "installs_openrc_service": False,
    "calls_openrc": False,
    "starts_launcher": False,
    "creates_scheduler": False,
    "creates_eventbus": False,
    "starts_threads": False,
    "publishes_events": False,
    "calls_github_api": False,
    "writes_postgresql": False,
    "writes_qdrant": False,
    "requires_non_stdlib": False,
}


REQUIRED_SNIPPETS: tuple[str, ...] = (
    "#!/sbin/openrc-run",
    "description=",
    "command=",
    "command_args=",
    "pidfile=",
    "depend()",
    "need postgresql qdrant",
    "configtest()",
    "start_pre()",
    "--configtest",
    "supervisor=supervise-daemon",
)


@dataclass(frozen=True)
class OpenRCSurfaceIssue:
    """One issue in the proposed OpenRC launcher surface."""

    field: str
    message: str


@dataclass(frozen=True)
class OpenRCSurfaceReport:
    """JSON-compatible OpenRC launcher surface report."""

    version: str
    config_path: str
    initd_path: str
    valid: bool
    bootstrap_ready: bool
    service_name: str
    expected_commands: tuple[str, ...]
    issues: tuple[OpenRCSurfaceIssue, ...]


def read_initd(path: Path) -> str:
    """Read an OpenRC init script as text."""

    return path.read_text(encoding="utf-8")


def validate_openrc_surface(*, config_path: Path, initd_path: Path) -> OpenRCSurfaceReport:
    """Validate the OpenRC launcher surface without installing or starting it."""

    readiness = build_bootstrap_readiness(config_path)
    text = read_initd(initd_path)
    issues: list[OpenRCSurfaceIssue] = []

    if not readiness.ready:
        issues.append(OpenRCSurfaceIssue("bootstrap_readiness", "Scheduler/EventBus readiness must pass first"))

    for snippet in REQUIRED_SNIPPETS:
        if snippet not in text:
            issues.append(OpenRCSurfaceIssue("initd", f"missing snippet: {snippet}"))

    if "rc-service" in text:
        issues.append(OpenRCSurfaceIssue("initd", "must not call rc-service recursively"))
    if "GITHUB_TOKEN=" in text:
        issues.append(OpenRCSurfaceIssue("initd", "must not embed GITHUB_TOKEN value"))
    if "autodoc.launcher" not in text:
        issues.append(OpenRCSurfaceIssue("command", "launcher module must be explicit"))
    if "/etc/autodoc/autodoc.ini" not in text:
        issues.append(OpenRCSurfaceIssue("command_args", "production config path must be explicit"))

    return OpenRCSurfaceReport(
        version=OPENRC_LAUNCHER_SURFACE_VERSION,
        config_path=str(config_path),
        initd_path=str(initd_path),
        valid=not issues,
        bootstrap_ready=readiness.ready,
        service_name="autodoc",
        expected_commands=("configtest", "start", "stop", "status"),
        issues=tuple(issues),
    )


def openrc_surface_to_dict(report: OpenRCSurfaceReport) -> dict[str, Any]:
    """Convert an OpenRC surface report to JSON-compatible data."""

    return asdict(report)


def write_openrc_surface_report(*, config_path: Path, initd_path: Path, output_path: Path) -> dict[str, Any]:
    """Validate and write the OpenRC launcher surface report."""

    report = validate_openrc_surface(config_path=config_path, initd_path=initd_path)
    payload = {
        "production_server_openrc_launcher_surface_written": True,
        "openrc_surface": openrc_surface_to_dict(report),
        "boundary": dict(OPENRC_LAUNCHER_SURFACE_BOUNDARY),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    return payload
