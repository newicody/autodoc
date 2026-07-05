from __future__ import annotations

import pytest

from context.scheduler_deliberation_route_contract import (
    DeliberationCycleCommand,
    DeliberationObservationFact,
    DeliberationRouteRef,
    SpecialistDemandFrame,
    SpecialistOpinionFrame,
    build_scheduler_deliberation_route_bridge,
    build_specialist_demand_frames,
)
from context.server_oriented_deliberation_cycle import ServerOrientation, SpecialistPreliminaryOpinion


def make_orientation() -> ServerOrientation:
    return ServerOrientation(
        orientation_ref="orientation:spoon-thermal",
        artifact_ref="github:project-item-123",
        source_ref="artifact:github-123",
        sql_context_ref="sql:context/spoon",
        title="Cuillère bébé",
        intent="Explorer les matériaux et les risques thermiques.",
        requested_specialist_refs=("specialist:material", "specialist:thermal"),
        requested_document_kinds=("preliminary-opinion",),
        context_refs=("ctx:brief/spoon", "qdrant:collection/autodoc"),
    )


def test_cycle_command_from_orientation_keeps_scheduler_as_orchestrator() -> None:
    command = DeliberationCycleCommand.from_orientation(make_orientation())
    mapping = command.to_mapping()
    assert mapping["scheduler_orchestrates"] is True
    assert mapping["parallel_local_orchestrator"] is False
    assert mapping["github_exchange_role"] == "artifact exchange only"
    assert command.route_cycle_root_ref.startswith("route:deliberation/")
    assert "sql:context/spoon" in command.context_refs


def test_route_ref_requires_dev_shm_autodoc_route_root() -> None:
    good = DeliberationRouteRef(
        route_ref="route:deliberation/cycle/round/demand",
        dev_shm_path="/dev/shm/autodoc/routes/deliberation/cycle/round/demand.frame",
        frame_kind="specialist_demand",
        cycle_id="cycle",
        round_id="round-0001",
        specialist_ref="specialist:thermal",
    )
    assert good.to_mapping()["data_plane"] == "dev_shm_multitask_interface"
    with pytest.raises(ValueError, match="/dev/shm/autodoc/routes/"):
        DeliberationRouteRef(
            route_ref="route:bad",
            dev_shm_path="/tmp/bad.frame",
            frame_kind="specialist_demand",
            cycle_id="cycle",
        )


def test_build_scheduler_bridge_creates_dispatch_commands_and_bus_ready_facts() -> None:
    bridge = build_scheduler_deliberation_route_bridge(make_orientation())
    mapping = bridge.to_mapping()
    assert mapping["scheduler_is_orchestrator"] is True
    assert mapping["dev_shm_is_multitask_interface"] is True
    assert mapping["event_bus_observation_only"] is True
    assert mapping["github_artifact_exchange_only"] is True
    assert mapping["e5_embedding_only"] is True
    assert len(bridge.dispatch_commands) == 2
    assert len(bridge.route_exchange.demand_routes) == 2
    assert len(bridge.route_exchange.opinion_routes) == 2
    assert {fact.kind for fact in bridge.observation_facts} == {
        "scheduler.dispatched_round",
        "scheduler.dispatched_specialist",
    }


def test_demand_frames_use_e5_embedding_hints_without_decision_authority() -> None:
    bridge = build_scheduler_deliberation_route_bridge(make_orientation())
    frames = build_specialist_demand_frames(
        bridge,
        request_text_by_specialist={"specialist:thermal": "Analyse thermique préliminaire."},
    )
    thermal = [frame for frame in frames if frame.specialist_ref == "specialist:thermal"][0]
    mapping = thermal.to_mapping()
    assert mapping["embedding_model_ref"] == "openvino:e5-small"
    assert mapping["qdrant_collection_ref"] == "qdrant:autodoc-context"
    assert mapping["e5_role"] == "embedding only"
    assert mapping["decision_maker"] is False
    assert "sql:context/spoon" in thermal.context_refs


def test_opinion_frame_from_preliminary_opinion_is_not_final_validation() -> None:
    opinion = SpecialistPreliminaryOpinion(
        opinion_ref="specialist-opinion:thermal-1",
        orientation_ref="orientation:spoon-thermal",
        specialist_ref="specialist:thermal",
        stance="analysis_signal",
        summary="La proposition est recevable comme signal mais nécessite revue thermique.",
        recommendation="Demander une seconde passe matériau.",
        evidence_refs=("sql:context/spoon",),
        context_delta_refs=("ctx-result:thermal-delta",),
        bus_observation_refs=("bus:thermal/explored-axis",),
        confidence=0.62,
    )
    frame = SpecialistOpinionFrame.from_preliminary_opinion(
        opinion,
        demand_frame_ref="route-frame:demand-thermal",
        route_ref="route:deliberation/cycle/round/opinion-thermal",
    )
    mapping = frame.to_mapping()
    assert mapping["validated_as_final_solution"] is False
    assert mapping["observation_fact_refs"] == ["bus:thermal/explored-axis"]


def test_observation_facts_are_commands_never_payload_transport() -> None:
    fact = DeliberationObservationFact(
        fact_ref="scheduler-trace:route-written",
        kind="route.frame_written",
        cycle_ref="scheduler-command:cycle",
        route_ref="route:deliberation/cycle/round/demand",
        specialist_ref="specialist:material",
        count=3,
    )
    mapping = fact.to_mapping()
    assert mapping["event_bus_role"] == "observation_only"
    assert mapping["command"] is False
    assert mapping["payload_ref_only"] is True
