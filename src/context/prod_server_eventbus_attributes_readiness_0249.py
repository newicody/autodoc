"""EventBus advanced attribute readiness for phase 0249.

This module validates the production EventBus attribute allowlist and redaction
surface. It composes the projection path readiness from 0248 so future SQL ->
OpenVINO -> Qdrant events can expose refs without putting large payloads on the
EventBus.

It does not create an EventBus, publish events, trigger commands, or mutate any
runtime backend.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from context.prod_server_ini_validation_0241 import load_ini, validate_ini_file
from context.prod_server_projection_path_readiness_0248 import build_projection_path_readiness


EVENTBUS_ATTRIBUTES_READINESS_VERSION = "0249.r1"


EVENTBUS_ATTRIBUTES_READINESS_BOUNDARY: dict[str, bool] = {
    "readiness_only": True,
    "uses_validated_ini": True,
    "uses_projection_path_readiness": True,
    "creates_eventbus": False,
    "publishes_events": False,
    "triggers_scheduler": False,
    "starts_threads": False,
    "writes_postgresql": False,
    "runs_openvino_inference": False,
    "writes_qdrant": False,
    "calls_github_api": False,
    "requires_non_stdlib": False,
}


EVENTBUS_SECTION = "eventbus.attributes"
REQUIRED_ATTRIBUTES = ("schema_version", "event_type", "trace_id", "component", "phase")
REFERENCE_ATTRIBUTES = ("intent_id", "result_id", "sql_ref", "qdrant_ref", "github_ref", "project_push_frame_ref", "payload_hash", "priority")
PROJECTION_REFERENCE_ATTRIBUTES = ("sql_ref", "payload_hash")
REDACTED_ATTRIBUTES = ("secret",)


@dataclass(frozen=True)
class EventBusAttributeIssue:
    """One issue in the EventBus attribute readiness surface."""

    field: str
    message: str


@dataclass(frozen=True)
class EventBusAttributeSurface:
    """Validated EventBus attribute allowlist and redaction surface."""

    required: tuple[str, ...]
    optional: tuple[str, ...]
    optional_redacted: tuple[str, ...]
    projection_references: tuple[str, ...]
    schema_version_required: bool
    large_payload_policy: str


@dataclass(frozen=True)
class EventBusAttributeReadinessReport:
    """JSON-compatible EventBus attribute readiness report."""

    version: str
    server_config_path: str
    openvino_config_path: str
    ready: bool
    surface: EventBusAttributeSurface | None
    issues: tuple[EventBusAttributeIssue, ...]


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def build_eventbus_attributes_readiness(*, server_config_path: Path, openvino_config_path: Path) -> EventBusAttributeReadinessReport:
    """Build EventBus attribute readiness from INI and projection readiness."""

    ini_validation = validate_ini_file(server_config_path)
    projection = build_projection_path_readiness(
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    parser = load_ini(server_config_path)
    issues: list[EventBusAttributeIssue] = []

    if not ini_validation.valid:
        for issue in ini_validation.issues:
            if issue.section == EVENTBUS_SECTION:
                issues.append(EventBusAttributeIssue(issue.key, issue.message))
    if not projection.ready:
        for issue in projection.issues:
            issues.append(EventBusAttributeIssue(issue.field, issue.message))

    if not parser.has_section(EVENTBUS_SECTION):
        return EventBusAttributeReadinessReport(
            version=EVENTBUS_ATTRIBUTES_READINESS_VERSION,
            server_config_path=str(server_config_path),
            openvino_config_path=str(openvino_config_path),
            ready=False,
            surface=None,
            issues=tuple(issues + [EventBusAttributeIssue(EVENTBUS_SECTION, "missing EventBus attribute section")]),
        )

    required = _split_csv(parser.get(EVENTBUS_SECTION, "required", fallback=""))
    optional = _split_csv(parser.get(EVENTBUS_SECTION, "optional", fallback=""))
    optional_redacted = _split_csv(parser.get(EVENTBUS_SECTION, "optional_redacted", fallback=""))
    allowed = set(required) | set(optional) | set(optional_redacted)

    for attribute in REQUIRED_ATTRIBUTES:
        if attribute not in required:
            issues.append(EventBusAttributeIssue("required", f"must include {attribute}"))
    for attribute in REFERENCE_ATTRIBUTES:
        if attribute not in allowed:
            issues.append(EventBusAttributeIssue("optional", f"must allow {attribute}"))
    for attribute in REDACTED_ATTRIBUTES:
        if attribute not in optional_redacted:
            issues.append(EventBusAttributeIssue("optional_redacted", f"must redact {attribute}"))
    for attribute in PROJECTION_REFERENCE_ATTRIBUTES:
        if attribute not in allowed:
            issues.append(EventBusAttributeIssue("projection_references", f"must expose {attribute} as a reference"))

    if "payload" in allowed or "payload_json" in allowed:
        issues.append(EventBusAttributeIssue("large_payload_policy", "large payloads must not be EventBus attributes"))

    surface = EventBusAttributeSurface(
        required=required,
        optional=optional,
        optional_redacted=optional_redacted,
        projection_references=PROJECTION_REFERENCE_ATTRIBUTES,
        schema_version_required="schema_version" in required,
        large_payload_policy="refs_only_no_large_payloads",
    )

    return EventBusAttributeReadinessReport(
        version=EVENTBUS_ATTRIBUTES_READINESS_VERSION,
        server_config_path=str(server_config_path),
        openvino_config_path=str(openvino_config_path),
        ready=not issues,
        surface=surface,
        issues=tuple(issues),
    )


def eventbus_attributes_readiness_to_dict(report: EventBusAttributeReadinessReport) -> dict[str, Any]:
    """Convert an EventBus attribute readiness report to JSON-compatible data."""

    return asdict(report)


def write_eventbus_attributes_readiness_report(*, server_config_path: Path, openvino_config_path: Path, output_path: Path) -> dict[str, Any]:
    """Build and write the EventBus attribute readiness report."""

    report = build_eventbus_attributes_readiness(
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    payload = {
        "production_server_eventbus_attributes_readiness_written": True,
        "eventbus_attributes_readiness": eventbus_attributes_readiness_to_dict(report),
        "boundary": dict(EVENTBUS_ATTRIBUTES_READINESS_BOUNDARY),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    return payload
