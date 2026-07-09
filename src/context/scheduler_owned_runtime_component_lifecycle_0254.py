"""Scheduler-owned runtime component lifecycle model.

This module fixes the production runtime ownership boundary:

OpenRC -> launcher -> Scheduler -> runtime components

OpenRC supervises the process.  The launcher performs the minimal bootstrap
needed to hand the production server configuration to the Scheduler.  The
Scheduler owns runtime component instantiation and lifecycle management.

The module is intentionally small and stdlib-only.  It does not start runtime
objects, import factories, open SQL/Qdrant/OpenVINO/GitHub connections, publish
events, or replace the existing Scheduler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEDULER_LIFECYCLE_AUTHORITY: dict[str, bool] = {
    "openrc_supervises_process": True,
    "launcher_bootstrap_only": True,
    "scheduler_owns_runtime_components": True,
    "scheduler_manages_component_lifecycle": True,
    "eventbus_observation_only": True,
    "no_cli_per_component_runtime_api": True,
    "no_parallel_orchestrator": True,
    "uses_scheduler_run": False,
    "imports_factories": False,
    "starts_components": False,
    "writes_sql": False,
    "writes_qdrant": False,
    "calls_github_api": False,
    "runs_openvino_inference": False,
}


DEFAULT_SCHEDULER_MANAGED_COMPONENTS: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("eventbus", "observation", ("eventbus.publish_fact",), ()),
    ("passive_supervisor_sink", "observation", ("supervisor.observe",), ("eventbus",)),
    ("sql_context_store", "command", ("sql.context.write", "sql.context.rehydrate"), ()),
    ("openvino_embedding_service", "command", ("embedding.openvino.query", "embedding.openvino.passage"), ()),
    ("qdrant_projection_store", "command", ("qdrant.projection.upsert", "qdrant.recall"), ("sql_context_store", "openvino_embedding_service")),
    ("github_artifact_exchange", "command", ("github.artifact.scan_once",), ()),
)


@dataclass(frozen=True)
class SchedulerManagedComponentSpec:
    """Declarative runtime component description owned by Scheduler."""

    component_id: str
    role: str
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    depends_on: tuple[str, ...] = field(default_factory=tuple)
    lifecycle: tuple[str, ...] = ("validate", "instantiate", "start", "health", "stop")

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "role": self.role,
            "capabilities": list(self.capabilities),
            "depends_on": list(self.depends_on),
            "lifecycle": list(self.lifecycle),
            "owner": "scheduler",
        }


@dataclass(frozen=True)
class SchedulerOwnedRuntimeLifecycle:
    """Serializable model for Scheduler-owned runtime lifecycle."""

    bootstrap_path: tuple[str, ...]
    authority: Mapping[str, bool]
    components: tuple[SchedulerManagedComponentSpec, ...]
    execution_phase_opened: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "scheduler_owned_runtime_component_lifecycle": True,
            "execution_phase_opened": self.execution_phase_opened,
            "bootstrap_path": list(self.bootstrap_path),
            "authority": dict(self.authority),
            "components": [component.to_dict() for component in self.components],
            "component_count": len(self.components),
        }


def default_scheduler_managed_components() -> tuple[SchedulerManagedComponentSpec, ...]:
    """Return the production runtime components that Scheduler owns."""

    return tuple(
        SchedulerManagedComponentSpec(
            component_id=component_id,
            role=role,
            capabilities=tuple(capabilities),
            depends_on=tuple(depends_on),
        )
        for component_id, role, capabilities, depends_on in DEFAULT_SCHEDULER_MANAGED_COMPONENTS
    )


def _component_ids(components: Sequence[SchedulerManagedComponentSpec]) -> set[str]:
    return {component.component_id for component in components}


def validate_scheduler_owned_lifecycle(
    lifecycle: SchedulerOwnedRuntimeLifecycle,
) -> tuple[str, ...]:
    """Validate Scheduler ownership and dependency shape."""

    issues: list[str] = []
    bootstrap = tuple(lifecycle.bootstrap_path)
    if bootstrap != ("OpenRC", "launcher", "Scheduler"):
        issues.append("bootstrap path must be OpenRC -> launcher -> Scheduler")
    authority = dict(lifecycle.authority)
    if not authority.get("scheduler_owns_runtime_components", False):
        issues.append("Scheduler must own runtime components")
    if not authority.get("launcher_bootstrap_only", False):
        issues.append("launcher must remain bootstrap-only")
    if not authority.get("eventbus_observation_only", False):
        issues.append("EventBus must remain observation-only")
    if not authority.get("no_cli_per_component_runtime_api", False):
        issues.append("runtime API must not become one CLI per component")
    if authority.get("starts_components", False):
        issues.append("this model must not start components")
    ids = _component_ids(lifecycle.components)
    if "eventbus" not in ids:
        issues.append("eventbus component is required")
    if "sql_context_store" not in ids:
        issues.append("sql_context_store component is required")
    if "openvino_embedding_service" not in ids:
        issues.append("openvino_embedding_service component is required")
    if "qdrant_projection_store" not in ids:
        issues.append("qdrant_projection_store component is required")
    for component in lifecycle.components:
        for dependency in component.depends_on:
            if dependency not in ids:
                issues.append(f"{component.component_id} depends on missing {dependency}")
    return tuple(issues)


def build_scheduler_owned_runtime_lifecycle(
    components: Iterable[SchedulerManagedComponentSpec] | None = None,
) -> SchedulerOwnedRuntimeLifecycle:
    """Build the Scheduler-owned runtime lifecycle model."""

    component_tuple = tuple(components) if components is not None else default_scheduler_managed_components()
    return SchedulerOwnedRuntimeLifecycle(
        bootstrap_path=("OpenRC", "launcher", "Scheduler"),
        authority=dict(SCHEDULER_LIFECYCLE_AUTHORITY),
        components=component_tuple,
    )


def write_scheduler_owned_runtime_lifecycle_report(path: Path) -> dict[str, Any]:
    """Write the lifecycle model report as JSON."""

    lifecycle = build_scheduler_owned_runtime_lifecycle()
    issues = validate_scheduler_owned_lifecycle(lifecycle)
    payload = lifecycle.to_dict()
    payload["valid"] = not issues
    payload["issues"] = list(issues)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
