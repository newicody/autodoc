"""Scheduler-owned runtime registry built from the 0256 reuse source map.

This module turns the filtered source map into a Scheduler-owned component
registry plan.  It does not instantiate components and it does not create a new
runtime manager.  Scheduler remains the owner of runtime components.

The registry references existing implementation surfaces so the following
patches can adapt and execute them without reinventing a separate component
stack or creating one production CLI per component.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


DEFAULT_LIFECYCLE: tuple[str, ...] = (
    "validate",
    "instantiate_by_scheduler",
    "start_by_scheduler",
    "health_by_scheduler",
    "stop_by_scheduler",
)


CANONICAL_COMPONENT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "component_id": "eventbus",
        "surface": "eventbus",
        "role": "observation",
        "capabilities": ("eventbus.publish_fact", "eventbus.subscribe_fact"),
        "depends_on": (),
        "canonical_paths": ("src/kernel/event_bus.py",),
    },
    {
        "component_id": "passive_supervisor_sink",
        "surface": "passive_supervisor",
        "role": "observation",
        "capabilities": ("supervisor.observe", "supervisor.visual_read_model"),
        "depends_on": ("eventbus",),
        "canonical_paths": (
            "src/context/passive_bus_supervisor_cellular_snapshot.py",
            "src/context/passive_supervisor_visual_layout_model.py",
            "src/context/passive_supervisor_visual_pipeline_0238.py",
        ),
    },
    {
        "component_id": "sql_context_store",
        "surface": "sql_context_store",
        "role": "command",
        "capabilities": ("sql.context.write", "sql.context.rehydrate"),
        "depends_on": (),
        "canonical_paths": (
            "tools/run_sql_context_store_controlled_write_smoke.py",
        ),
    },
    {
        "component_id": "openvino_embedding_service",
        "surface": "openvino_embedding",
        "role": "command",
        "capabilities": ("embedding.openvino.passage", "embedding.openvino.query"),
        "depends_on": (),
        "canonical_paths": (
            "tools/run_openvino_e5_live_smoke.py",
            "tools/embed_e5.py",
        ),
    },
    {
        "component_id": "qdrant_projection_store",
        "surface": "qdrant_projection",
        "role": "command",
        "capabilities": (
            "qdrant.collection.ensure",
            "qdrant.projection.upsert",
            "qdrant.recall",
        ),
        "depends_on": ("sql_context_store", "openvino_embedding_service"),
        "canonical_paths": (
            "tools/run_qdrant_projection_live_smoke.py",
            "tools/run_qdrant_live_recall_sql_rehydrate_smoke.py",
            "tools/run_qdrant_recall_sql_rehydrate_smoke.py",
        ),
    },
    {
        "component_id": "github_artifact_exchange",
        "surface": "github_artifact_exchange",
        "role": "command",
        "capabilities": ("github.artifact.scan_once", "github.project_push_frame.build"),
        "depends_on": (),
        "canonical_paths": (
            "src/context/github_artifact_scheduler_intake.py",
            "src/context/github_project_push_frame.py",
            "src/context/github_action_ticket_artifact.py",
        ),
    },
)


@dataclass(frozen=True)
class SchedulerOwnedRuntimeComponentRegistration:
    """One Scheduler-owned runtime component registration."""

    component_id: str
    surface: str
    owner: str
    role: str
    capabilities: tuple[str, ...]
    depends_on: tuple[str, ...]
    source_paths: tuple[str, ...]
    lifecycle: tuple[str, ...] = DEFAULT_LIFECYCLE
    runtime_api_kind: str = "scheduler_owned_object"
    selected_from_existing_surfaces: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "surface": self.surface,
            "owner": self.owner,
            "role": self.role,
            "capabilities": list(self.capabilities),
            "depends_on": list(self.depends_on),
            "source_paths": list(self.source_paths),
            "lifecycle": list(self.lifecycle),
            "runtime_api_kind": self.runtime_api_kind,
            "selected_from_existing_surfaces": self.selected_from_existing_surfaces,
        }


@dataclass(frozen=True)
class SchedulerOwnedRuntimeRegistry:
    """Registry plan owned by Scheduler, derived from existing source surfaces."""

    registrations: tuple[SchedulerOwnedRuntimeComponentRegistration, ...]
    source_map_complete: bool
    owner: str = "scheduler"
    launcher_bootstrap_only: bool = True
    eventbus_observation_only: bool = True
    no_cli_per_component: bool = True
    creates_runtime_manager: bool = False
    instantiates_components: bool = False

    def to_dict(self) -> dict[str, Any]:
        issues = validate_scheduler_owned_runtime_registry(self)
        return {
            "scheduler_owned_runtime_registry": True,
            "valid": not issues,
            "issues": list(issues),
            "owner": self.owner,
            "source_map_complete": self.source_map_complete,
            "launcher_bootstrap_only": self.launcher_bootstrap_only,
            "eventbus_observation_only": self.eventbus_observation_only,
            "no_cli_per_component": self.no_cli_per_component,
            "creates_runtime_manager": self.creates_runtime_manager,
            "instantiates_components": self.instantiates_components,
            "registrations": [registration.to_dict() for registration in self.registrations],
        }


def _selection_index(source_map_payload: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not source_map_payload:
        return {}
    return {
        str(selection.get("surface")): dict(selection)
        for selection in source_map_payload.get("selections", [])
        if selection.get("surface")
    }


def _candidate_paths(selection: Mapping[str, Any] | None) -> tuple[str, ...]:
    if not selection:
        return ()
    primary = tuple(str(path) for path in selection.get("primary_paths", ()) if path)
    hits = tuple(
        str(hit.get("path"))
        for hit in selection.get("hits", ())
        if isinstance(hit, Mapping) and hit.get("path")
    )
    result: list[str] = []
    for path in primary + hits:
        if path not in result:
            result.append(path)
    return tuple(result)


def _select_source_paths(
    canonical_paths: Sequence[str],
    selection: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    candidates = _candidate_paths(selection)
    selected: list[str] = []

    for canonical in canonical_paths:
        if canonical in candidates:
            selected.append(canonical)

    if not selected:
        for candidate in candidates:
            if candidate.startswith(("src/", "tools/")) and candidate not in selected:
                selected.append(candidate)
            if len(selected) >= 3:
                break

    for canonical in canonical_paths:
        if canonical not in selected:
            selected.append(canonical)

    return tuple(selected[:5])


def build_scheduler_owned_runtime_registry(
    source_map_payload: Mapping[str, Any] | None = None,
) -> SchedulerOwnedRuntimeRegistry:
    """Build a Scheduler-owned registry plan from the 0256 source map payload."""

    selections = _selection_index(source_map_payload)
    registrations: list[SchedulerOwnedRuntimeComponentRegistration] = []

    for spec in CANONICAL_COMPONENT_SPECS:
        surface = str(spec["surface"])
        selected_paths = _select_source_paths(
            tuple(spec["canonical_paths"]),
            selections.get(surface),
        )
        registrations.append(
            SchedulerOwnedRuntimeComponentRegistration(
                component_id=str(spec["component_id"]),
                surface=surface,
                owner="scheduler",
                role=str(spec["role"]),
                capabilities=tuple(str(capability) for capability in spec["capabilities"]),
                depends_on=tuple(str(dependency) for dependency in spec["depends_on"]),
                source_paths=selected_paths,
            )
        )

    return SchedulerOwnedRuntimeRegistry(
        registrations=tuple(registrations),
        source_map_complete=bool(source_map_payload.get("complete", False)) if source_map_payload else False,
    )


def validate_scheduler_owned_runtime_registry(
    registry: SchedulerOwnedRuntimeRegistry,
) -> tuple[str, ...]:
    """Validate Scheduler-owned runtime registry boundaries."""

    issues: list[str] = []
    if registry.owner != "scheduler":
        issues.append("registry owner must be scheduler")
    if not registry.launcher_bootstrap_only:
        issues.append("launcher must remain bootstrap-only")
    if not registry.eventbus_observation_only:
        issues.append("EventBus must remain observation-only")
    if not registry.no_cli_per_component:
        issues.append("runtime API must keep no CLI per component")
    if registry.creates_runtime_manager:
        issues.append("must not create a RuntimeManager")
    if registry.instantiates_components:
        issues.append("0257 must not instantiate components")
    registrations = {item.component_id: item for item in registry.registrations}
    required = {
        "eventbus",
        "passive_supervisor_sink",
        "sql_context_store",
        "openvino_embedding_service",
        "qdrant_projection_store",
        "github_artifact_exchange",
    }
    missing = sorted(required.difference(registrations))
    for component_id in missing:
        issues.append(f"missing component registration {component_id}")
    for registration in registry.registrations:
        if registration.owner != "scheduler":
            issues.append(f"{registration.component_id} must be owned by scheduler")
        if not registration.source_paths:
            issues.append(f"{registration.component_id} must reference existing source paths")
        if registration.runtime_api_kind != "scheduler_owned_object":
            issues.append(f"{registration.component_id} must not expose a component CLI runtime API")
        for dependency in registration.depends_on:
            if dependency not in registrations:
                issues.append(f"{registration.component_id} depends on missing {dependency}")
    qdrant = registrations.get("qdrant_projection_store")
    if qdrant and qdrant.depends_on != ("sql_context_store", "openvino_embedding_service"):
        issues.append("qdrant_projection_store must depend on SQL and OpenVINO components")
    supervisor = registrations.get("passive_supervisor_sink")
    if supervisor and supervisor.depends_on != ("eventbus",):
        issues.append("passive_supervisor_sink must depend only on EventBus")
    return tuple(issues)


def load_source_map_payload(path: Path) -> dict[str, Any]:
    """Load a 0256 source-map report."""

    return json.loads(path.read_text(encoding="utf-8"))


def write_scheduler_owned_runtime_registry_report(
    output: Path,
    source_map_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Write the Scheduler-owned runtime registry report."""

    registry = build_scheduler_owned_runtime_registry(source_map_payload)
    payload = registry.to_dict()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
