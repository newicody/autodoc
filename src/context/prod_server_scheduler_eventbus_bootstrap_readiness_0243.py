"""Scheduler/EventBus bootstrap readiness for phase 0243.

This module checks whether the validated production server INI and component
registry are ready to bootstrap the core Scheduler/EventBus pair.

It deliberately does not import factory modules, call factories, instantiate
Scheduler/EventBus, start OpenRC, start threads, publish EventBus events, call
GitHub, or mutate PostgreSQL/Qdrant.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from context.prod_server_component_registry_0242 import build_component_registry


BOOTSTRAP_READINESS_VERSION = "0243.r1"


BOOTSTRAP_READINESS_BOUNDARY: dict[str, bool] = {
    "readiness_only": True,
    "uses_validated_registry": True,
    "imports_factory_modules": False,
    "calls_factories": False,
    "creates_scheduler": False,
    "creates_eventbus": False,
    "starts_openrc": False,
    "starts_threads": False,
    "publishes_events": False,
    "calls_github_api": False,
    "writes_postgresql": False,
    "writes_qdrant": False,
    "requires_non_stdlib": False,
}


@dataclass(frozen=True)
class BootstrapReadinessIssue:
    """One issue preventing Scheduler/EventBus bootstrap readiness."""

    component_id: str
    field: str
    message: str


@dataclass(frozen=True)
class BootstrapComponent:
    """One core component required for the bootstrap pair."""

    component_id: str
    factory: str
    phase: str
    command_path: bool
    observation_path: bool
    dependency_position: int


@dataclass(frozen=True)
class BootstrapReadinessReport:
    """JSON-compatible bootstrap readiness report."""

    version: str
    config_path: str
    ready: bool
    core_components: tuple[BootstrapComponent, ...]
    dependency_order: tuple[str, ...]
    issues: tuple[BootstrapReadinessIssue, ...]


def _entry_map(report: Any) -> dict[str, Any]:
    return {entry.component_id: entry for entry in report.entries}


def build_bootstrap_readiness(config_path: Path) -> BootstrapReadinessReport:
    """Build a readiness report for the Scheduler/EventBus bootstrap pair."""

    registry = build_component_registry(config_path)
    issues: list[BootstrapReadinessIssue] = []
    entries = _entry_map(registry)

    if not registry.valid:
        for issue in registry.issues:
            issues.append(
                BootstrapReadinessIssue(
                    issue.component_id,
                    issue.field,
                    issue.message,
                )
            )

    for component_id in ("eventbus", "scheduler"):
        if component_id not in entries:
            issues.append(
                BootstrapReadinessIssue(component_id, "component", "missing core component")
            )
            continue
        entry = entries[component_id]
        if not entry.enabled:
            issues.append(BootstrapReadinessIssue(component_id, "enabled", "must be enabled"))

    if "scheduler" in entries:
        scheduler = entries["scheduler"]
        if not scheduler.command_path:
            issues.append(BootstrapReadinessIssue("scheduler", "command_path", "must be true"))
        if scheduler.observation_path:
            issues.append(BootstrapReadinessIssue("scheduler", "observation_path", "must be false"))

    if "eventbus" in entries:
        eventbus = entries["eventbus"]
        if eventbus.command_path:
            issues.append(BootstrapReadinessIssue("eventbus", "command_path", "must be false"))
        if not eventbus.observation_path:
            issues.append(BootstrapReadinessIssue("eventbus", "observation_path", "must be true"))

    ordered_components = registry.ordered_components
    for component_id in ("eventbus", "scheduler"):
        if component_id not in ordered_components:
            issues.append(
                BootstrapReadinessIssue(
                    component_id,
                    "dependency_order",
                    "must be present in dependency order",
                )
            )

    core_components: list[BootstrapComponent] = []
    for component_id in ("eventbus", "scheduler"):
        entry = entries.get(component_id)
        if entry is None:
            continue
        position = ordered_components.index(component_id) if component_id in ordered_components else -1
        core_components.append(
            BootstrapComponent(
                component_id=component_id,
                factory=entry.factory,
                phase=entry.phase,
                command_path=entry.command_path,
                observation_path=entry.observation_path,
                dependency_position=position,
            )
        )

    return BootstrapReadinessReport(
        version=BOOTSTRAP_READINESS_VERSION,
        config_path=str(config_path),
        ready=not issues,
        core_components=tuple(core_components),
        dependency_order=ordered_components,
        issues=tuple(issues),
    )


def readiness_to_dict(report: BootstrapReadinessReport) -> dict[str, Any]:
    """Convert a readiness report to JSON-compatible data."""

    return asdict(report)


def write_bootstrap_readiness_report(*, config_path: Path, output_path: Path) -> dict[str, Any]:
    """Build and write the Scheduler/EventBus bootstrap readiness report."""

    report = build_bootstrap_readiness(config_path)
    payload = {
        "production_server_scheduler_eventbus_bootstrap_readiness_written": True,
        "readiness": readiness_to_dict(report),
        "boundary": dict(BOOTSTRAP_READINESS_BOUNDARY),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    return payload
