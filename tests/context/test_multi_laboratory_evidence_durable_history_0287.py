from dataclasses import FrozenInstanceError

import pytest

from context.multi_laboratory_evidence_durable_history_0287 import (
    MULTI_LABORATORY_EVIDENCE_HISTORY_APPEND_COMMAND_SCHEMA,
    DeterministicMultiLaboratoryEvidenceHistoryAdapter,
    MultiLaboratoryEvidenceDurableHistoryError,
    MultiLaboratoryEvidenceHistoryAppendCommand,
    MultiLaboratoryEvidenceHistoryConflictError,
    MultiLaboratoryEvidenceHistoryPort,
)
from context.multi_laboratory_evidence_operator_weighting_policy_0287 import (
    MULTI_LABORATORY_EVIDENCE_WEIGHTING_DECISION_SCHEMA,
    MultiLaboratoryEvidenceWeightingDecision,
)


def _decision(index: int, outcome: str = "approve"):
    return MultiLaboratoryEvidenceWeightingDecision(
        schema=MULTI_LABORATORY_EVIDENCE_WEIGHTING_DECISION_SCHEMA,
        decision_ref=f"decision:weighting-{index}",
        outcome=outcome,
        operator_ref="operator:eric",
        policy_ref="policy:weighting:v1",
        policy_digest="a" * 64,
        aggregation_ref="aggregation:chalouf-drive:1",
        detection_digest="b" * 64,
        weights=(),
        contradiction_dispositions=(),
        canonical_evidence_refs=(),
        contradiction_refs=(),
        operator_reviewed_contradiction_refs=(),
        unresolved_contradiction_refs=(),
        reason="operator reviewed",
        policy_issues=(),
        weighting_digest=f"{index:064x}",
    )


def _command(index, *, count=0, head="0" * 64, outcome="approve"):
    return MultiLaboratoryEvidenceHistoryAppendCommand(
        schema=(
            MULTI_LABORATORY_EVIDENCE_HISTORY_APPEND_COMMAND_SCHEMA
        ),
        history_ref="history:chalouf-evidence",
        entry_ref=f"history-entry:chalouf-{index}",
        sql_ref=f"sql:evidence-history:{index}",
        decision=_decision(index, outcome),
        expected_entry_count=count,
        expected_head_entry_digest=head,
    )


def test_first_append_and_sql_authority_contract():
    adapter = DeterministicMultiLaboratoryEvidenceHistoryAdapter()
    result = adapter.append(_command(1))
    assert result.inserted is True
    assert result.entry.sequence_number == 1
    assert result.durable_write_performed is False
    assert result.to_mapping()["authority_contract"] == "sql"


def test_second_append_continues_digest_chain():
    adapter = DeterministicMultiLaboratoryEvidenceHistoryAdapter()
    first = adapter.append(_command(1))
    second = adapter.append(
        _command(2, count=1, head=first.snapshot.head_entry_digest)
    )
    assert second.entry.previous_entry_digest == first.entry.entry_digest
    assert len(second.snapshot.entries) == 2


def test_exact_replay_is_idempotent():
    adapter = DeterministicMultiLaboratoryEvidenceHistoryAdapter()
    command = _command(1)
    first = adapter.append(command)
    replay = adapter.append(command)
    assert first.inserted is True
    assert replay.inserted is False


def test_reused_entry_ref_with_other_content_conflicts():
    adapter = DeterministicMultiLaboratoryEvidenceHistoryAdapter()
    first = adapter.append(_command(1))
    command = MultiLaboratoryEvidenceHistoryAppendCommand(
        schema=MULTI_LABORATORY_EVIDENCE_HISTORY_APPEND_COMMAND_SCHEMA,
        history_ref="history:chalouf-evidence",
        entry_ref="history-entry:chalouf-1",
        sql_ref="sql:evidence-history:other",
        decision=_decision(2),
        expected_entry_count=1,
        expected_head_entry_digest=first.snapshot.head_entry_digest,
    )
    with pytest.raises(
        MultiLaboratoryEvidenceHistoryConflictError,
        match="different content",
    ):
        adapter.append(command)


def test_optimistic_count_and_head_are_enforced():
    adapter = DeterministicMultiLaboratoryEvidenceHistoryAdapter()
    first = adapter.append(_command(1))
    with pytest.raises(
        MultiLaboratoryEvidenceHistoryConflictError,
        match="expected_entry_count",
    ):
        adapter.append(
            _command(2, count=0, head="0" * 64)
        )
    with pytest.raises(
        MultiLaboratoryEvidenceHistoryConflictError,
        match="head digest",
    ):
        adapter.append(_command(2, count=1, head="f" * 64))


def test_reject_and_defer_cannot_be_appended():
    for outcome in ("reject", "defer"):
        with pytest.raises(
            MultiLaboratoryEvidenceDurableHistoryError,
            match="operator-approved",
        ):
            _command(1, outcome=outcome)


def test_adapter_implements_port_but_is_not_durable():
    adapter = DeterministicMultiLaboratoryEvidenceHistoryAdapter()
    assert isinstance(adapter, MultiLaboratoryEvidenceHistoryPort)
    assert adapter.authority_contract == "sql"
    assert adapter.durable is False


def test_snapshot_is_immutable_and_boundaries_are_closed():
    result = DeterministicMultiLaboratoryEvidenceHistoryAdapter().append(
        _command(1)
    )
    mapping = result.to_mapping()
    assert mapping["qdrant_write_performed"] is False
    assert mapping["scheduler_selection_performed"] is False
    assert mapping["eventbus_observation_published"] is False
    assert mapping["github_mutation_performed"] is False
    with pytest.raises(FrozenInstanceError):
        result.snapshot.history_ref = "history:other"
