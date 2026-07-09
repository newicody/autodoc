"""Attach the Scheduler-owned runtime registry to Scheduler bootstrap.

0258 is the first adaptation patch after the reuse map and registry.  It keeps
the corrected ownership boundary:

OpenRC -> launcher -> Scheduler -> runtime registry -> runtime components

The launcher remains bootstrap-only.  Scheduler owns the registry attachment and
the future component lifecycle.  This module does not modify Scheduler.run, does
not instantiate runtime components, and does not start SQL/OpenVINO/Qdrant/GitHub.

The attachment is deliberately a small stdlib-only helper around an existing
Scheduler object.  It does not create a RuntimeManager or a parallel
orchestrator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Sequence


SCHEDULER_RUNTIME_REGISTRY_ATTRIBUTE = "_autodoc_scheduler_owned_runtime_registry_0258"
SCHEDULER_RUNTIME_BOOTSTRAP_ATTRIBUTE = "_autodoc_scheduler_runtime_bootstrap_0258"


@dataclass(frozen=True)
class SchedulerRuntimeBootstrapAttachment:
    """Serializable record of a registry attachment owned by Scheduler."""

    scheduler_ref: str
    registry_component_ids: tuple[str, ...]
    capability_index: Mapping[str, str]
    dependency_index: Mapping[str, tuple[str, ...]]
    lifecycle_steps: tuple[str, ...] = (
        "validate_registry",
        "attach_registry_to_scheduler",
        "prepare_scheduler_owned_lifecycle",
    )
    owner: str = "scheduler"
    launcher_bootstrap_only: bool = True
    eventbus_observation_only: bool = True
    no_cli_per_component: bool = True
    modifies_scheduler_run: bool = False
    instantiates_components: bool = False
    starts_components: bool = False
    creates_runtime_manager: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "scheduler_ref": self.scheduler_ref,
            "owner": self.owner,
            "registry_component_ids": list(self.registry_component_ids),
            "capability_index": dict(self.capability_index),
            "dependency_index": {
                key: list(value)
                for key, value in self.dependency_index.items()
            },
            "lifecycle_steps": list(self.lifecycle_steps),
            "launcher_bootstrap_only": self.launcher_bootstrap_only,
            "eventbus_observation_only": self.eventbus_observation_only,
            "no_cli_per_component": self.no_cli_per_component,
            "modifies_scheduler_run": self.modifies_scheduler_run,
            "instantiates_components": self.instantiates_components,
            "starts_components": self.starts_components,
            "creates_runtime_manager": self.creates_runtime_manager,
        }


@dataclass(frozen=True)
class SchedulerRuntimeBootstrapResult:
    """Result for Scheduler-owned runtime bootstrap registry attachment."""

    valid: bool
    issues: tuple[str, ...]
    attachment: SchedulerRuntimeBootstrapAttachment
    registry_payload_digest: str = ""
    attached_to_scheduler_object: bool = False
    dry_run: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "scheduler_runtime_bootstrap_registry_attachment": True,
            "valid": self.valid,
            "issues": list(self.issues),
            "registry_payload_digest": self.registry_payload_digest,
            "attached_to_scheduler_object": self.attached_to_scheduler_object,
            "dry_run": self.dry_run,
            "attachment": self.attachment.to_dict(),
        }


def _stable_digest(payload: Mapping[str, Any]) -> str:
    import hashlib

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _scheduler_ref(scheduler: object | None) -> str:
    if scheduler is None:
        return "scheduler:dry-run"
    return f"{scheduler.__class__.__module__}.{scheduler.__class__.__qualname__}:{id(scheduler)}"


def _registrations(registry_payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        registration
        for registration in registry_payload.get("registrations", ())
        if isinstance(registration, Mapping)
    )


def _build_capability_index(registrations: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    index: dict[str, str] = {}
    for registration in registrations:
        component_id = str(registration.get("component_id", ""))
        for capability in registration.get("capabilities", ()):
            capability_text = str(capability)
            if capability_text:
                index[capability_text] = component_id
    return index


def _build_dependency_index(registrations: Sequence[Mapping[str, Any]]) -> dict[str, tuple[str, ...]]:
    index: dict[str, tuple[str, ...]] = {}
    for registration in registrations:
        component_id = str(registration.get("component_id", ""))
        if component_id:
            index[component_id] = tuple(str(dep) for dep in registration.get("depends_on", ()))
    return index


def validate_scheduler_runtime_bootstrap_attachment(
    registry_payload: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate that a 0257 registry can be attached under Scheduler ownership."""

    issues: list[str] = []
    if not registry_payload.get("scheduler_owned_runtime_registry", False):
        issues.append("registry payload must be scheduler_owned_runtime_registry")
    if not registry_payload.get("valid", False):
        issues.append("registry payload must be valid")
    if registry_payload.get("owner") != "scheduler":
        issues.append("registry owner must be scheduler")
    if not registry_payload.get("launcher_bootstrap_only", False):
        issues.append("launcher must remain bootstrap-only")
    if not registry_payload.get("eventbus_observation_only", False):
        issues.append("EventBus must remain observation-only")
    if not registry_payload.get("no_cli_per_component", False):
        issues.append("runtime API must keep no CLI per component")
    if registry_payload.get("creates_runtime_manager", False):
        issues.append("registry must not create a RuntimeManager")
    if registry_payload.get("instantiates_components", False):
        issues.append("0258 must not receive a registry that already instantiates components")

    registrations = _registrations(registry_payload)
    components = {str(item.get("component_id", "")) for item in registrations}
    required = {
        "eventbus",
        "passive_supervisor_sink",
        "sql_context_store",
        "openvino_embedding_service",
        "qdrant_projection_store",
        "github_artifact_exchange",
    }
    for component_id in sorted(required.difference(components)):
        issues.append(f"missing registry component {component_id}")

    capability_index = _build_capability_index(registrations)
    for capability in (
        "eventbus.publish_fact",
        "sql.context.write",
        "embedding.openvino.passage",
        "qdrant.projection.upsert",
        "qdrant.recall",
        "github.artifact.scan_once",
        "supervisor.observe",
    ):
        if capability not in capability_index:
            issues.append(f"missing capability {capability}")

    dependency_index = _build_dependency_index(registrations)
    if dependency_index.get("qdrant_projection_store") != (
        "sql_context_store",
        "openvino_embedding_service",
    ):
        issues.append("qdrant_projection_store must depend on SQL and OpenVINO")
    if dependency_index.get("passive_supervisor_sink") != ("eventbus",):
        issues.append("passive_supervisor_sink must depend on EventBus")
    return tuple(issues)


def build_scheduler_runtime_bootstrap_attachment(
    registry_payload: Mapping[str, Any],
    scheduler: object | None = None,
) -> SchedulerRuntimeBootstrapResult:
    """Build the Scheduler-owned runtime bootstrap attachment result.

    Passing ``scheduler`` is optional.  When omitted, the function returns a
    dry-run attachment plan.  When provided with ``attach`` below, the same data
    is attached to that Scheduler instance without starting any component.
    """

    registrations = _registrations(registry_payload)
    component_ids = tuple(str(item.get("component_id")) for item in registrations if item.get("component_id"))
    attachment = SchedulerRuntimeBootstrapAttachment(
        scheduler_ref=_scheduler_ref(scheduler),
        registry_component_ids=component_ids,
        capability_index=_build_capability_index(registrations),
        dependency_index=_build_dependency_index(registrations),
    )
    issues = validate_scheduler_runtime_bootstrap_attachment(registry_payload)
    return SchedulerRuntimeBootstrapResult(
        valid=not issues,
        issues=issues,
        attachment=attachment,
        registry_payload_digest=_stable_digest(registry_payload),
        attached_to_scheduler_object=False,
        dry_run=scheduler is None,
    )


def attach_scheduler_owned_runtime_registry(
    scheduler: object,
    registry_payload: Mapping[str, Any],
) -> SchedulerRuntimeBootstrapResult:
    """Attach the validated registry payload to an existing Scheduler object.

    This function intentionally uses attributes on the existing Scheduler
    instance instead of introducing a RuntimeManager.  It is an attachment step,
    not component instantiation or execution.
    """

    result = build_scheduler_runtime_bootstrap_attachment(registry_payload, scheduler)
    if not result.valid:
        return result

    setattr(scheduler, SCHEDULER_RUNTIME_REGISTRY_ATTRIBUTE, dict(registry_payload))
    setattr(scheduler, SCHEDULER_RUNTIME_BOOTSTRAP_ATTRIBUTE, result.attachment.to_dict())
    return SchedulerRuntimeBootstrapResult(
        valid=True,
        issues=(),
        attachment=result.attachment,
        registry_payload_digest=result.registry_payload_digest,
        attached_to_scheduler_object=True,
        dry_run=False,
    )


def scheduler_has_runtime_registry_attachment(scheduler: object) -> bool:
    """Return whether the Scheduler has a 0258 runtime registry attachment."""

    return hasattr(scheduler, SCHEDULER_RUNTIME_REGISTRY_ATTRIBUTE) and hasattr(
        scheduler,
        SCHEDULER_RUNTIME_BOOTSTRAP_ATTRIBUTE,
    )


def get_scheduler_runtime_registry_attachment(scheduler: object) -> dict[str, Any]:
    """Return the attached Scheduler runtime registry bootstrap metadata."""

    value = getattr(scheduler, SCHEDULER_RUNTIME_BOOTSTRAP_ATTRIBUTE)
    if not isinstance(value, MutableMapping):
        return dict(value)
    return dict(value)


def load_registry_payload(path: Path) -> dict[str, Any]:
    """Load the 0257 registry report."""

    return json.loads(path.read_text(encoding="utf-8"))


def write_scheduler_runtime_bootstrap_attachment_report(
    output: Path,
    registry_payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Write a dry-run Scheduler runtime bootstrap attachment report."""

    result = build_scheduler_runtime_bootstrap_attachment(registry_payload)
    payload = result.to_dict()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
