"""Build the one-shot server framing assessment from component-owned snapshots.

The caller supplies snapshots collected through existing component interfaces.
This module is a pure aggregation adapter: it creates no registry, poller,
manager, EventBus, Scheduler, or backend connection.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from contracts.server_component_state import ServerComponentStateSnapshot

ASSESSMENT_SCHEMA = "missipy.server.scientific_framing_assessment.v1"


class ServerScientificFramingAssessmentError(ValueError):
    """Invalid or insufficient component state for a server assessment."""


def build_server_scientific_framing_assessment(
    snapshots: Iterable[ServerComponentStateSnapshot | Mapping[str, Any]],
    *,
    observed_at: str | None = None,
) -> dict[str, Any]:
    values = tuple(
        item if isinstance(item, ServerComponentStateSnapshot)
        else ServerComponentStateSnapshot.from_mapping(item)
        for item in snapshots
    )
    if not values:
        raise ServerScientificFramingAssessmentError(
            "at least one component-owned state snapshot is required"
        )
    refs = [item.component_ref for item in values]
    if len(refs) != len(set(refs)):
        raise ServerScientificFramingAssessmentError(
            "component state snapshots must have unique component_ref values"
        )
    timestamp = observed_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    # Validate the aggregation timestamp with the same timezone-aware rule.
    ServerComponentStateSnapshot(
        component_ref="component:assessment-aggregator",
        source_ref="component-state-source:assessment-aggregator",
        observed_at=timestamp,
        status="complete",
        availability="available",
        freshness="fresh",
        communication_status="connected",
    )

    def merge(name: str) -> list[str]:
        result: list[str] = []
        for snapshot in values:
            for item in getattr(snapshot, name):
                if item not in result:
                    result.append(item)
        return result

    statuses = {item.coherence_status for item in values}
    if "incoherent" in statuses:
        coherence = "incoherent"
    elif (
        statuses == {"coherent"}
        and all(
            item.status == "complete"
            and item.availability == "available"
            and item.freshness == "fresh"
            and item.communication_status == "connected"
            for item in values
        )
        and not merge("unsupported_representations")
        and not merge("missing_data")
    ):
        coherence = "coherent"
    else:
        coherence = "partially_coherent"

    assessments = [
        f"{item.component_ref}: {item.assessment.strip()}"
        for item in values if item.assessment.strip()
    ]
    if not assessments:
        assessments = [
            "Évaluation limitée aux états déclarés par les composants ; "
            "les informations absentes ou non fraîches restent inconnues."
        ]

    component_observations = [item.to_mapping() for item in values]
    provenance = [
        {
            "source_ref": item.source_ref,
            "observed_at": item.observed_at,
            "freshness": item.freshness,
        }
        for item in values
    ]
    constraints = merge("constraints")
    for item in values:
        if item.availability != "available":
            constraints.append(
                f"{item.component_ref}: disponibilité {item.availability}"
            )
        if item.communication_status != "connected":
            constraints.append(
                f"{item.component_ref}: communication {item.communication_status}"
            )
        if item.status != "complete":
            constraints.append(
                f"{item.component_ref}: état de collecte {item.status}"
            )
        if item.freshness != "fresh":
            constraints.append(
                f"{item.component_ref}: fraîcheur {item.freshness}"
            )
        constraints.extend(
            f"{item.component_ref}: réservation {value}"
            for value in item.reservations
        )
        constraints.extend(
            f"{item.component_ref}: interface {value}"
            for value in item.interfaces
        )
        constraints.extend(
            f"{item.component_ref}: erreur {value}"
            for value in item.errors
        )

    return {
        "schema": ASSESSMENT_SCHEMA,
        "coherence_status": coherence,
        "assessment": " ".join(assessments),
        "supported_representations": merge("supported_representations"),
        "unsupported_representations": merge("unsupported_representations"),
        "available_data": merge("available_data"),
        "missing_data": merge("missing_data"),
        "verified_capabilities": merge("capabilities"),
        "constraints": list(dict.fromkeys(constraints)),
        "report_outline": merge("report_outline"),
        "provenance": provenance,
        "component_observations": component_observations,
        "component_usage_statistics": {
            item.component_ref: dict(item.usage_statistics) for item in values
        },
        "observed_at": timestamp,
        "scheduler_capacity_inferred_from_hardware": False,
        "unknown_values_defaulted_to_zero": False,
    }
