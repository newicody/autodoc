"""Full deterministic local proof for phase 0287-r7-r14.

The smoke composes the already-existing GitHub artifact intake, correlated work
package, explicit SourceCandidate operator decision, Scheduler-owned native love
laboratory, two real specialists, SQL authority, OpenVINO/E5-384 + Qdrant recall,
liaison synthesis, final-deliverable publication planning and exact simulated
readback.

Only injected local ports are used.  The function creates no Scheduler, queue,
manager, registry, network client or remote mutation path.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any

from contracts.scheduler import SchedulerContract
from context.context_revision_sql_authority_0287 import (
    SQLiteContextRevisionAuthorityStore,
)
from context.correlated_research_work_package_0287 import (
    CorrelatedResearchWorkPackageCommand,
    build_correlated_research_work_package,
)
from context.github_controlled_advisory_issue_publication_0281 import (
    GitHubIssueCommentSnapshot,
)
from context.github_dual_artifact_run_assembly_0281 import (
    GitHubDualArtifactRunAssemblyCommand,
    GitHubDualArtifactRunMember,
    GitHubDualArtifactRunAssemblyPolicy,
    run_github_dual_artifact_run_assembly,
)
from context.laboratory_framework_contract_0273 import (
    LABORATORY_VISIT_REQUEST_SCHEMA,
    LaboratoryResourceBudget,
    LaboratoryVisitRequest,
)
from context.love_final_deliverable_publication_plan_0287 import (
    FinalDeliverablePublicationReadbackResult,
    LoveFinalDeliverablePublicationCommand,
    LoveFinalDeliverablePublicationPlan,
    ProjectV2FieldSnapshot,
    plan_love_final_deliverable_publication,
    verify_love_final_deliverable_publication_readback,
)
from context.love_memory_evidence_liaison_synthesis_0287 import (
    LOVE_MEMORY_EVIDENCE_SYNTHESIS_COMMAND_SCHEMA,
    LoveAnalysisProjectionPort,
    LoveMemoryEvidenceSynthesisCommand,
    LoveMemoryEvidenceSynthesisResult,
    run_love_memory_evidence_liaison_synthesis,
)
from context.love_async_hybrid_recall_liaison_synthesis_0287 import (
    LoveAsyncHybridRecallLiaisonSynthesisResult,
    run_love_async_hybrid_recall_liaison_synthesis,
)
from context.love_specialist_live_projection_binding_0287 import (
    LoveSpecialistLiveProjectionBindingResult,
    bind_love_specialist_analyses_live,
)
from context.love_study_contracts_0287 import (
    LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
    LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    LOVE_STUDIES_LABORATORY_REF,
    LOVE_STUDY_REQUEST_CONTRACT_REF,
    LOVE_STUDY_REQUEST_SCHEMA,
    LoveStudyRequest,
)
from context.native_love_laboratory_collaboration_scheduler_binding_0287 import (
    NativeLoveCollaborationSchedulerVisitReceipt,
    NativeLoveCollaborationVisitDispatcher,
    register_native_love_collaboration_visit_handler,
    submit_native_love_collaboration_visit,
)
from context.native_love_laboratory_second_specialist_0287 import (
    InMemoryCollaborativeLoveLaboratoryInputResolver,
    NativeLoveCollaborationRecord,
    build_completed_collaboration_record,
    build_native_love_collaborative_provider,
    prepare_second_specialist_collaboration,
)
from context.qdrant_canonical_profile_0287 import QdrantCollectionProfile
from context.source_candidate import (
    SourceCandidate,
    SourceCandidateDecision,
    SourceCandidateOrigin,
    apply_source_candidate_decision,
)
from context.specialist_multitask_model_0287 import (
    SPECIALIST_TASK_REQUEST_SCHEMA,
    SpecialistTaskRequest,
)

LOVE_FULL_DETERMINISTIC_LOCAL_SMOKE_COMMAND_SCHEMA = (
    "missipy.love.full_deterministic_local_smoke_command.v1"
)
LOVE_FULL_DETERMINISTIC_LOCAL_SMOKE_RESULT_SCHEMA = (
    "missipy.love.full_deterministic_local_smoke_result.v1"
)
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_EXPECTED_ARTIFACT_NAMES = frozenset(
    {
        "autodoc-authoritative-request",
        "autodoc-copilot-advisory",
        "autodoc-dual-artifact-manifest",
    }
)
_RETURN_ROUTE_PREFIXES = ("route:", "specialist-path:")
_STUDY_CONTEXT_PREFIXES = (
    "sql:",
    "ctx:",
    "ctx-result:",
    "ctx-fragment:",
    "qdrant:",
    "artifact:",
    "dataset:",
    "research-work-package:",
    "context-revision:",
)


class LoveFullDeterministicLocalSmokeError(RuntimeError):
    """Raised when one local proof stage fails closed."""


@dataclass(frozen=True, slots=True)
class LoveFullDeterministicLocalSmokeCommand:
    """Immutable command for one full local proof with remote boundaries closed."""

    schema: str
    repository: str
    run_id: str
    members: tuple[GitHubDualArtifactRunMember, ...]
    operator_decision: SourceCandidateDecision
    conversation_ref: str
    return_route_ref: str
    context_generation: int
    base_revision_ref: str
    branch_ref: str
    project_ref: str
    security_scope: str
    artifact_storage_ref: str
    created_at: str
    policy_decision_id: str
    project_item_id: str
    project_field_ref: str
    project_field_name: str
    project_status_value: str = "Livrable final prêt"
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    remote_mutation_allowed: bool = False

    def __post_init__(self) -> None:
        if self.schema != LOVE_FULL_DETERMINISTIC_LOCAL_SMOKE_COMMAND_SCHEMA:
            raise LoveFullDeterministicLocalSmokeError(
                "unsupported local smoke command schema"
            )
        if not _REPOSITORY_RE.fullmatch(self.repository):
            raise LoveFullDeterministicLocalSmokeError(
                "repository must use owner/name"
            )
        _require_text("run_id", self.run_id)
        if not isinstance(self.members, tuple):
            object.__setattr__(self, "members", tuple(self.members))
        names = frozenset(member.artifact_name for member in self.members)
        if len(self.members) != 3 or names != _EXPECTED_ARTIFACT_NAMES:
            raise LoveFullDeterministicLocalSmokeError(
                "r14 requires exactly the request, advisory and manifest artifacts"
            )
        if not isinstance(self.operator_decision, SourceCandidateDecision):
            raise TypeError("operator_decision must be SourceCandidateDecision")
        if self.operator_decision.action not in {"promote", "merge"}:
            raise LoveFullDeterministicLocalSmokeError(
                "operator decision must promote or merge the candidate"
            )
        if (
            self.operator_decision.action == "merge"
            and not self.operator_decision.target_context_id
        ):
            raise LoveFullDeterministicLocalSmokeError(
                "merge decision requires target_context_id"
            )
        for name in (
            "conversation_ref",
            "return_route_ref",
            "base_revision_ref",
            "branch_ref",
            "project_ref",
            "security_scope",
            "artifact_storage_ref",
            "created_at",
            "policy_decision_id",
            "project_item_id",
            "project_field_ref",
            "project_field_name",
            "project_status_value",
        ):
            _require_text(name, getattr(self, name))
        if self.context_generation < 0:
            raise LoveFullDeterministicLocalSmokeError(
                "context_generation must be non-negative"
            )
        if not self.return_route_ref.startswith(_RETURN_ROUTE_PREFIXES):
            raise LoveFullDeterministicLocalSmokeError(
                "return_route_ref must start with route: or specialist-path:"
            )
        if not self.base_revision_ref.startswith("context-revision:"):
            raise LoveFullDeterministicLocalSmokeError(
                "base_revision_ref must be typed"
            )
        if not self.artifact_storage_ref.startswith("storage:"):
            raise LoveFullDeterministicLocalSmokeError(
                "artifact_storage_ref must be typed"
            )
        if not self.policy_decision_id.startswith("policy:"):
            raise LoveFullDeterministicLocalSmokeError(
                "policy_decision_id must start with policy:"
            )
        normalized_context_refs = _unique_texts(self.context_refs)
        for context_ref in normalized_context_refs:
            if not context_ref.startswith(_STUDY_CONTEXT_PREFIXES):
                raise LoveFullDeterministicLocalSmokeError(
                    "context_refs must use an existing love-study context prefix"
                )
        object.__setattr__(
            self,
            "context_refs",
            normalized_context_refs,
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _unique_texts(self.evidence_refs),
        )
        if self.remote_mutation_allowed:
            raise LoveFullDeterministicLocalSmokeError(
                "r14 remote mutation must remain disabled"
            )


@dataclass(frozen=True, slots=True)
class LoveFullDeterministicLocalSmokeResult:
    """One correlated proof spanning r7, r11, r12 and r13."""

    schema: str
    proof_ref: str
    proof_digest: str
    run_assembly: Mapping[str, Any]
    work_package: Mapping[str, Any]
    decided_candidate: SourceCandidate
    study: LoveStudyRequest
    first_task: SpecialistTaskRequest
    first_visit: LaboratoryVisitRequest
    first_receipt: NativeLoveCollaborationSchedulerVisitReceipt
    second_receipt: NativeLoveCollaborationSchedulerVisitReceipt
    collaboration: NativeLoveCollaborationRecord
    synthesis_result: LoveMemoryEvidenceSynthesisResult
    publication_plan: LoveFinalDeliverablePublicationPlan
    readback: FinalDeliverablePublicationReadbackResult
    stage_refs: tuple[str, ...]
    live_binding: LoveSpecialistLiveProjectionBindingResult | None = None
    async_continuation: LoveAsyncHybridRecallLiaisonSynthesisResult | None = None
    live_path_used: bool = False
    issue_fixture_exercised: bool = True
    three_artifacts_assembled: bool = True
    explicit_operator_gate_used: bool = True
    same_scheduler_used: bool = True
    simulated_readback_used: bool = True
    remote_mutation_performed: bool = False
    scheduler_created: bool = False
    parallel_orchestrator_created: bool = False

    def __post_init__(self) -> None:
        if self.schema != LOVE_FULL_DETERMINISTIC_LOCAL_SMOKE_RESULT_SCHEMA:
            raise LoveFullDeterministicLocalSmokeError(
                "unsupported local smoke result schema"
            )
        if not self.proof_ref.startswith("love-local-smoke-proof:"):
            raise LoveFullDeterministicLocalSmokeError("proof_ref must be typed")
        if len(self.proof_digest) != 64:
            raise LoveFullDeterministicLocalSmokeError(
                "proof_digest must be SHA-256"
            )
        if not bool(self.run_assembly.get("valid")):
            raise LoveFullDeterministicLocalSmokeError("run assembly is invalid")
        if not bool(self.work_package.get("ready_for_laboratory_route")):
            raise LoveFullDeterministicLocalSmokeError(
                "work package is not ready for laboratory route"
            )
        if self.decided_candidate.status not in {"promoted", "merged"}:
            raise LoveFullDeterministicLocalSmokeError(
                "candidate did not pass the explicit operator gate"
            )
        if self.first_receipt.event_id == self.second_receipt.event_id:
            raise LoveFullDeterministicLocalSmokeError(
                "two distinct Scheduler events are required"
            )
        if self.collaboration.scheduler_receipt_refs != (
            self.first_receipt.receipt_ref,
            self.second_receipt.receipt_ref,
        ):
            raise LoveFullDeterministicLocalSmokeError(
                "collaboration Scheduler receipts mismatch"
            )
        if not self.publication_plan.valid:
            raise LoveFullDeterministicLocalSmokeError(
                "publication preview is not valid"
            )
        if not self.readback.valid or self.readback.action != "confirmed":
            raise LoveFullDeterministicLocalSmokeError(
                "simulated publication readback is not exact"
            )
        if self.live_path_used:
            if not isinstance(
                self.live_binding,
                LoveSpecialistLiveProjectionBindingResult,
            ):
                raise LoveFullDeterministicLocalSmokeError(
                    "live path requires the r12 specialist projection binding"
                )
            if not isinstance(
                self.async_continuation,
                LoveAsyncHybridRecallLiaisonSynthesisResult,
            ):
                raise LoveFullDeterministicLocalSmokeError(
                    "live path requires the r13 async recall continuation"
                )
            if self.async_continuation.binding != self.live_binding:
                raise LoveFullDeterministicLocalSmokeError(
                    "r13 continuation does not preserve the r12 binding"
                )
            if self.async_continuation.synthesis != self.synthesis_result:
                raise LoveFullDeterministicLocalSmokeError(
                    "result synthesis differs from the r13 continuation"
                )
            if self.async_continuation.analysis_reprojected:
                raise LoveFullDeterministicLocalSmokeError(
                    "live local smoke reprojected specialist analyses"
                )
        elif self.live_binding is not None or self.async_continuation is not None:
            raise LoveFullDeterministicLocalSmokeError(
                "deterministic path cannot claim live r12/r13 evidence"
            )
        forbidden = (
            not self.issue_fixture_exercised,
            not self.three_artifacts_assembled,
            not self.explicit_operator_gate_used,
            not self.same_scheduler_used,
            not self.simulated_readback_used,
            self.remote_mutation_performed,
            self.scheduler_created,
            self.parallel_orchestrator_created,
        )
        if any(forbidden):
            raise LoveFullDeterministicLocalSmokeError(
                "r14 authority boundary changed"
            )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "proof_ref": self.proof_ref,
            "proof_digest": self.proof_digest,
            "run_assembly": dict(self.run_assembly),
            "work_package": dict(self.work_package),
            "decided_candidate": self.decided_candidate.to_json_dict(),
            "study": self.study.to_mapping(),
            "first_task": self.first_task.to_mapping(),
            "first_visit": self.first_visit.to_mapping(),
            "first_receipt": self.first_receipt.to_mapping(),
            "second_receipt": self.second_receipt.to_mapping(),
            "collaboration": self.collaboration.to_mapping(),
            "synthesis_result": self.synthesis_result.to_mapping(),
            "publication_plan": self.publication_plan.to_mapping(),
            "readback": self.readback.to_mapping(),
            "stage_refs": list(self.stage_refs),
            "live_binding": (
                self.live_binding.to_mapping()
                if self.live_binding is not None
                else None
            ),
            "async_continuation": (
                self.async_continuation.to_mapping()
                if self.async_continuation is not None
                else None
            ),
            "boundaries": {
                "live_path_used": self.live_path_used,
                "r12_live_binding_used": self.live_path_used,
                "r13_async_recall_used": self.live_path_used,
                "analyses_reprojected": False,
                "issue_fixture_exercised": True,
                "three_artifacts_assembled": True,
                "request_authoritative": True,
                "advisory_used_as_hint_only": True,
                "explicit_operator_gate_used": True,
                "same_scheduler_used": True,
                "scheduler_created": False,
                "parallel_orchestrator_created": False,
                "sql_is_authority": True,
                "qdrant_is_projection_only": True,
                "openvino_e5_384_reused": True,
                "publication_preview_only": True,
                "simulated_readback_used": True,
                "remote_mutation_performed": False,
            },
        }


async def run_love_full_deterministic_local_smoke(
    command: LoveFullDeterministicLocalSmokeCommand,
    *,
    scheduler: SchedulerContract,
    dispatcher: NativeLoveCollaborationVisitDispatcher,
    authority_store: SQLiteContextRevisionAuthorityStore,
    projection_port: LoveAnalysisProjectionPort,
    collection: QdrantCollectionProfile,
    embedder: Any,
    executor: Any,
    live_async: bool = False,
) -> LoveFullDeterministicLocalSmokeResult:
    """Execute the complete r14 proof through existing local boundaries."""

    if not isinstance(scheduler, SchedulerContract):
        raise TypeError("scheduler must implement SchedulerContract")

    assembly = run_github_dual_artifact_run_assembly(
        GitHubDualArtifactRunAssemblyCommand(
            repository=command.repository,
            run_id=command.run_id,
            members=command.members,
        ),
        GitHubDualArtifactRunAssemblyPolicy(allow_missing_advisory=False),
    )
    if not assembly.valid:
        raise LoveFullDeterministicLocalSmokeError(
            "artifact assembly failed: " + "; ".join(assembly.issues)
        )

    package_build = build_correlated_research_work_package(
        CorrelatedResearchWorkPackageCommand(
            run_assembly=assembly.to_mapping(),
            conversation_ref=command.conversation_ref,
            return_route_ref=command.return_route_ref,
            context_generation=command.context_generation,
            context_refs=_unique_texts(
                (command.base_revision_ref, *command.context_refs)
            ),
            evidence_refs=command.evidence_refs,
            require_advisory=True,
        )
    )
    if not package_build.valid:
        raise LoveFullDeterministicLocalSmokeError(
            "work package failed: " + "; ".join(package_build.issues)
        )
    package = dict(package_build.work_package)

    candidate = _candidate_from_mapping(
        assembly.intake.get("source_candidate", {})
    )
    decided_candidate = apply_source_candidate_decision(
        candidate,
        command.operator_decision,
    )
    if decided_candidate.status not in {"promoted", "merged"}:
        raise LoveFullDeterministicLocalSmokeError(
            "operator gate did not authorize the laboratory route"
        )

    study, first_task, first_visit, second_task_ref, second_visit_ref = (
        _build_first_visit_surface(command, package, decided_candidate)
    )
    resolver = InMemoryCollaborativeLoveLaboratoryInputResolver(
        studies={study.study_ref: study},
        tasks={first_task.task_ref: first_task},
    )
    provider = build_native_love_collaborative_provider(resolver)
    register_native_love_collaboration_visit_handler(
        dispatcher,
        provider=provider,
    )

    first_receipt = await submit_native_love_collaboration_visit(
        scheduler,
        first_visit,
    )
    preparation = prepare_second_specialist_collaboration(
        first_visit=first_visit,
        first_result=first_receipt.execution.result,
        second_task_ref=second_task_ref,
        second_visit_ref=second_visit_ref,
    )
    resolver.register_concept_analysis(
        preparation.first_analysis,
        preparation.first_artifact,
    )
    resolver.register_task(preparation.second_task)
    second_receipt = await submit_native_love_collaboration_visit(
        scheduler,
        preparation.second_visit,
    )
    collaboration = build_completed_collaboration_record(
        preparation=preparation,
        first_execution=first_receipt.execution,
        second_execution=second_receipt.execution,
        first_scheduler_receipt_ref=first_receipt.receipt_ref,
        second_scheduler_receipt_ref=second_receipt.receipt_ref,
    )

    issue_number = int(package["source_issue"]["number"])
    target_ref = f"github:issue:{command.repository}#{issue_number}"
    synthesis_command = LoveMemoryEvidenceSynthesisCommand(
        schema=LOVE_MEMORY_EVIDENCE_SYNTHESIS_COMMAND_SCHEMA,
        command_ref=_digest_ref(
            "love-synthesis-command:",
            package["work_package_ref"],
            collaboration.second_analysis.analysis_ref,
        ),
        study=study,
        collaboration=collaboration,
        base_revision_ref=command.base_revision_ref,
        branch_ref=command.branch_ref,
        project_ref=command.project_ref,
        security_scope=command.security_scope,
        target_ref=target_ref,
        artifact_storage_ref=command.artifact_storage_ref,
        created_at=command.created_at,
    )
    live_binding: LoveSpecialistLiveProjectionBindingResult | None = None
    async_continuation: LoveAsyncHybridRecallLiaisonSynthesisResult | None = None
    if live_async:
        live_binding, async_continuation = await _run_live_synthesis_path(
            synthesis_command,
            authority_store=authority_store,
            projection_port=projection_port,
            collection=collection,
            embedder=embedder,
            executor=executor,
        )
        synthesis_result = async_continuation.synthesis
    else:
        synthesis_result = run_love_memory_evidence_liaison_synthesis(
            synthesis_command,
            authority_store=authority_store,
            projection_port=projection_port,
            collection=collection,
            embedder=embedder,
            executor=executor,
        )

    source_issue_ref = (
        f"github-frame:{command.repository}/issues/{issue_number}"
    )
    publication_plan = plan_love_final_deliverable_publication(
        LoveFinalDeliverablePublicationCommand(
            repository=command.repository,
            issue_number=issue_number,
            source_issue_ref=source_issue_ref,
            policy_decision_id=command.policy_decision_id,
            operator_decision="approve",
            synthesis_result=synthesis_result,
            project_item_id=command.project_item_id,
            project_field_ref=command.project_field_ref,
            project_field_name=command.project_field_name,
            project_status_value=command.project_status_value,
        )
    )
    if not publication_plan.valid or publication_plan.project_projection is None:
        raise LoveFullDeterministicLocalSmokeError(
            "final deliverable publication preview failed: "
            + "; ".join(publication_plan.issues)
        )

    simulated_comment = GitHubIssueCommentSnapshot(
        comment_id=issue_number * 1000 + 14,
        body=publication_plan.body,
        html_url=(
            f"local-readback://{command.repository}/issues/{issue_number}/"
            "comments/final-deliverable"
        ),
    )
    projection = publication_plan.project_projection
    simulated_project = ProjectV2FieldSnapshot(
        project_item_id=projection.project_item_id,
        field_ref=projection.field_ref,
        field_name=projection.field_name,
        value=projection.value,
    )
    readback = verify_love_final_deliverable_publication_readback(
        publication_plan,
        issue_comments=(simulated_comment,),
        project_snapshot=simulated_project,
    )
    if not readback.valid:
        raise LoveFullDeterministicLocalSmokeError(
            "simulated exact readback failed: " + "; ".join(readback.issues)
        )

    stage_refs = (
        str(package["work_package_ref"]),
        decided_candidate.candidate_id,
        study.study_ref,
        first_visit.visit_ref,
        preparation.second_visit.visit_ref,
        synthesis_result.analysis_revision.revision_ref,
        synthesis_result.synthesis_revision.revision_ref,
        publication_plan.plan_ref,
        f"readback:{publication_plan.plan_digest[:24]}",
    )
    proof_payload = {
        "schema": LOVE_FULL_DETERMINISTIC_LOCAL_SMOKE_RESULT_SCHEMA,
        "repository": command.repository,
        "run_id": command.run_id,
        "stage_refs": list(stage_refs),
        "candidate_status": decided_candidate.status,
        "publication_plan_digest": publication_plan.plan_digest,
        "readback_action": readback.action,
        "live_path_used": live_async,
    }
    proof_digest = hashlib.sha256(
        _canonical_json(proof_payload).encode("utf-8")
    ).hexdigest()
    return LoveFullDeterministicLocalSmokeResult(
        schema=LOVE_FULL_DETERMINISTIC_LOCAL_SMOKE_RESULT_SCHEMA,
        proof_ref=f"love-local-smoke-proof:{proof_digest[:24]}",
        proof_digest=proof_digest,
        run_assembly=assembly.to_mapping(),
        work_package=package,
        decided_candidate=decided_candidate,
        study=study,
        first_task=first_task,
        first_visit=first_visit,
        first_receipt=first_receipt,
        second_receipt=second_receipt,
        collaboration=collaboration,
        synthesis_result=synthesis_result,
        publication_plan=publication_plan,
        readback=readback,
        stage_refs=stage_refs,
        live_binding=live_binding,
        async_continuation=async_continuation,
        live_path_used=live_async,
    )


async def _run_live_synthesis_path(
    command: LoveMemoryEvidenceSynthesisCommand,
    *,
    authority_store: Any,
    projection_port: Any,
    collection: QdrantCollectionProfile,
    embedder: Any,
    executor: Any,
) -> tuple[
    LoveSpecialistLiveProjectionBindingResult,
    LoveAsyncHybridRecallLiaisonSynthesisResult,
]:
    """Run r12 then r13 without reprojecting either specialist analysis."""

    binding = await bind_love_specialist_analyses_live(
        command,
        authority_store=authority_store,
        projection_port=projection_port,
    )
    continuation = await run_love_async_hybrid_recall_liaison_synthesis(
        command,
        binding=binding,
        collection=collection,
        embedder=embedder,
        executor=executor,
        authority_store=authority_store,
    )
    if continuation.binding != binding:
        raise LoveFullDeterministicLocalSmokeError(
            "r13 continuation did not preserve the r12 binding"
        )
    if continuation.analysis_reprojected:
        raise LoveFullDeterministicLocalSmokeError(
            "r13 continuation reprojected specialist analyses"
        )
    return binding, continuation


async def run_love_full_live_local_smoke(
    command: LoveFullDeterministicLocalSmokeCommand,
    *,
    scheduler: SchedulerContract,
    dispatcher: NativeLoveCollaborationVisitDispatcher,
    authority_store: Any,
    projection_port: Any,
    collection: QdrantCollectionProfile,
    embedder: Any,
    executor: Any,
) -> LoveFullDeterministicLocalSmokeResult:
    """Execute the full local chain through the real async r12/r13 path."""

    return await run_love_full_deterministic_local_smoke(
        command,
        scheduler=scheduler,
        dispatcher=dispatcher,
        authority_store=authority_store,
        projection_port=projection_port,
        collection=collection,
        embedder=embedder,
        executor=executor,
        live_async=True,
    )


def _build_first_visit_surface(
    command: LoveFullDeterministicLocalSmokeCommand,
    package: Mapping[str, Any],
    candidate: SourceCandidate,
) -> tuple[
    LoveStudyRequest,
    SpecialistTaskRequest,
    LaboratoryVisitRequest,
    str,
    str,
]:
    request = _mapping(package.get("authoritative_request"))
    advisory = _mapping(package.get("copilot_advisory"))
    issue_number = int(_mapping(package.get("source_issue"))["number"])
    stable_ref = str(package["work_package_ref"])
    suffix = hashlib.sha256(stable_ref.encode("utf-8")).hexdigest()[:16]
    study_ref = f"love-study:github-{issue_number}-{suffix}"
    task_ref = f"specialist-task:love-first-{suffix}"
    visit_ref = f"laboratory-visit:love-first-{suffix}"
    second_task_ref = f"specialist-task:love-second-{suffix}"
    second_visit_ref = f"laboratory-visit:love-second-{suffix}"

    request_title = _require_text("request title", request.get("title"))
    request_body = _require_text("request body", request.get("body"))
    source_issue_ref = f"github-issue:{command.repository}#{issue_number}"
    study_context_refs = _unique_texts(
        (
            command.base_revision_ref,
            stable_ref,
            *command.context_refs,
        )
    )
    visit_context_refs = (f"ctx:love-study-{suffix}",)
    advisory_ref = str(advisory.get("artifact_ref", "")).strip()
    evidence_refs = _unique_texts(
        (
            str(request.get("artifact_ref", "")),
            *(command.evidence_refs),
            *((advisory_ref,) if advisory_ref else ()),
        )
    )
    study = LoveStudyRequest(
        schema=LOVE_STUDY_REQUEST_SCHEMA,
        study_ref=study_ref,
        source_issue_ref=source_issue_ref,
        objective=request_title,
        subject_text=request_body,
        constraints=(
            "Ne pas produire de diagnostic psychologique.",
            "Conserver les contradictions et incertitudes.",
        ),
        success_criteria=(
            "Produire deux analyses spécialisées attribuées.",
            "Fonder chaque constat sur des éléments observables du texte source.",
        ),
        context_refs=study_context_refs,
    )
    first_task = SpecialistTaskRequest(
        schema=SPECIALIST_TASK_REQUEST_SCHEMA,
        task_ref=task_ref,
        plan_ref=f"specialist-task-plan:love-{suffix}",
        mission_ref=f"mission:love-study-{issue_number}-{suffix}",
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        task_type_ref="task-type:love.concept_analysis",
        capability="love.concept_analysis",
        objective="Analyser profondément les concepts et affects présents.",
        input_contract_ref=LOVE_STUDY_REQUEST_CONTRACT_REF,
        expected_output_contract_ref=LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
        conversation_ref=command.conversation_ref,
        return_route_ref=command.return_route_ref,
        constraints=study.constraints,
        success_criteria=("Fournir des constats attribués et leurs preuves.",),
        context_refs=visit_context_refs,
        idempotency_key=f"idempotency:love-first-{suffix}",
        metadata={
            "context_revision_ref": command.base_revision_ref,
            "work_package_ref": stable_ref,
            "source_candidate_ref": candidate.candidate_id,
            "request_authoritative": True,
            "advisory_used_as_hint_only": True,
            "advisory_ref": advisory_ref,
            "evidence_refs": list(evidence_refs),
        },
    )
    first_visit = LaboratoryVisitRequest(
        schema=LABORATORY_VISIT_REQUEST_SCHEMA,
        visit_ref=visit_ref,
        laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        objective_ref=first_task.task_ref,
        source_candidate_ref=study.study_ref,
        context_generation=command.context_generation,
        input_contract_ref=first_task.input_contract_ref,
        expected_output_contract_ref=first_task.expected_output_contract_ref,
        resource_budget=LaboratoryResourceBudget(),
        return_route_ref=first_task.return_route_ref,
        context_refs=first_task.context_refs,
        origin_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        target_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        conversation_ref=first_task.conversation_ref,
    )
    return study, first_task, first_visit, second_task_ref, second_visit_ref


def _candidate_from_mapping(value: object) -> SourceCandidate:
    mapping = _mapping(value)
    origin_mapping = _mapping(mapping.get("origin"))
    status = str(mapping.get("status", "new"))
    if status != "new":
        raise LoveFullDeterministicLocalSmokeError(
            "source candidate must reach r14 before an operator decision"
        )
    return SourceCandidate(
        candidate_id=_require_text("candidate_id", mapping.get("candidate_id")),
        title=_require_text("candidate title", mapping.get("title")),
        body=str(mapping.get("body", "")),
        origin=SourceCandidateOrigin(
            kind=_require_text("origin kind", origin_mapping.get("kind")),
            reference=str(origin_mapping.get("reference", "")),
            repository=(
                None
                if origin_mapping.get("repository") is None
                else str(origin_mapping.get("repository"))
            ),
        ),
        status=status,
        labels=tuple(str(item) for item in mapping.get("labels", ())),
        metadata=_mapping(mapping.get("metadata")),
    )


def _digest_ref(prefix: str, *parts: object) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(str(part).encode("utf-8"))
        digest.update(b"\0")
    return prefix + digest.hexdigest()[:24]


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        dict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _require_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LoveFullDeterministicLocalSmokeError(
            f"{name} must be a non-empty string"
        )
    return value.strip()


def _unique_texts(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    normalized = tuple(str(value).strip() for value in values if str(value).strip())
    return tuple(dict.fromkeys(normalized))


__all__ = (
    "LOVE_FULL_DETERMINISTIC_LOCAL_SMOKE_COMMAND_SCHEMA",
    "LOVE_FULL_DETERMINISTIC_LOCAL_SMOKE_RESULT_SCHEMA",
    "LoveFullDeterministicLocalSmokeCommand",
    "LoveFullDeterministicLocalSmokeError",
    "LoveFullDeterministicLocalSmokeResult",
    "run_love_full_deterministic_local_smoke",
    "run_love_full_live_local_smoke",
)
