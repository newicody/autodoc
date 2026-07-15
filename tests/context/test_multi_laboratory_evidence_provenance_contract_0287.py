from __future__ import annotations

from hashlib import sha256

import pytest

from context.laboratory_framework_contract_0273 import (
    LABORATORY_VISIT_REQUEST_SCHEMA,
    LABORATORY_VISIT_RESULT_SCHEMA,
    LaboratoryResourceBudget,
    LaboratoryVisitRequest,
    LaboratoryVisitResult,
)
from context.multi_laboratory_evidence_aggregation_contract_0287 import (
    MULTI_LABORATORY_EVIDENCE_AGGREGATE_SCHEMA,
    MULTI_LABORATORY_EVIDENCE_ITEM_SCHEMA,
    MultiLaboratoryEvidenceAggregate,
    MultiLaboratoryEvidenceItem,
)
from context.multi_laboratory_evidence_provenance_contract_0287 import (
    MULTI_LABORATORY_EVIDENCE_PROVENANCE_SCHEMA,
    MultiLaboratoryEvidenceProvenance,
    MultiLaboratoryEvidenceProvenanceContractError,
    multi_laboratory_evidence_provenance_from_visit,
    validate_multi_laboratory_evidence_provenance,
)
from context.specialist_laboratory_transfer_contract_0284 import (
    SPECIALIST_TRANSFER_REQUEST_SCHEMA,
    SPECIALIST_TRANSFER_RESULT_SCHEMA,
    SPECIALIST_TRANSFER_VISIT_PLAN_SCHEMA,
    SpecialistTransferRequest,
    SpecialistTransferResult,
    SpecialistTransferVisitPlan,
)


def _item(index: int) -> MultiLaboratoryEvidenceItem:
    return MultiLaboratoryEvidenceItem(
        schema=MULTI_LABORATORY_EVIDENCE_ITEM_SCHEMA,
        evidence_ref=f"artifact:evidence-{index}",
        evidence_kind="execution_result",
        subject_ref="requirement:chalouf-drive",
        specialist_ref=f"specialist:technical-{index}",
        capability="technical.review",
        source_ref=f"result:visit-{index}",
        provenance_ref=f"provenance:visit-{index}",
        digest_sha256=sha256(f"content-{index}".encode()).hexdigest(),
        claim_key="technical.review",
        claim_value=f"claim {index}",
        claim_relation="supports",
    )


def _aggregate() -> MultiLaboratoryEvidenceAggregate:
    return MultiLaboratoryEvidenceAggregate(
        schema=MULTI_LABORATORY_EVIDENCE_AGGREGATE_SCHEMA,
        aggregation_ref="aggregation:chalouf-drive:1",
        subject_ref="requirement:chalouf-drive",
        conversation_ref="conversation:chalouf-drive",
        context_refs=("context:design",),
        evidence_items=(_item(1), _item(2)),
        aggregation_policy_ref="policy:multi-laboratory-evidence:v1",
    )


def _visit(index: int, laboratory: str) -> tuple[LaboratoryVisitRequest, LaboratoryVisitResult]:
    request = LaboratoryVisitRequest(
        schema=LABORATORY_VISIT_REQUEST_SCHEMA,
        visit_ref=f"laboratory-visit:{index}",
        laboratory_ref=laboratory,
        specialist_ref=f"specialist:technical-{index}",
        objective_ref="objective:technical-review",
        source_candidate_ref="candidate:chalouf-drive",
        context_generation=1,
        input_contract_ref="contract:technical-input:v1",
        expected_output_contract_ref="contract:technical-output:v1",
        resource_budget=LaboratoryResourceBudget(),
        return_route_ref="route:scheduler",
        context_refs=("ctx:design",),
    )
    result = LaboratoryVisitResult(
        schema=LABORATORY_VISIT_RESULT_SCHEMA,
        visit_ref=request.visit_ref,
        laboratory_ref=laboratory,
        specialist_ref=request.specialist_ref,
        status="completed",
        output_contract_ref=request.expected_output_contract_ref,
        machine_result={"claim": index},
        human_representation=f"claim {index}",
        confidence=0.8,
        evidence_refs=(f"artifact:evidence-{index}",),
    )
    return request, result


def test_visit_factory_binds_existing_visit_contract() -> None:
    request, result = _visit(1, "laboratory:local-a")
    provenance = multi_laboratory_evidence_provenance_from_visit(
        _item(1), request, result
    )
    assert provenance.schema == MULTI_LABORATORY_EVIDENCE_PROVENANCE_SCHEMA
    assert provenance.laboratory_ref == "laboratory:local-a"
    assert provenance.visit_ref == "laboratory-visit:1"
    assert provenance.evidence_ref == "artifact:evidence-1"
    assert provenance.cross_laboratory is False
    assert len(provenance.provenance_digest) == 64


def test_factory_rejects_evidence_absent_from_visit_result() -> None:
    request, result = _visit(1, "laboratory:local-a")
    wrong = LaboratoryVisitResult(
        schema=result.schema,
        visit_ref=result.visit_ref,
        laboratory_ref=result.laboratory_ref,
        specialist_ref=result.specialist_ref,
        status=result.status,
        output_contract_ref=result.output_contract_ref,
        machine_result=result.machine_result,
        human_representation=result.human_representation,
        confidence=result.confidence,
        evidence_refs=("artifact:other",),
    )
    with pytest.raises(MultiLaboratoryEvidenceProvenanceContractError, match="present"):
        multi_laboratory_evidence_provenance_from_visit(_item(1), request, wrong)


def test_two_distinct_laboratories_validate_the_aggregate() -> None:
    p1 = multi_laboratory_evidence_provenance_from_visit(
        _item(1), *_visit(1, "laboratory:local-a")
    )
    p2 = multi_laboratory_evidence_provenance_from_visit(
        _item(2), *_visit(2, "laboratory:local-b")
    )
    result = validate_multi_laboratory_evidence_provenance(_aggregate(), (p2, p1))
    assert result.valid is True
    assert result.multi_laboratory_confirmed is True
    assert result.provenance_chain_validated is True
    assert result.laboratory_refs == (
        "laboratory:local-a", "laboratory:local-b"
    )
    assert len(result.validation_digest) == 64


def test_two_provenance_refs_from_one_laboratory_are_not_multi_laboratory() -> None:
    p1 = multi_laboratory_evidence_provenance_from_visit(
        _item(1), *_visit(1, "laboratory:local-a")
    )
    p2 = multi_laboratory_evidence_provenance_from_visit(
        _item(2), *_visit(2, "laboratory:local-a")
    )
    result = validate_multi_laboratory_evidence_provenance(_aggregate(), (p1, p2))
    assert result.valid is False
    assert result.multi_laboratory_confirmed is False


def test_missing_provenance_is_detected() -> None:
    p1 = multi_laboratory_evidence_provenance_from_visit(
        _item(1), *_visit(1, "laboratory:local-a")
    )
    result = validate_multi_laboratory_evidence_provenance(_aggregate(), (p1,))
    assert result.valid is False
    assert any("missing provenance" in issue for issue in result.issues)


def test_cross_laboratory_visit_reuses_transfer_chain() -> None:
    item = _item(2)
    transfer_request = SpecialistTransferRequest(
        schema=SPECIALIST_TRANSFER_REQUEST_SCHEMA,
        transfer_ref="specialist-transfer:1",
        mode="transfer",
        specialist_ref=item.specialist_ref,
        conversation_ref="laboratory-conversation:chalouf",
        source_visit_ref="laboratory-visit:1",
        requested_by_message_ref="laboratory-message:1",
        origin_laboratory_ref="laboratory:local-a",
        target_laboratory_ref="laboratory:local-b",
        input_contract_ref="contract:technical-input:v1",
        expected_output_contract_ref="contract:technical-output:v1",
        return_route_ref="route:scheduler",
        context_refs=("ctx:design",),
        evidence_refs=(item.evidence_ref,),
    )
    plan = SpecialistTransferVisitPlan(
        schema=SPECIALIST_TRANSFER_VISIT_PLAN_SCHEMA,
        transfer_ref=transfer_request.transfer_ref,
        target_visit_ref="laboratory-visit:2",
        specialist_ref=item.specialist_ref,
        laboratory_ref="laboratory:local-b",
        origin_laboratory_ref="laboratory:local-a",
        target_laboratory_ref="laboratory:local-b",
        conversation_ref=transfer_request.conversation_ref,
        parent_visit_ref=transfer_request.source_visit_ref,
        input_contract_ref=transfer_request.input_contract_ref,
        expected_output_contract_ref=transfer_request.expected_output_contract_ref,
        return_route_ref=transfer_request.return_route_ref,
        visit_mode="transfer",
        context_refs=transfer_request.context_refs,
        evidence_refs=transfer_request.evidence_refs,
    )
    transfer_result = SpecialistTransferResult(
        schema=SPECIALIST_TRANSFER_RESULT_SCHEMA,
        transfer_ref=transfer_request.transfer_ref,
        mode="transfer",
        status="completed",
        specialist_ref=item.specialist_ref,
        conversation_ref=transfer_request.conversation_ref,
        source_visit_ref=transfer_request.source_visit_ref,
        target_visit_ref=plan.target_visit_ref,
        origin_laboratory_ref="laboratory:local-a",
        target_laboratory_ref="laboratory:local-b",
        active_laboratory_ref="laboratory:local-b",
        return_route_ref=transfer_request.return_route_ref,
        reason="validated transfer",
        context_refs=transfer_request.context_refs,
        evidence_refs=(item.evidence_ref,),
    )
    request = LaboratoryVisitRequest(
        schema=LABORATORY_VISIT_REQUEST_SCHEMA,
        visit_ref=plan.target_visit_ref,
        laboratory_ref="laboratory:local-b",
        specialist_ref=item.specialist_ref,
        objective_ref="objective:technical-review",
        source_candidate_ref="candidate:chalouf-drive",
        context_generation=2,
        input_contract_ref=plan.input_contract_ref,
        expected_output_contract_ref=plan.expected_output_contract_ref,
        resource_budget=LaboratoryResourceBudget(),
        return_route_ref=plan.return_route_ref,
        context_refs=("ctx:design",),
        origin_laboratory_ref="laboratory:local-a",
        target_laboratory_ref="laboratory:local-b",
        conversation_ref=plan.conversation_ref,
        parent_visit_ref=plan.parent_visit_ref,
    )
    result = LaboratoryVisitResult(
        schema=LABORATORY_VISIT_RESULT_SCHEMA,
        visit_ref=request.visit_ref,
        laboratory_ref=request.laboratory_ref,
        specialist_ref=request.specialist_ref,
        status="completed",
        output_contract_ref=request.expected_output_contract_ref,
        machine_result={"claim": 2},
        human_representation="claim 2",
        confidence=0.9,
        evidence_refs=(item.evidence_ref,),
        conversation_ref=request.conversation_ref,
        parent_visit_ref=request.parent_visit_ref,
    )
    provenance = multi_laboratory_evidence_provenance_from_visit(
        item,
        request,
        result,
        transfer_request=transfer_request,
        transfer_plan=plan,
        transfer_result=transfer_result,
    )
    assert provenance.cross_laboratory is True
    assert provenance.transfer_ref == "specialist-transfer:1"
    assert provenance.parent_visit_ref == "laboratory-visit:1"


def test_mapping_keeps_later_phase_boundaries_closed() -> None:
    p1 = multi_laboratory_evidence_provenance_from_visit(
        _item(1), *_visit(1, "laboratory:local-a")
    )
    p2 = multi_laboratory_evidence_provenance_from_visit(
        _item(2), *_visit(2, "laboratory:local-b")
    )
    mapping = validate_multi_laboratory_evidence_provenance(
        _aggregate(), (p1, p2)
    ).to_mapping()
    assert mapping["provenance_chain_validated"] is True
    assert mapping["authoritative"] is False
    assert mapping["approved"] is False
    assert mapping["deduplication_performed"] is False
    assert mapping["contradiction_detection_performed"] is False
    assert mapping["weighting_authorized"] is False
    assert mapping["durable_state_written"] is False
    assert mapping["scheduler_selection_allowed"] is False
    assert mapping["sql_remains_durable_authority"] is True
    assert mapping["scheduler_remains_only_orchestrator"] is True
