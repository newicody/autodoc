from dataclasses import FrozenInstanceError, dataclass, replace
from copy import deepcopy

import pytest

from context.specialist_capability_growth_projects_review_projection_0286 import (
    SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_SCHEMA,
    SpecialistCapabilityGrowthProjectsReviewProjectionError,
    build_specialist_capability_growth_projects_review_projection,
)


HASHES = {name: character * 64 for name, character in {
    "smoke": "a",
    "proposal": "b",
    "revision": "c",
    "decision": "d",
    "entry": "e",
    "snapshot": "f",
    "selection": "1",
}.items()}


@dataclass(frozen=True)
class ClosedLoopSource:
    payload: dict[str, object]
    smoke_digest: str = HASHES["smoke"]

    def to_mapping(self, *, include_digest: bool = True):
        mapping = deepcopy(self.payload)
        if include_digest:
            mapping["smoke_digest"] = self.smoke_digest
        return mapping


def _payload() -> dict[str, object]:
    proposal = {
        "proposal_ref": "proposal:0286-r2:technical",
        "proposal_digest": HASHES["proposal"],
        "specialist_ref": "specialist:technical",
        "base_specialist_version": "1.0.0",
        "action": "add",
        "capability": "laboratory.analysis",
        "evidence_refs": [
            {
                "evidence_ref": "evidence:0286-r2:test-report",
                "digest_sha256": "2" * 64,
            }
        ],
        "conversation_ref": "conversation:0286-r2",
        "context_refs": ["context:0286-r2", "sql:context:0286-r2"],
    }
    revision = {
        "revision_ref": "revision:technical:2",
        "specialist_ref": "specialist:technical",
        "specialist_version": "1.1.0",
        "source_proposal_ref": proposal["proposal_ref"],
        "source_proposal_digest_sha256": HASHES["proposal"],
        "revision_digest": HASHES["revision"],
    }
    decision = {
        "decision_ref": "decision:0286-r2:approve",
        "decision_digest": HASHES["decision"],
        "outcome": "approve",
        "operator_ref": "operator:eric",
        "reason": "Approved for controlled Projects review.",
        "proposal_ref": proposal["proposal_ref"],
        "proposal_digest_sha256": HASHES["proposal"],
        "candidate_revision_ref": revision["revision_ref"],
        "candidate_revision_digest_sha256": HASHES["revision"],
        "specialist_ref": proposal["specialist_ref"],
        "revision_authorized": True,
    }
    entry = {
        "history_ref": "history:technical",
        "entry_ref": "history-entry:technical:1",
        "entry_digest": HASHES["entry"],
        "sql_ref": "sql:specialist-history:technical:1",
        "specialist_ref": proposal["specialist_ref"],
        "decision": decision,
        "revision": revision,
    }
    selection = {
        "selection_ref": "selection:technical:2",
        "selection_digest": HASHES["selection"],
        "scheduler_ref": "scheduler:main",
        "history_ref": entry["history_ref"],
        "history_snapshot_digest_sha256": HASHES["snapshot"],
        "history_entry_ref": entry["entry_ref"],
        "history_entry_digest_sha256": HASHES["entry"],
        "sql_ref": entry["sql_ref"],
        "decision_ref": decision["decision_ref"],
        "selected_revision": revision,
        "specialist_ref": proposal["specialist_ref"],
        "capability": proposal["capability"],
        "laboratory_ref": "laboratory:local-fake",
        "visit_mode": "visitor",
        "execution_boundary": "in_process",
        "conversation_ref": proposal["conversation_ref"],
        "context_refs": proposal["context_refs"],
    }
    observation_projection = {
        "selection_ref": selection["selection_ref"],
        "selection_digest_sha256": HASHES["selection"],
        "specialist_ref": proposal["specialist_ref"],
        "revision_ref": revision["revision_ref"],
        "proposal_ref": proposal["proposal_ref"],
        "decision_ref": decision["decision_ref"],
        "history_entry_ref": entry["entry_ref"],
        "sql_ref": entry["sql_ref"],
    }
    passive_read_model = {
        "selection_ref": selection["selection_ref"],
        "specialist_ref": proposal["specialist_ref"],
        "revision_ref": revision["revision_ref"],
        "proposal_ref": proposal["proposal_ref"],
        "decision_ref": decision["decision_ref"],
        "history_entry_ref": entry["entry_ref"],
        "sql_ref": entry["sql_ref"],
        "valid": True,
    }
    return {
        "command": {
            "smoke_ref": "smoke:0285-r8:technical",
            "proposal": proposal,
            "candidate_revision": revision,
        },
        "decision": decision,
        "history_result": {
            "entry": entry,
            "snapshot": {
                "history_ref": entry["history_ref"],
                "snapshot_digest": HASHES["snapshot"],
            },
            "durable_write_performed": True,
        },
        "selection": selection,
        "laboratory_result": {"valid": True},
        "observation_publication": {
            "projection": observation_projection,
            "event_id": "event-0285-r8-technical",
            "published_count": 1,
        },
        "passive_read_model": passive_read_model,
        "phase_0285_closed": True,
        "issues": [],
        "operator_gate_closed": True,
        "durable_sql_history_recorded": True,
        "scheduler_selection_performed": True,
        "laboratory_execution_performed": True,
        "eventbus_observation_published": True,
        "passive_supervisor_read_model_valid": True,
        "qdrant_authoritative": False,
        "github_mutation_performed": False,
        "new_scheduler_created": False,
        "parallel_orchestrator_created": False,
    }


def _projection():
    return build_specialist_capability_growth_projects_review_projection(
        ClosedLoopSource(_payload()),
        review_ref="projects-review:0286-r2:technical",
        metadata=(("source", "phase-0285"),),
    )


def test_builds_non_authoritative_review_projection_from_closed_0285_evidence() -> None:
    projection = _projection()

    assert projection.schema == (
        SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_SCHEMA
    )
    assert projection.specialist_ref == "specialist:technical"
    assert projection.revision_ref == "revision:technical:2"
    assert projection.decision_outcome == "approve"
    assert projection.review_status == "approved_selected_observed"
    assert projection.github_projects_authoritative is False
    assert projection.publication_performed is False


def test_projection_preserves_sql_scheduler_laboratory_and_context_refs() -> None:
    projection = _projection()

    assert projection.sql_ref == "sql:specialist-history:technical:1"
    assert projection.scheduler_ref == "scheduler:main"
    assert projection.laboratory_ref == "laboratory:local-fake"
    assert projection.conversation_ref == "conversation:0286-r2"
    assert projection.context_refs == (
        "context:0286-r2",
        "sql:context:0286-r2",
    )


def test_projectv2_fields_are_preview_values_only() -> None:
    projection = _projection()
    fields = dict(projection.projectv2_field_values)

    assert fields["Spécialiste"] == "specialist:technical"
    assert fields["Révision spécialiste"] == "revision:technical:2"
    assert fields["Décision capacité"] == "approve"
    assert fields["Référence SQL"] == "sql:specialist-history:technical:1"
    assert projection.projectv2_mutation_performed is False
    assert projection.issue_comment_published is False


def test_projection_digest_is_deterministic() -> None:
    left = _projection()
    right = _projection()

    assert left.projection_digest == right.projection_digest
    assert len(left.projection_digest) == 64


def test_projection_is_immutable() -> None:
    projection = _projection()

    with pytest.raises(FrozenInstanceError):
        projection.review_status = "published"


def test_rejects_unclosed_phase_0285_source() -> None:
    payload = _payload()
    payload["phase_0285_closed"] = False

    with pytest.raises(
        SpecialistCapabilityGrowthProjectsReviewProjectionError,
        match="phase_0285_closed",
    ):
        build_specialist_capability_growth_projects_review_projection(
            ClosedLoopSource(payload),
            review_ref="projects-review:0286-r2:technical",
        )


def test_rejects_non_durable_history_evidence() -> None:
    payload = _payload()
    payload["durable_sql_history_recorded"] = False

    with pytest.raises(
        SpecialistCapabilityGrowthProjectsReviewProjectionError,
        match="durable_sql_history_recorded",
    ):
        build_specialist_capability_growth_projects_review_projection(
            ClosedLoopSource(payload),
            review_ref="projects-review:0286-r2:technical",
        )


def test_rejects_reference_correlation_drift() -> None:
    payload = _payload()
    payload["selection"]["sql_ref"] = "sql:other"  # type: ignore[index]

    with pytest.raises(
        SpecialistCapabilityGrowthProjectsReviewProjectionError,
        match="correlation drift",
    ):
        build_specialist_capability_growth_projects_review_projection(
            ClosedLoopSource(payload),
            review_ref="projects-review:0286-r2:technical",
        )


def test_rejects_digest_correlation_drift() -> None:
    payload = _payload()
    payload["selection"]["selection_digest"] = "9" * 64  # type: ignore[index]

    with pytest.raises(
        SpecialistCapabilityGrowthProjectsReviewProjectionError,
        match="digest drift",
    ):
        build_specialist_capability_growth_projects_review_projection(
            ClosedLoopSource(payload),
            review_ref="projects-review:0286-r2:technical",
        )


def test_mapping_preserves_authority_boundaries() -> None:
    mapping = _projection().to_mapping()

    assert mapping["github_projects_authoritative"] is False
    assert mapping["publication_performed"] is False
    assert mapping["projectv2_mutation_performed"] is False
    assert mapping["sql_remains_durable_authority"] is True
    assert mapping["scheduler_remains_only_orchestrator"] is True
    assert mapping["qdrant_authoritative"] is False
    assert mapping["copilot_authoritative"] is False
    assert mapping["new_scheduler_created"] is False
    assert mapping["new_global_specialist_registry_created"] is False
    assert mapping["new_http_client_created"] is False


def test_invalid_review_ref_is_rejected() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthProjectsReviewProjectionError,
        match="review_ref",
    ):
        replace(_projection(), review_ref="review-without-prefix")
