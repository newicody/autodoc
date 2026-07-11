import asyncio
import json

import pytest

from context.fake_laboratory_deliberation_composition_0274 import (
    FAKE_LABORATORY_DELIBERATION_COMMAND_SCHEMA,
    FakeLaboratoryDeliberationCommand,
    FakeLaboratoryDeliberationError,
    run_fake_laboratory_deliberation,
)
from context.laboratory_framework_contract_0273 import (
    LaboratoryResourceBudget,
)
from context.scheduler_laboratory_visit_binding_0274 import (
    register_laboratory_visit_handler,
)
from context.server_oriented_deliberation_cycle import ServerOrientation
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler


def orientation() -> ServerOrientation:
    return ServerOrientation(
        orientation_ref="orientation:laboratory-r2",
        artifact_ref="artifact:github-request:r2",
        source_ref="artifact:source-candidate:r2",
        sql_context_ref="sql:github_artifact:r2",
        title="Étude laboratoire fictif",
        intent="Produire une synthèse locale bornée.",
        requested_specialist_refs=(
            "specialist:technical",
            "specialist:validator",
        ),
        requested_document_kinds=("analysis",),
        do_directives=("Conserver les preuves.",),
        avoid_directives=("Ne pas publier sans gate.",),
        context_refs=("ctx:project:r2",),
    )


def command(
    *,
    scenarios: tuple[tuple[str, str], ...] = (),
) -> FakeLaboratoryDeliberationCommand:
    return FakeLaboratoryDeliberationCommand(
        schema=FAKE_LABORATORY_DELIBERATION_COMMAND_SCHEMA,
        orientation=orientation(),
        artifact_ref="artifact:github-request:r2",
        source_candidate_ref="source-candidate:projectv2:r2",
        target_ref="github:issue:newicody/ideas/42",
        context_generation=3,
        resource_budget=LaboratoryResourceBudget(
            max_duration_ms=2_000,
            max_context_refs=16,
            max_evidence_refs=16,
            max_followup_requests=8,
        ),
        scenario_by_specialist=scenarios,
        priority=7,
    )


async def execute(
    item: FakeLaboratoryDeliberationCommand,
):
    event_bus = EventBus()
    dispatcher = Dispatcher(event_bus)
    register_laboratory_visit_handler(dispatcher)
    scheduler = Scheduler(
        queue=PriorityQueue(),
        dispatcher=dispatcher,
        event_bus=event_bus,
        registry=Registry(),
        context_interval=60.0,
    )
    run_task = asyncio.create_task(scheduler.run())
    try:
        return await run_fake_laboratory_deliberation(
            scheduler,
            item,
            timeout_per_visit=1.0,
        )
    finally:
        await scheduler.shutdown()
        await asyncio.wait_for(run_task, timeout=1.0)


def test_completed_visits_close_local_synthesis_and_final_artifact() -> None:
    result = asyncio.run(execute(command()))
    payload = result.to_mapping()

    assert len(result.receipts) == 2
    assert len(result.opinions) == 2
    assert result.refined_demands == ()
    assert result.round.convergence_state == "ready_for_final_synthesis"
    assert result.round.needs_next_round is False
    assert result.publication_ready is True
    assert result.final_packet is not None
    assert result.final_packet.synthesis.final_publication_ready is True
    assert result.final_artifact is not None
    assert result.final_artifact.artifact_ref == "artifact:github-request:r2"
    assert payload["publication_gate_required"] is True
    assert payload["github_mutation_performed"] is False
    assert payload["scheduler_created"] is False
    assert payload["parallel_orchestrator_created"] is False
    json.dumps(payload, sort_keys=True)


def test_needs_context_keeps_local_cycle_open_and_builds_demand() -> None:
    result = asyncio.run(
        execute(
            command(
                scenarios=(
                    ("specialist:technical", "needs_context"),
                )
            )
        )
    )

    assert result.publication_ready is False
    assert result.final_packet is None
    assert result.final_artifact is None
    assert result.round.convergence_state == "needs_refinement"
    assert result.round.needs_next_round is True
    assert result.refined_demands
    assert any(
        opinion.stance == "needs_context"
        for opinion in result.opinions
    )


def test_needs_specialist_propagates_mediated_followup() -> None:
    result = asyncio.run(
        execute(
            command(
                scenarios=(
                    ("specialist:technical", "needs_specialist"),
                )
            )
        )
    )

    opinion = next(
        item
        for item in result.opinions
        if item.specialist_ref == "specialist:technical"
    )
    assert opinion.stance == "needs_specialist"
    assert opinion.proposed_specialist_refs == ("specialist:validator",)
    assert result.publication_ready is False
    assert result.refined_demands


def test_all_rejected_visits_block_without_final_artifact() -> None:
    result = asyncio.run(
        execute(
            command(
                scenarios=(
                    ("specialist:technical", "rejected"),
                    ("specialist:validator", "rejected"),
                )
            )
        )
    )

    assert result.round.convergence_state == "blocked"
    assert result.publication_ready is False
    assert result.final_artifact is None


def test_replay_is_deterministic_except_scheduler_event_ids() -> None:
    first = asyncio.run(execute(command()))
    second = asyncio.run(execute(command()))

    assert first.round.to_mapping() == second.round.to_mapping()
    assert first.synthesis.to_mapping() == second.synthesis.to_mapping()
    assert (
        first.final_artifact.to_mapping()
        == second.final_artifact.to_mapping()
    )
    assert [
        receipt.execution.to_mapping() for receipt in first.receipts
    ] == [
        receipt.execution.to_mapping() for receipt in second.receipts
    ]


def test_command_rejects_network_and_unknown_specialist_scenario() -> None:
    with pytest.raises(
        FakeLaboratoryDeliberationError,
        match="network-closed",
    ):
        FakeLaboratoryDeliberationCommand(
            schema=FAKE_LABORATORY_DELIBERATION_COMMAND_SCHEMA,
            orientation=orientation(),
            artifact_ref="artifact:github-request:r2",
            source_candidate_ref="source-candidate:projectv2:r2",
            target_ref="github:issue:newicody/ideas/42",
            context_generation=3,
            resource_budget=LaboratoryResourceBudget(
                allow_network=True,
                max_external_calls=1,
            ),
        )

    with pytest.raises(
        FakeLaboratoryDeliberationError,
        match="must be requested",
    ):
        command(
            scenarios=(("specialist:not-requested", "completed"),)
        )
