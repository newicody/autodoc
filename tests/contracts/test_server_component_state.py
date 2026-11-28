from __future__ import annotations

import pytest

from contracts.server_component_state import (
    ComponentStateContractError,
    ServerComponentStateSnapshot,
)
from context.server_scientific_framing_assessment_0287 import (
    build_server_scientific_framing_assessment,
)


def _snapshot(**overrides):
    value = {
        "component_ref": "component:openvino",
        "source_ref": "component-state-source:openvino-status",
        "observed_at": "2026-11-28T12:00:00Z",
        "status": "complete",
        "availability": "available",
        "freshness": "fresh",
        "communication_status": "connected",
        "capabilities": ["embedding.e5.384"],
        "reservations": [],
        "interfaces": ["embedding.query"],
        "usage_statistics": {"requests": 12, "latency_ms": 8.5},
        "supported_representations": ["vector embeddings"],
        "unsupported_representations": [],
        "available_data": ["dataset:embeddings:v2"],
        "missing_data": [],
        "constraints": [],
        "report_outline": ["Embedding coverage"],
        "assessment": "E5 is available.",
        "coherence_status": "coherent",
        "errors": [],
    }
    value.update(overrides)
    return value


def test_component_snapshot_round_trips_and_keeps_provenance():
    snapshot = ServerComponentStateSnapshot.from_mapping(_snapshot())
    assert snapshot.to_mapping()["source_ref"] == "component-state-source:openvino-status"
    assert snapshot.to_mapping()["usage_statistics"]["requests"] == 12


def test_component_snapshot_rejects_timezone_free_observation():
    with pytest.raises(ComponentStateContractError, match="timezone"):
        ServerComponentStateSnapshot.from_mapping(
            _snapshot(observed_at="2026-11-28T12:00:00")
        )


def test_assessment_aggregates_capabilities_and_keeps_usage_separate():
    result = build_server_scientific_framing_assessment(
        [ServerComponentStateSnapshot.from_mapping(_snapshot())],
        observed_at="2026-11-28T12:01:00Z",
    )
    assert result["coherence_status"] == "coherent"
    assert result["verified_capabilities"] == ["embedding.e5.384"]
    assert result["component_usage_statistics"]["component:openvino"]["requests"] == 12
    assert result["scheduler_capacity_inferred_from_hardware"] is False
    assert result["unknown_values_defaulted_to_zero"] is False


def test_stale_or_partial_component_makes_assessment_partial():
    snapshot = ServerComponentStateSnapshot.from_mapping(
        _snapshot(
            status="partial",
            freshness="stale",
            availability="constrained",
            communication_status="degraded",
            errors=["last sample incomplete"],
            missing_data=["dataset:calibration"],
            coherence_status="coherent",
        )
    )
    result = build_server_scientific_framing_assessment([snapshot])
    assert result["coherence_status"] == "partially_coherent"
    assert any("fraîcheur stale" in item for item in result["constraints"])
    assert "dataset:calibration" in result["missing_data"]


def test_incoherent_component_is_not_hidden_by_aggregation():
    snapshot = ServerComponentStateSnapshot.from_mapping(
        _snapshot(coherence_status="incoherent")
    )
    result = build_server_scientific_framing_assessment([snapshot])
    assert result["coherence_status"] == "incoherent"


def test_duplicate_component_snapshots_are_rejected():
    snapshot = ServerComponentStateSnapshot.from_mapping(_snapshot())
    with pytest.raises(ValueError, match="unique component_ref"):
        build_server_scientific_framing_assessment([snapshot, snapshot])
