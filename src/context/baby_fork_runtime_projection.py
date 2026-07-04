"""Baby-fork smoke project projection to SHM Runtime schemas.

This module implements the P4 integration step without changing the existing
baby-fork smoke pipeline.

It deliberately does not:
- create shared memory
- create semaphores
- start RouteProxy
- call Scheduler
- mutate ControlFS
- replace the baby-fork smoke project

It only projects an existing baby-fork report into compact runtime messages:
DataHandle, EventBusMessage, ContextBusMessage and RouteMessage.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping

from runtime.shm_runtime_schema import (
    CONTEXT_BUS_MESSAGE_SCHEMA,
    DATA_HANDLE_SCHEMA,
    EVENT_BUS_MESSAGE_SCHEMA,
    ROUTE_MESSAGE_SCHEMA,
    ContextBusMessage,
    DataHandle,
    EventBusMessage,
    RouteMessage,
)


BABY_FORK_CONTEXT_ID = "baby_fork_smoke"
BABY_FORK_RETRIEVAL_ROUTE = "baby_fork.retrieval"
BABY_FORK_VARIANT_ROUTE = "baby_fork.variant_stub"
BABY_FORK_CONTEXT_GATE_ROUTE = "baby_fork.context_gate"

BABY_FORK_REPORT_SCHEMA = "missipy.baby_fork.report.v1"
BABY_FORK_RETRIEVAL_COMPLETED_SCHEMA = "missipy.baby_fork.retrieval_completed.v1"
BABY_FORK_VARIANTS_GENERATED_SCHEMA = "missipy.baby_fork.variants_generated.v1"
BABY_FORK_CONTEXT_VERSIONED_SCHEMA = "missipy.baby_fork.context_versioned.v1"
BABY_FORK_ROUTE_REPLY_SCHEMA = "missipy.baby_fork.route_reply.v1"
BABY_FORK_CONTEXT_PATCH_SCHEMA = "missipy.baby_fork.context_patch.v1"


@dataclass(frozen=True)
class BabyForkRuntimeProjection:
    """Runtime-message projection of a baby-fork smoke report."""

    data_handles: tuple[DataHandle, ...]
    events: tuple[EventBusMessage, ...]
    contexts: tuple[ContextBusMessage, ...]
    routes: tuple[RouteMessage, ...]

    def to_mapping(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            "data_handles": [item.to_mapping() for item in self.data_handles],
            "events": [item.to_mapping() for item in self.events],
            "contexts": [item.to_mapping() for item in self.contexts],
            "routes": [item.to_mapping() for item in self.routes],
        }


def build_baby_fork_runtime_projection(
    report: Mapping[str, Any],
    *,
    report_uri: str = ".var/baby_fork_smoke/baby_fork_report.json",
    occurred_at: str = "2026-07-04T20:00:00Z",
) -> BabyForkRuntimeProjection:
    """Project a baby-fork smoke report into runtime schema messages.

    The report may be the current smoke-project JSON result. The function is
    intentionally tolerant of missing optional fields because the current smoke
    project is still evolving.
    """

    context_id = _context_id(report)
    context_version = _context_version(report)
    selected_variant_id = _selected_variant_id(report)

    evidence_handle = DataHandle.from_mapping(
        {
            "schema": DATA_HANDLE_SCHEMA,
            "handle_id": f"{context_id}:report",
            "storage": "zfs",
            "uri": report_uri,
            "content_schema": BABY_FORK_REPORT_SCHEMA,
            "size_bytes": _stable_size(report),
            "hash": "sha256:projection",
            "producer": "baby_fork_smoke_project",
            "zone": "workers",
            "created_at": occurred_at,
            "ttl_seconds": 3600,
        }
    )

    retrieved_ids = _retrieved_ids(report)
    rejected_ids = _rejected_ids(report)
    variants = _variants(report)

    retrieval_event = EventBusMessage.from_mapping(
        {
            "schema": EVENT_BUS_MESSAGE_SCHEMA,
            "event_id": "evt:baby_fork.retrieval.completed",
            "topic": "retrieval.completed",
            "source": "retrieval_worker",
            "occurred_at": occurred_at,
            "zone": "workers",
            "payload_schema": BABY_FORK_RETRIEVAL_COMPLETED_SCHEMA,
            "payload": {
                "route_id": BABY_FORK_RETRIEVAL_ROUTE,
                "context_id": context_id,
                "retrieved_ids": retrieved_ids,
                "rejected_ids": rejected_ids,
                "retrieved_count": len(retrieved_ids),
                "rejected_count": len(rejected_ids),
            },
            "data_handles": [evidence_handle.to_mapping()],
        }
    )

    variants_event = EventBusMessage.from_mapping(
        {
            "schema": EVENT_BUS_MESSAGE_SCHEMA,
            "event_id": "evt:baby_fork.variants.generated",
            "topic": "variants.generated",
            "source": "variant_generator_stub",
            "occurred_at": occurred_at,
            "zone": "workers",
            "payload_schema": BABY_FORK_VARIANTS_GENERATED_SCHEMA,
            "payload": {
                "route_id": BABY_FORK_VARIANT_ROUTE,
                "context_id": context_id,
                "variant_count": len(variants),
                "selected_variant_id": selected_variant_id,
            },
        }
    )

    context_message = ContextBusMessage.from_mapping(
        {
            "schema": CONTEXT_BUS_MESSAGE_SCHEMA,
            "context_id": context_id,
            "context_version": context_version,
            "topic": "context.versioned",
            "source": "context_gate",
            "occurred_at": occurred_at,
            "zone": "context",
            "payload_schema": BABY_FORK_CONTEXT_VERSIONED_SCHEMA,
            "payload": {
                "selected_variant_id": selected_variant_id,
                "route_id": BABY_FORK_CONTEXT_GATE_ROUTE,
            },
            "data_handles": [evidence_handle.to_mapping()],
        }
    )

    retrieval_reply = RouteMessage.from_mapping(
        {
            "schema": ROUTE_MESSAGE_SCHEMA,
            "route_id": BABY_FORK_RETRIEVAL_ROUTE,
            "message_id": "msg:baby_fork.retrieval.reply",
            "kind": "reply",
            "source": "retrieval_worker",
            "target": "scheduler",
            "occurred_at": occurred_at,
            "payload_schema": BABY_FORK_ROUTE_REPLY_SCHEMA,
            "payload": {
                "context_id": context_id,
                "retrieved_ids": retrieved_ids,
                "rejected_ids": rejected_ids,
            },
            "data_handles": [evidence_handle.to_mapping()],
        }
    )

    variant_event = RouteMessage.from_mapping(
        {
            "schema": ROUTE_MESSAGE_SCHEMA,
            "route_id": BABY_FORK_VARIANT_ROUTE,
            "message_id": "msg:baby_fork.variant_stub.event",
            "kind": "event",
            "source": "variant_generator_stub",
            "target": "scheduler",
            "occurred_at": occurred_at,
            "payload_schema": BABY_FORK_VARIANTS_GENERATED_SCHEMA,
            "payload": {
                "context_id": context_id,
                "variant_count": len(variants),
                "selected_variant_id": selected_variant_id,
            },
        }
    )

    context_patch = RouteMessage.from_mapping(
        {
            "schema": ROUTE_MESSAGE_SCHEMA,
            "route_id": BABY_FORK_CONTEXT_GATE_ROUTE,
            "message_id": "msg:baby_fork.context_gate.patch",
            "kind": "context_patch",
            "source": "context_gate",
            "target": "scheduler",
            "occurred_at": occurred_at,
            "payload_schema": BABY_FORK_CONTEXT_PATCH_SCHEMA,
            "payload": {
                "context_id": context_id,
                "context_version": context_version,
                "selected_variant_id": selected_variant_id,
            },
        }
    )

    return BabyForkRuntimeProjection(
        data_handles=(evidence_handle,),
        events=(retrieval_event, variants_event),
        contexts=(context_message,),
        routes=(retrieval_reply, variant_event, context_patch),
    )


def build_baby_fork_runtime_projection_json(
    report: Mapping[str, Any],
    *,
    report_uri: str = ".var/baby_fork_smoke/baby_fork_report.json",
    occurred_at: str = "2026-07-04T20:00:00Z",
) -> str:
    """Return the projection as deterministic JSON."""

    projection = build_baby_fork_runtime_projection(
        report,
        report_uri=report_uri,
        occurred_at=occurred_at,
    )
    return json.dumps(projection.to_mapping(), indent=2, sort_keys=True)


def _context_id(report: Mapping[str, Any]) -> str:
    final_context = _mapping(report.get("final_context"))
    return str(final_context.get("context_id") or report.get("context_id") or BABY_FORK_CONTEXT_ID)


def _context_version(report: Mapping[str, Any]) -> int:
    final_context = _mapping(report.get("final_context"))
    for key in ("context_version", "version"):
        value = final_context.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 1:
            return value
    value = report.get("context_version")
    if isinstance(value, int) and not isinstance(value, bool) and value >= 1:
        return value
    return 2


def _selected_variant_id(report: Mapping[str, Any]) -> str:
    final_context = _mapping(report.get("final_context"))
    value = final_context.get("selected_variant_id") or report.get("selected_variant_id")
    if value:
        return str(value)
    variants = _variants(report)
    if variants:
        first = _mapping(variants[0])
        if first.get("variant_id"):
            return str(first["variant_id"])
        if first.get("id"):
            return str(first["id"])
    return "variant-1"


def _retrieved_ids(report: Mapping[str, Any]) -> list[str]:
    retrieval = _mapping(report.get("retrieval"))
    value = retrieval.get("retrieved_ids") or report.get("retrieved_ids") or []
    return [str(item) for item in value] if isinstance(value, list) else []


def _rejected_ids(report: Mapping[str, Any]) -> list[str]:
    retrieval = _mapping(report.get("retrieval"))
    value = retrieval.get("rejected_ids") or report.get("rejected_ids") or []
    return [str(item) for item in value] if isinstance(value, list) else []


def _variants(report: Mapping[str, Any]) -> list[Any]:
    value = report.get("variants") or []
    return list(value) if isinstance(value, list) else []


def _stable_size(report: Mapping[str, Any]) -> int:
    return len(json.dumps(dict(report), sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
