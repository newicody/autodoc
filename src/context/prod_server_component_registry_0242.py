"""Production server component registry for phase 0242.

The registry is a declarative table built from the validated production server
INI. It records component ids, factory references, phases, dependency order, and
command/observation roles.

This module does not import component factory modules, call factories,
instantiate Scheduler/EventBus, start OpenRC, start threads, publish events,
call GitHub, or mutate PostgreSQL/Qdrant.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from context.prod_server_ini_validation_0241 import load_ini, validate_ini_file


COMPONENT_REGISTRY_VERSION = "0242.r1"


COMPONENT_REGISTRY_BOUNDARY: dict[str, bool] = {
    "registry_only": True,
    "validates_ini_first": True,
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


FACTORY_REF_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*$")


COMMAND_COMPONENTS = frozenset(
    {
        "scheduler",
        "sql_context_store",
        "qdrant_projection",
        "github_artifact_exchange",
    }
)
OBSERVATION_COMPONENTS = frozenset({"eventbus", "passive_supervisor_sink"})
DEFAULT_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "sql_context_store": ("scheduler",),
    "qdrant_projection": ("sql_context_store",),
    "github_artifact_exchange": ("scheduler", "sql_context_store"),
    "passive_supervisor_sink": ("eventbus",),
}


@dataclass(frozen=True)
class ComponentRegistryIssue:
    """One registry issue found while reading component sections."""

    component_id: str
    field: str
    message: str


@dataclass(frozen=True)
class ComponentRegistryEntry:
    """One declarative component registry entry."""

    component_id: str
    factory: str
    phase: str
    enabled: bool
    depends_on: tuple[str, ...]
    command_path: bool
    observation_path: bool


@dataclass(frozen=True)
class ComponentRegistryReport:
    """JSON-compatible component registry report."""

    version: str
    config_path: str
    valid: bool
    ordered_components: tuple[str, ...]
    entries: tuple[ComponentRegistryEntry, ...]
    issues: tuple[ComponentRegistryIssue, ...]


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _component_id_from_section(section: str) -> str:
    return section.removeprefix("component.")


def _component_sections(parser: Any) -> tuple[str, ...]:
    return tuple(section for section in parser.sections() if section.startswith("component."))


def _entry_from_section(parser: Any, section: str) -> tuple[ComponentRegistryEntry | None, tuple[ComponentRegistryIssue, ...]]:
    component_id = _component_id_from_section(section)
    issues: list[ComponentRegistryIssue] = []

    factory = parser.get(section, "factory", fallback="")
    phase = parser.get(section, "phase", fallback="")
    enabled = parser.getboolean(section, "enabled", fallback=False)
    depends_on = _split_csv(parser.get(section, "depends_on", fallback=""))
    if not depends_on:
        depends_on = DEFAULT_DEPENDENCIES.get(component_id, ())

    if not factory:
        issues.append(ComponentRegistryIssue(component_id, "factory", "missing factory reference"))
    elif not FACTORY_REF_RE.match(factory):
        issues.append(ComponentRegistryIssue(component_id, "factory", "must use module:function syntax"))

    if not phase:
        issues.append(ComponentRegistryIssue(component_id, "phase", "missing phase"))

    if issues:
        return None, tuple(issues)

    return (
        ComponentRegistryEntry(
            component_id=component_id,
            factory=factory,
            phase=phase,
            enabled=enabled,
            depends_on=depends_on,
            command_path=component_id in COMMAND_COMPONENTS,
            observation_path=component_id in OBSERVATION_COMPONENTS,
        ),
        tuple(),
    )


def dependency_order(entries: tuple[ComponentRegistryEntry, ...]) -> tuple[tuple[str, ...], tuple[ComponentRegistryIssue, ...]]:
    """Return dependency order for enabled entries without instantiating them."""

    enabled_entries = {entry.component_id: entry for entry in entries if entry.enabled}
    issues: list[ComponentRegistryIssue] = []

    for entry in enabled_entries.values():
        for dependency in entry.depends_on:
            if dependency not in enabled_entries:
                issues.append(
                    ComponentRegistryIssue(
                        entry.component_id,
                        "depends_on",
                        f"unknown or disabled dependency {dependency}",
                    )
                )

    ordered: list[str] = []
    remaining = set(enabled_entries)
    while remaining:
        ready = sorted(
            component_id
            for component_id in remaining
            if all(dependency in ordered for dependency in enabled_entries[component_id].depends_on)
        )
        if not ready:
            cycle = ",".join(sorted(remaining))
            issues.append(ComponentRegistryIssue("*", "depends_on", f"dependency cycle {cycle}"))
            break
        ordered.extend(ready)
        remaining.difference_update(ready)

    return tuple(ordered), tuple(issues)


def build_component_registry(config_path: Path) -> ComponentRegistryReport:
    """Build the declarative component registry from a validated INI file."""

    ini_validation = validate_ini_file(config_path)
    parser = load_ini(config_path)

    entries: list[ComponentRegistryEntry] = []
    issues: list[ComponentRegistryIssue] = []

    if not ini_validation.valid:
        for issue in ini_validation.issues:
            issues.append(ComponentRegistryIssue(issue.section, issue.key, issue.message))

    for section in _component_sections(parser):
        entry, section_issues = _entry_from_section(parser, section)
        issues.extend(section_issues)
        if entry is not None:
            entries.append(entry)

    ordered_components, dependency_issues = dependency_order(tuple(entries))
    issues.extend(dependency_issues)

    return ComponentRegistryReport(
        version=COMPONENT_REGISTRY_VERSION,
        config_path=str(config_path),
        valid=not issues,
        ordered_components=ordered_components,
        entries=tuple(entries),
        issues=tuple(issues),
    )


def registry_to_dict(report: ComponentRegistryReport) -> dict[str, Any]:
    """Convert a registry report to JSON-compatible data."""

    return asdict(report)


def write_component_registry_report(*, config_path: Path, output_path: Path) -> dict[str, Any]:
    """Build and write the component registry report."""

    report = build_component_registry(config_path)
    payload = {
        "production_server_component_registry_written": True,
        "registry": registry_to_dict(report),
        "boundary": dict(COMPONENT_REGISTRY_BOUNDARY),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    return payload
