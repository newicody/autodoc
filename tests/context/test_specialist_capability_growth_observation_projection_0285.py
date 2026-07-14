import asyncio
from dataclasses import FrozenInstanceError, replace

import pytest

from contracts.event import Event, EventType
from context.portable_specialist_revision_lineage_contract_0285 import (
    PORTABLE_SPECIALIST_REVISION_SCHEMA,
    PortableSpecialistRevision,
)
from context.scheduler_approved_specialist_revision_selection_0285 import (
    SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_RESULT_SCHEMA,
    SchedulerApprovedSpecialistRevisionSelectionResult,
)
from context.specialist_capability_growth_observation_projection_0285 import (
    SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION_SCHEMA,
    SpecialistCapabilityGrowthObservationProjectionError,
    build_specialist_capability_growth_observation_event,
    build_specialist_capability_growth_observation_projection,
    build_specialist_capability_growth_passive_read_model,
    publish_specialist_capability_growth_observation,
)


class FakeDescriptor:
    specialist_ref = "specialist:researcher"
    specialist_version = "2.0.0"

    def to_mapping(self):
        return {
            "specialist_ref": self.specialist_ref,
            "specialist_version": self.specialist_version,
        }


class FakeEventBus:
    def __init__(self) -> None:
        self.events = []

    async def publish(self, event: Event) -> None:
        self.events.append(event)


class UnsafeSelectionResult(SchedulerApprovedSpecialistRevisionSelectionResult):
    def to_mapping(self, *, include_digest: bool = True):
        mapping = super().to_mapping(include_digest=include_digest)
        mapping["laboratory_execution_performed"] = True
        return mapping


def revision(*, proposal_ref="proposal:researcher:add-analysis"):
    value = object.__new__(PortableSpecialistRevision)
    fields = {
        "schema": PORTABLE_SPECIALIST_REVISION_SCHEMA,
        "revision_ref": "revision:researcher:2",
        "revision_number": 2,
        "descriptor": FakeDescriptor(),
        "parent_revision_ref": "revision:researcher:1",
        "source_proposal_ref": proposal_ref,
        "source_proposal_digest_sha256": "a" * 64,
        "evidence_refs": ("evidence:test:1", "report:test:2"),
        "metadata": (),
    }
    for name, item in fields.items():
        object.__setattr__(value, name, item)
    return value


def selection(*, selected_revision=None, result_type=SchedulerApprovedSpecialistRevisionSelectionResult):
    return result_type(
        schema=SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_RESULT_SCHEMA,
        selection_ref="selection:researcher:2",
        command_ref="selection-command:researcher:2",
        scheduler_ref="scheduler:main",
        policy_ref="policy:specialist-selection",
        policy_digest_sha256="c" * 64,
        history_ref="history:researcher",
        history_snapshot_digest_sha256="d" * 64,
        history_entry_ref="history-entry:researcher:2",
        history_entry_digest_sha256="e" * 64,
        sql_ref="sql:specialist-history:researcher:2",
        decision_ref="decision:researcher:2",
        selected_revision=selected_revision or revision(),
        capability="analysis.deep",
        input_contract_ref="contract:research-request.v1",
        output_contract_ref="contract:research-result.v1",
        laboratory_ref="laboratory:local-fake",
        visit_mode="visitor",
        execution_boundary="in_process",
        conversation_ref="conversation:researcher:2",
        context_refs=("context:researcher:2",),
    )


def test_projection_contains_four_correlated_facts_in_deterministic_order() -> None:
    result = build_specialist_capability_growth_observation_projection(selection())

    assert result.schema == SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION_SCHEMA
    assert [fact.fact_kind for fact in result.facts] == [
        "specialist_capability_growth.revision_proposed",
        "specialist_capability_growth.operator_approved",
        "specialist_capability_growth.durable_history_recorded",
        "specialist_capability_growth.scheduler_selected",
    ]
    assert all(fact.observation_only for fact in result.facts)
    assert all(not fact.command for fact in result.facts)
    assert all(fact.sql_ref == result.sql_ref for fact in result.facts)
    assert result.authoritative is False


def test_projection_digest_is_deterministic() -> None:
    left = build_specialist_capability_growth_observation_projection(selection())
    right = build_specialist_capability_growth_observation_projection(selection())
    assert left.projection_digest == right.projection_digest
    assert len(left.projection_digest) == 64


def test_fact_is_immutable() -> None:
    fact = build_specialist_capability_growth_observation_projection(selection()).facts[0]
    with pytest.raises(FrozenInstanceError):
        fact.command = True


def test_event_uses_reserved_result_type_and_observability_destination() -> None:
    projection = build_specialist_capability_growth_observation_projection(selection())
    event = build_specialist_capability_growth_observation_event(
        projection, event_id="event-r7"
    )
    assert event.type is EventType.SPECIALIST_REVISION_SELECTION_RESULT
    assert event.dest == "observability"
    assert event.id == "event-r7"
    assert event.correlation_id == projection.selection_ref
    assert event.metadata["observation_only"] is True
    assert event.metadata["command"] is False
    assert event.metadata["sql_ref"] == projection.sql_ref


def test_publish_uses_existing_event_bus_port_once() -> None:
    bus = FakeEventBus()
    report = asyncio.run(
        publish_specialist_capability_growth_observation(
            bus, selection(), event_id="event-published"
        )
    )
    assert report.published_count == 1
    assert report.controls_execution is False
    assert len(bus.events) == 1
    assert bus.events[0].id == "event-published"


def test_passive_read_model_accepts_all_canonical_facts() -> None:
    projection = build_specialist_capability_growth_observation_projection(selection())
    event = build_specialist_capability_growth_observation_event(
        projection, event_id="event-read-model"
    )
    read_model = build_specialist_capability_growth_passive_read_model(event)
    assert read_model.valid is True
    assert read_model.accepted_fact_count == 4
    assert read_model.rejected_fact_count == 0
    assert read_model.authoritative is False
    mapping = read_model.to_mapping()
    assert mapping["can_authorize_revision"] is False
    assert mapping["can_select_revision"] is False
    assert mapping["can_dispatch_laboratory"] is False
    assert mapping["can_write_sql"] is False
    assert mapping["can_write_qdrant"] is False


def test_non_root_proposal_is_required() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthObservationProjectionError,
        match="non-root revision",
    ):
        build_specialist_capability_growth_observation_projection(
            selection(selected_revision=revision(proposal_ref=None))
        )


def test_unsafe_selection_boundary_is_rejected() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthObservationProjectionError,
        match="laboratory_execution_performed",
    ):
        build_specialist_capability_growth_observation_projection(
            selection(result_type=UnsafeSelectionResult)
        )


def test_wrong_event_type_is_rejected_by_passive_read_model() -> None:
    projection = build_specialist_capability_growth_observation_projection(selection())
    event = Event(type=EventType.ERROR, source="test", payload=projection)
    with pytest.raises(
        SpecialistCapabilityGrowthObservationProjectionError,
        match="only accepts",
    ):
        build_specialist_capability_growth_passive_read_model(event)


def test_fact_rejects_unknown_kind() -> None:
    base = build_specialist_capability_growth_observation_projection(selection()).facts[0]
    with pytest.raises(
        SpecialistCapabilityGrowthObservationProjectionError,
        match="fact_kind",
    ):
        replace(base, fact_kind="unknown")
