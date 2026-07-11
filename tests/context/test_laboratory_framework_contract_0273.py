from dataclasses import FrozenInstanceError
import json

import pytest

from context.laboratory_framework_contract_0273 import (
    LABORATORY_DESCRIPTOR_SCHEMA,
    LABORATORY_REGISTRY_BINDING_SCHEMA,
    LABORATORY_VISIT_REQUEST_SCHEMA,
    LABORATORY_VISIT_RESULT_SCHEMA,
    LaboratoryContractError,
    LaboratoryDescriptor,
    LaboratoryRegistryBindingPlan,
    LaboratoryResourceBudget,
    LaboratoryVisitRequest,
    LaboratoryVisitResult,
    build_laboratory_registry_binding_plan,
    validate_laboratory_visit_result,
)


def descriptor(**overrides):
    values = {
        "schema": LABORATORY_DESCRIPTOR_SCHEMA,
        "laboratory_ref": "laboratory:local-fake",
        "provider_kind": "local_fake",
        "display_name": "Local deterministic fake",
        "capabilities": (
            "laboratory.visit.execute",
            "laboratory.specialist.simulate",
        ),
        "accepted_input_contract_refs": (
            "contract:missipy.laboratory.visit_request.v1",
        ),
        "produced_output_contract_refs": (
            "contract:missipy.laboratory.visit_result.v1",
        ),
        "execution_boundary": "in_process",
    }
    values.update(overrides)
    return LaboratoryDescriptor(**values)


def request(**overrides):
    values = {
        "schema": LABORATORY_VISIT_REQUEST_SCHEMA,
        "visit_ref": "laboratory-visit:test-001",
        "laboratory_ref": "laboratory:local-fake",
        "specialist_ref": "specialist:technical",
        "objective_ref": "orientation:test-001",
        "source_candidate_ref": "source-candidate:test-001",
        "context_generation": 1,
        "input_contract_ref": "contract:missipy.specialist.demand.v1",
        "expected_output_contract_ref": (
            "contract:missipy.laboratory.visit_result.v1"
        ),
        "resource_budget": LaboratoryResourceBudget(),
        "return_route_ref": "route:laboratory/test-001/result",
        "context_refs": ("sql:context:test-001",),
        "evidence_refs": ("artifact:evidence:test-001",),
    }
    values.update(overrides)
    return LaboratoryVisitRequest(**values)


def result(**overrides):
    values = {
        "schema": LABORATORY_VISIT_RESULT_SCHEMA,
        "visit_ref": "laboratory-visit:test-001",
        "laboratory_ref": "laboratory:local-fake",
        "specialist_ref": "specialist:technical",
        "status": "completed",
        "output_contract_ref": "contract:missipy.laboratory.visit_result.v1",
        "machine_result": {
            "finding": "deterministic",
            "scores": [1, 2, 3],
            "details": {"safe": True},
        },
        "human_representation": "Deterministic fake result.",
        "confidence": 0.75,
        "evidence_refs": ("artifact:evidence:test-001",),
        "provenance_refs": ("sql:context:test-001",),
    }
    values.update(overrides)
    return LaboratoryVisitResult(**values)


def test_descriptor_is_immutable_serializable_and_inactive() -> None:
    item = descriptor()
    payload = item.to_mapping()

    assert payload["provider_instantiated"] is False
    assert payload["registry_attached"] is False
    assert payload["enabled"] is False
    assert payload["availability"] == "declared"
    json.dumps(payload, sort_keys=True)

    with pytest.raises(FrozenInstanceError):
        item.display_name = "changed"  # type: ignore[misc]


def test_descriptor_rejects_unready_enabled_or_invalid_capabilities() -> None:
    with pytest.raises(LaboratoryContractError, match="availability ready"):
        descriptor(enabled=True)
    with pytest.raises(LaboratoryContractError, match="invalid laboratory capability"):
        descriptor(capabilities=("INVALID CAPABILITY",))


def test_resource_budget_is_bounded_and_network_explicit() -> None:
    with pytest.raises(LaboratoryContractError, match="max_duration_ms"):
        LaboratoryResourceBudget(max_duration_ms=0)
    with pytest.raises(LaboratoryContractError, match="max_external_calls"):
        LaboratoryResourceBudget(max_external_calls=1)
    allowed = LaboratoryResourceBudget(
        allow_network=True,
        max_external_calls=2,
    )
    assert allowed.to_mapping()["max_external_calls"] == 2


def test_visit_request_defaults_to_same_laboratory_and_scheduler_path() -> None:
    item = request()
    payload = item.to_mapping()

    assert item.origin_laboratory_ref == "laboratory:local-fake"
    assert item.target_laboratory_ref == "laboratory:local-fake"
    assert payload["next_boundary"] == "Scheduler.emit()"
    assert payload["direct_backend_access_allowed"] is False
    assert payload["publication_allowed"] is False
    json.dumps(payload, sort_keys=True)


def test_cross_laboratory_request_requires_conversation_and_target_match() -> None:
    with pytest.raises(LaboratoryContractError, match="conversation_ref"):
        request(origin_laboratory_ref="laboratory:autodoc-native")
    moved = request(
        origin_laboratory_ref="laboratory:autodoc-native",
        conversation_ref="laboratory-conversation:test-001",
    )
    assert moved.origin_laboratory_ref == "laboratory:autodoc-native"

    with pytest.raises(LaboratoryContractError, match="must match laboratory_ref"):
        request(target_laboratory_ref="laboratory:other")


def test_visit_request_enforces_context_and_evidence_budgets() -> None:
    tiny = LaboratoryResourceBudget(max_context_refs=0, max_evidence_refs=0)
    with pytest.raises(LaboratoryContractError, match="context_refs exceed"):
        request(resource_budget=tiny)


def test_visit_result_deep_freezes_machine_result_and_serializes() -> None:
    item = result()
    assert tuple(item.machine_result["scores"]) == (1, 2, 3)
    with pytest.raises(TypeError):
        item.machine_result["new"] = "forbidden"  # type: ignore[index]

    payload = item.to_mapping()
    assert payload["machine_result"]["scores"] == [1, 2, 3]
    assert payload["eventbus_command_allowed"] is False
    json.dumps(payload, sort_keys=True)


def test_completed_result_requires_machine_result() -> None:
    with pytest.raises(LaboratoryContractError, match="requires a machine_result"):
        result(machine_result={})


def test_result_validation_checks_identity_output_and_bounds() -> None:
    req = request()
    assert validate_laboratory_visit_result(req, result()) == ()

    bad = result(
        visit_ref="laboratory-visit:other",
        human_representation="x" * 40_000,
    )
    issues = validate_laboratory_visit_result(req, bad)
    assert "result visit_ref must match request" in issues
    assert "result human_representation exceeds max_output_chars" in issues


def test_external_laboratory_followup_requires_network_budget() -> None:
    issues = validate_laboratory_visit_result(
        request(),
        result(requested_laboratory_refs=("laboratory:external",)),
    )
    assert (
        "external laboratory request requires a network-enabled budget"
        in issues
    )


def test_registry_binding_targets_existing_registry_but_stays_inactive() -> None:
    plan = build_laboratory_registry_binding_plan(descriptor())
    payload = plan.to_mapping()

    assert plan.schema == LABORATORY_REGISTRY_BINDING_SCHEMA
    assert (
        payload["target_registry_module"]
        == "context.scheduler_owned_runtime_registry_0257"
    )
    assert (
        payload["target_registration_type"]
        == "SchedulerOwnedRuntimeComponentRegistration"
    )
    assert payload["owner"] == "scheduler"
    assert payload["ready_for_registry_attachment"] is False
    assert payload["provider_active"] is False
    assert payload["creates_parallel_registry"] is False
    assert payload["modifies_scheduler_run"] is False
    json.dumps(payload, sort_keys=True)


def test_registry_binding_refuses_parallel_authorities() -> None:
    with pytest.raises(LaboratoryContractError, match="parallel authorities"):
        LaboratoryRegistryBindingPlan(
            schema=LABORATORY_REGISTRY_BINDING_SCHEMA,
            laboratory_ref="laboratory:bad",
            component_id="laboratory_provider_bad",
            capabilities=("laboratory.visit.execute",),
            creates_runtime_manager=True,
        )
