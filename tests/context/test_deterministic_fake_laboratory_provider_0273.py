import json

import pytest

from context.deterministic_fake_laboratory_provider_0273 import (
    DETERMINISTIC_FAKE_COMPONENT_ID,
    DeterministicFakeLaboratoryProvider,
    LaboratoryProvider,
    LaboratoryProviderExecutionError,
    bind_deterministic_fake_laboratory_registration,
    build_deterministic_fake_laboratory_binding_plan,
    build_deterministic_fake_laboratory_descriptor,
    build_deterministic_fake_laboratory_provider,
    build_deterministic_fake_laboratory_registration,
    execute_deterministic_fake_laboratory_visit,
)
from context.laboratory_framework_contract_0273 import (
    LABORATORY_VISIT_REQUEST_SCHEMA,
    LaboratoryContractError,
    LaboratoryDescriptor,
    LaboratoryResourceBudget,
    LaboratoryVisitRequest,
)
from context.scheduler_owned_runtime_registry_0257 import (
    SchedulerOwnedRuntimeComponentRegistration,
    build_scheduler_owned_runtime_registry,
    validate_scheduler_owned_runtime_registry,
)


def request(**overrides):
    values = {
        "schema": LABORATORY_VISIT_REQUEST_SCHEMA,
        "visit_ref": "laboratory-visit:r3-test",
        "laboratory_ref": "laboratory:local-fake",
        "specialist_ref": "specialist:technical",
        "objective_ref": "orientation:r3-test",
        "source_candidate_ref": "source-candidate:r3-test",
        "context_generation": 1,
        "input_contract_ref": "contract:missipy.specialist.demand.v1",
        "expected_output_contract_ref": (
            "contract:missipy.laboratory.visit_result.v1"
        ),
        "resource_budget": LaboratoryResourceBudget(),
        "return_route_ref": "route:laboratory/r3-test/result",
        "context_refs": ("sql:context:r3-test",),
        "evidence_refs": ("artifact:evidence:r3-test",),
    }
    values.update(overrides)
    return LaboratoryVisitRequest(**values)


def test_fake_descriptor_is_enabled_ready_local_and_network_closed() -> None:
    descriptor = build_deterministic_fake_laboratory_descriptor()
    assert descriptor.laboratory_ref == "laboratory:local-fake"
    assert descriptor.provider_kind == "local_fake"
    assert descriptor.execution_boundary == "in_process"
    assert descriptor.enabled is True
    assert descriptor.availability == "ready"
    assert descriptor.network_allowed is False


def test_fake_provider_implements_membrane_and_is_deterministic() -> None:
    provider = build_deterministic_fake_laboratory_provider()
    assert isinstance(provider, LaboratoryProvider)

    first = provider.execute(request())
    second = provider.execute(request())
    assert first.to_mapping() == second.to_mapping()
    assert first.status == "completed"
    assert first.machine_result["deterministic"] is True
    assert first.machine_result["real_backend_used"] is False
    json.dumps(first.to_mapping(), sort_keys=True)


def test_handler_membrane_returns_bounded_execution_record() -> None:
    record = execute_deterministic_fake_laboratory_visit(request())
    payload = record.to_mapping()
    assert payload["result_valid"] is True
    assert payload["validation_issues"] == []
    assert payload["scheduler_path_required"] is True
    assert payload["provider_owns_orchestration"] is False
    assert payload["provider_owns_persistence"] is False
    assert payload["provider_owns_vector_index"] is False
    assert payload["provider_uses_network"] is False
    assert payload["real_backend_used"] is False
    json.dumps(payload, sort_keys=True)


def test_fake_provider_supports_context_and_specialist_followups() -> None:
    context_result = execute_deterministic_fake_laboratory_visit(
        request(metadata=(("fake_scenario", "needs_context"),))
    ).result
    assert context_result.status == "needs_context"
    assert context_result.requested_context_refs
    assert context_result.followup_request_refs

    specialist_result = execute_deterministic_fake_laboratory_visit(
        request(metadata=(("fake_scenario", "needs_specialist"),))
    ).result
    assert specialist_result.status == "needs_specialist"
    assert specialist_result.requested_specialist_refs == ("specialist:validator",)


def test_fake_provider_rejects_network_and_wrong_laboratory() -> None:
    network_budget = LaboratoryResourceBudget(
        allow_network=True,
        max_external_calls=1,
    )
    with pytest.raises(LaboratoryProviderExecutionError, match="network-enabled"):
        execute_deterministic_fake_laboratory_visit(
            request(resource_budget=network_budget)
        )

    provider = build_deterministic_fake_laboratory_provider()
    with pytest.raises(LaboratoryProviderExecutionError, match="laboratory_ref"):
        provider.execute(
            request(
                laboratory_ref="laboratory:other",
                target_laboratory_ref="laboratory:other",
            )
        )


def test_fake_provider_rejects_unsupported_scenario() -> None:
    with pytest.raises(LaboratoryProviderExecutionError, match="unsupported"):
        execute_deterministic_fake_laboratory_visit(
            request(metadata=(("fake_scenario", "unknown"),))
        )


def test_fake_provider_constructor_rejects_wrong_descriptor() -> None:
    base = build_deterministic_fake_laboratory_descriptor()
    wrong = LaboratoryDescriptor(
        schema=base.schema,
        laboratory_ref="laboratory:other",
        provider_kind="local_fake",
        display_name=base.display_name,
        capabilities=base.capabilities,
        accepted_input_contract_refs=base.accepted_input_contract_refs,
        produced_output_contract_refs=base.produced_output_contract_refs,
        execution_boundary="in_process",
        availability="ready",
        enabled=True,
        network_allowed=False,
    )
    with pytest.raises(LaboratoryContractError, match="local-fake"):
        DeterministicFakeLaboratoryProvider(wrong)


def test_binding_plan_and_registration_target_existing_registry_type() -> None:
    plan = build_deterministic_fake_laboratory_binding_plan()
    registration = build_deterministic_fake_laboratory_registration()
    assert plan.provider_active is True
    assert plan.ready_for_registry_attachment is True
    assert plan.creates_parallel_registry is False
    assert plan.modifies_scheduler_run is False
    assert isinstance(registration, SchedulerOwnedRuntimeComponentRegistration)
    assert registration.component_id == DETERMINISTIC_FAKE_COMPONENT_ID
    assert registration.surface == "laboratory_provider"
    assert registration.owner == "scheduler"
    assert registration.role == "command"
    assert registration.selected_from_existing_surfaces is False


def test_binding_appends_to_existing_registry_and_replay_is_idempotent() -> None:
    registry = build_scheduler_owned_runtime_registry()
    bound = bind_deterministic_fake_laboratory_registration(registry)
    assert not validate_scheduler_owned_runtime_registry(bound)
    ids = tuple(item.component_id for item in bound.registrations)
    assert ids[-1] == DETERMINISTIC_FAKE_COMPONENT_ID

    replayed = bind_deterministic_fake_laboratory_registration(bound)
    assert replayed is bound


def test_binding_rejects_conflicting_registration() -> None:
    registry = build_scheduler_owned_runtime_registry()
    conflicting = SchedulerOwnedRuntimeComponentRegistration(
        component_id=DETERMINISTIC_FAKE_COMPONENT_ID,
        surface="wrong",
        owner="scheduler",
        role="command",
        capabilities=("laboratory.visit.execute",),
        depends_on=(),
        source_paths=("src/context/wrong.py",),
    )
    conflicting_registry = type(registry)(
        registrations=registry.registrations + (conflicting,),
        source_map_complete=registry.source_map_complete,
    )
    with pytest.raises(LaboratoryContractError, match="conflicting"):
        bind_deterministic_fake_laboratory_registration(conflicting_registry)
