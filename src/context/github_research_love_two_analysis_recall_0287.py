"""Recall and SQL-rehydrate exactly two GitHub research analyses.

r16-r12 persists two distinct specialist analyses in SQL authority. r16-r13
projects those two objects separately into Qdrant. This unit reuses the existing
asynchronous hybrid retrieval composition to:

- await one OpenVINO/E5 ``query:`` embedding;
- run bounded dense and sparse Qdrant searches;
- fuse reference-only candidates;
- rehydrate authoritative objects from SQL;
- prove that the recalled set is exactly the persisted pair.

No projection, synthesis, Scheduler, laboratory or GitHub mutation occurs here.
The in-memory result retains the two rehydrated objects for the next synthesis
unit, while ``to_mapping()`` exposes only references, digests and scores.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import json
from types import MappingProxyType
from typing import Any

from context.github_research_love_sql_persistence_0287 import (
    RECEIPT_SCHEMA as SQL_PERSISTENCE_RECEIPT_SCHEMA,
    RESULT_SCHEMA as SQL_PERSISTENCE_RESULT_SCHEMA,
)
from context.github_research_love_two_qdrant_projections_0287 import (
    PLAN_SCHEMA as TWO_PROJECTION_PLAN_SCHEMA,
    RECEIPT_SCHEMA as TWO_PROJECTION_RECEIPT_SCHEMA,
    RESULT_SCHEMA as TWO_PROJECTION_RESULT_SCHEMA,
)
from context.hybrid_retrieval_sql_rehydration_0287 import (
    HYBRID_FILTER_SCHEMA,
    HYBRID_QUERY_SCHEMA,
    HybridRetrievalFilter,
    HybridRetrievalQuery,
    RehydratedAuthorityItem,
)
from context.love_async_hybrid_retrieval_execution_0287 import (
    LoveAsyncHybridRetrievalExecutionResult,
    execute_love_async_hybrid_retrieval,
)
from context.love_imported_actions_runtime_contract_0287 import (
    ImportedActionsRuntimePorts,
    validate_imported_actions_runtime_ports,
)

PLAN_SCHEMA = "missipy.github.research_love_two_analysis_recall_plan.v1"
RESULT_SCHEMA = "missipy.github.research_love_two_analysis_recall_result.v1"


class GitHubResearchLoveTwoAnalysisRecallError(RuntimeError):
    """Raised when recall diverges from the exact persisted/projected pair."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveTwoAnalysisRecallCommand:
    """Bounded read-side request using already injected runtime ports."""

    runtime_ports: ImportedActionsRuntimePorts
    sql_persistence: Mapping[str, Any]
    two_projections: Mapping[str, Any]
    query_text: str
    dense_candidate_limit: int = 8
    sparse_candidate_limit: int = 8
    final_limit: int = 2
    reciprocal_rank_k: int = 60

    def __post_init__(self) -> None:
        if not isinstance(self.sql_persistence, Mapping):
            raise TypeError("sql_persistence must be a mapping")
        if not isinstance(self.two_projections, Mapping):
            raise TypeError("two_projections must be a mapping")
        text = self.query_text.strip()
        if not text:
            raise GitHubResearchLoveTwoAnalysisRecallError(
                "query_text must not be empty"
            )
        object.__setattr__(self, "query_text", text)
        for name in (
            "dense_candidate_limit",
            "sparse_candidate_limit",
            "final_limit",
            "reciprocal_rank_k",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise GitHubResearchLoveTwoAnalysisRecallError(
                    f"{name} must be a positive integer"
                )
        if self.final_limit != 2:
            raise GitHubResearchLoveTwoAnalysisRecallError(
                "this bounded recall must select exactly two analyses"
            )
        if self.final_limit > (
            self.dense_candidate_limit + self.sparse_candidate_limit
        ):
            raise GitHubResearchLoveTwoAnalysisRecallError(
                "final_limit exceeds the candidate budget"
            )


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveTwoAnalysisRecallPlan:
    """Exact pair, scope and existing hybrid query to execute."""

    schema: str
    work_package_ref: str
    sql_persistence_plan_digest: str
    projection_pair_plan_digest: str
    expected_sql_refs: tuple[str, str]
    query: HybridRetrievalQuery
    plan_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema != PLAN_SCHEMA:
            raise GitHubResearchLoveTwoAnalysisRecallError(
                "unsupported two-analysis recall plan schema"
            )
        if not self.work_package_ref.startswith("research-work-package:"):
            raise GitHubResearchLoveTwoAnalysisRecallError(
                "work_package_ref must start with research-work-package:"
            )
        for name, value in (
            ("sql_persistence_plan_digest", self.sql_persistence_plan_digest),
            ("projection_pair_plan_digest", self.projection_pair_plan_digest),
        ):
            if not value.startswith("sha256:") or len(value) != 71:
                raise GitHubResearchLoveTwoAnalysisRecallError(
                    f"{name} must be sha256:*"
                )
        refs = tuple(self.expected_sql_refs)
        if len(refs) != 2 or len(set(refs)) != 2:
            raise GitHubResearchLoveTwoAnalysisRecallError(
                "exactly two distinct SQL object references are required"
            )
        if any(not ref.startswith("context-object:") for ref in refs):
            raise GitHubResearchLoveTwoAnalysisRecallError(
                "expected SQL refs must be context-object:*"
            )
        object.__setattr__(self, "expected_sql_refs", refs)
        if self.query.final_limit != 2 or self.query.group_by != "source_ref":
            raise GitHubResearchLoveTwoAnalysisRecallError(
                "recall query must select two source-grouped results"
            )
        object.__setattr__(self, "plan_digest", _plan_digest(self))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "plan_digest": self.plan_digest,
            "work_package_ref": self.work_package_ref,
            "sql_persistence_plan_digest": self.sql_persistence_plan_digest,
            "projection_pair_plan_digest": self.projection_pair_plan_digest,
            "expected_sql_refs": list(self.expected_sql_refs),
            "query": self.query.to_mapping(),
            "boundaries": {
                "existing_async_hybrid_retrieval_reused": True,
                "expected_result_count": 2,
                "dense_sparse_recall": True,
                "sql_rehydration_required": True,
                "query_text_serialized": False,
                "qdrant_write_performed": False,
                "global_synthesis_created": False,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveTwoAnalysisRecallResult:
    """In-memory retrieval plus a body-free serializable readback."""

    schema: str
    valid: bool
    status: str
    issues: tuple[str, ...]
    plan: GitHubResearchLoveTwoAnalysisRecallPlan
    retrieval_execution: LoveAsyncHybridRetrievalExecutionResult | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    items_by_sql_ref: Mapping[str, RehydratedAuthorityItem] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if self.schema != RESULT_SCHEMA:
            raise GitHubResearchLoveTwoAnalysisRecallError(
                "unsupported two-analysis recall result schema"
            )
        normalized = dict(self.items_by_sql_ref)
        if self.valid:
            if self.status != "recalled":
                raise GitHubResearchLoveTwoAnalysisRecallError(
                    "valid recall result status must be recalled"
                )
            if self.retrieval_execution is None:
                raise GitHubResearchLoveTwoAnalysisRecallError(
                    "valid recall requires retrieval execution"
                )
            if set(normalized) != set(self.plan.expected_sql_refs):
                raise GitHubResearchLoveTwoAnalysisRecallError(
                    "valid recall must retain exactly both expected SQL objects"
                )
        object.__setattr__(
            self,
            "items_by_sql_ref",
            MappingProxyType(normalized),
        )

    @property
    def first_item(self) -> RehydratedAuthorityItem:
        return self._item(self.plan.expected_sql_refs[0])

    @property
    def second_item(self) -> RehydratedAuthorityItem:
        return self._item(self.plan.expected_sql_refs[1])

    def _item(self, sql_ref: str) -> RehydratedAuthorityItem:
        item = self.items_by_sql_ref.get(sql_ref)
        if item is None:
            raise GitHubResearchLoveTwoAnalysisRecallError(
                f"rehydrated item is unavailable: {sql_ref}"
            )
        return item

    def to_mapping(self) -> dict[str, object]:
        retrieval = (
            self.retrieval_execution.retrieval
            if self.retrieval_execution is not None
            else None
        )
        hit_by_ref = (
            {hit.sql_ref: hit for hit in retrieval.hits}
            if retrieval is not None
            else {}
        )
        summaries: list[dict[str, object]] = []
        for sql_ref in self.plan.expected_sql_refs:
            item = self.items_by_sql_ref.get(sql_ref)
            hit = hit_by_ref.get(sql_ref)
            if item is None:
                continue
            summaries.append(
                {
                    "sql_ref": item.sql_ref,
                    "authority_kind": item.authority_kind,
                    "content_digest": item.content_digest,
                    "title": item.title,
                    "media_type": item.media_type,
                    "fused_score": (
                        hit.fused_score if hit is not None else None
                    ),
                    "dense_rank": (
                        hit.dense_rank if hit is not None else None
                    ),
                    "sparse_rank": (
                        hit.sparse_rank if hit is not None else None
                    ),
                    "rehydrated_from_sql": True,
                    "authoritative_body_serialized": False,
                }
            )
        execution_receipt = (
            self.retrieval_execution.receipt.to_mapping()
            if self.retrieval_execution is not None
            else None
        )
        return {
            "schema": self.schema,
            "valid": self.valid,
            "status": self.status,
            "issues": list(self.issues),
            "plan": self.plan.to_mapping(),
            "recalled_sql_refs": [
                item["sql_ref"] for item in summaries
            ],
            "recalled_items": summaries,
            "retrieval_execution_receipt": execution_receipt,
            "boundaries": {
                "two_expected_analyses_recalled": self.valid,
                "sql_rehydration_completed": self.valid,
                "rehydrated_bodies_available_in_memory": self.valid,
                "rehydrated_bodies_serialized": False,
                "raw_vectors_serialized": False,
                "query_text_serialized": False,
                "qdrant_write_performed": False,
                "sql_write_performed": False,
                "global_synthesis_created": False,
                "github_mutation_performed": False,
                "scheduler_created": False,
            },
        }


def build_github_research_love_two_analysis_recall_plan(
    command: GitHubResearchLoveTwoAnalysisRecallCommand,
) -> GitHubResearchLoveTwoAnalysisRecallPlan:
    """Validate r16-r12/r16-r13 lineage and build one existing hybrid query."""

    ports = validate_imported_actions_runtime_ports(command.runtime_ports)
    sql_result = command.sql_persistence
    projection_result = command.two_projections

    if sql_result.get("schema") != SQL_PERSISTENCE_RESULT_SCHEMA:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "unsupported SQL persistence result schema"
        )
    if sql_result.get("valid") is not True or sql_result.get("status") != "persisted":
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "SQL persistence result must be valid and persisted"
        )
    sql_plan = _required_mapping(sql_result, "plan")
    sql_receipt = _required_mapping(sql_result, "receipt")
    if sql_receipt.get("schema") != SQL_PERSISTENCE_RECEIPT_SCHEMA:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "unsupported SQL persistence receipt schema"
        )
    if sql_receipt.get("readback_verified") is not True:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "SQL analysis readback must be verified"
        )

    if projection_result.get("schema") != TWO_PROJECTION_RESULT_SCHEMA:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "unsupported two-projection result schema"
        )
    if (
        projection_result.get("valid") is not True
        or projection_result.get("status") != "projected"
    ):
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "both Qdrant projections must be valid and projected"
        )
    projection_plan = _required_mapping(projection_result, "plan")
    projection_receipt = _required_mapping(projection_result, "receipt")
    if projection_plan.get("schema") != TWO_PROJECTION_PLAN_SCHEMA:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "unsupported two-projection plan schema"
        )
    if projection_receipt.get("schema") != TWO_PROJECTION_RECEIPT_SCHEMA:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "unsupported two-projection receipt schema"
        )

    first_ref = _required_text(sql_receipt, "first_object_ref")
    second_ref = _required_text(sql_receipt, "second_object_ref")
    revision_ref = _required_text(sql_receipt, "revision_ref")
    work_package_ref = _required_text(sql_receipt, "work_package_ref")
    sql_plan_digest = _required_text(sql_plan, "plan_digest")
    pair_plan_digest = _required_text(
        projection_receipt,
        "pair_plan_digest",
    )

    first_projection_plan = _required_mapping(projection_plan, "first")
    second_projection_plan = _required_mapping(projection_plan, "second")
    first_request = _required_mapping(first_projection_plan, "request")
    second_request = _required_mapping(second_projection_plan, "request")
    first_projection_receipt = _required_mapping(
        projection_receipt,
        "first",
    )
    second_projection_receipt = _required_mapping(
        projection_receipt,
        "second",
    )

    _validate_projection_member(
        object_ref=first_ref,
        revision_ref=revision_ref,
        plan=first_projection_plan,
        request=first_request,
        receipt=first_projection_receipt,
    )
    _validate_projection_member(
        object_ref=second_ref,
        revision_ref=revision_ref,
        plan=second_projection_plan,
        request=second_request,
        receipt=second_projection_receipt,
    )
    for name in (
        "branch_ref",
        "project_ref",
        "conversation_ref",
        "laboratory_ref",
        "security_scope",
    ):
        if first_request.get(name) != second_request.get(name):
            raise GitHubResearchLoveTwoAnalysisRecallError(
                f"projection scope mismatch for {name}"
            )

    dense_vector_name = _required_text(
        first_projection_plan,
        "dense_vector_name",
    )
    sparse_vector_name = _required_text(
        first_projection_plan,
        "sparse_vector_name",
    )
    if dense_vector_name != second_projection_plan.get("dense_vector_name"):
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "dense vector names differ between analysis projections"
        )
    if sparse_vector_name != second_projection_plan.get("sparse_vector_name"):
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "sparse vector names differ between analysis projections"
        )
    collection_name = _required_text(
        first_projection_plan,
        "collection_name",
    )
    if collection_name != second_projection_plan.get("collection_name"):
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "projection collection names differ"
        )
    if collection_name != str(ports.collection.collection_name).strip():
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "projection collection differs from injected runtime"
        )
    if first_projection_plan.get("dimension") != 384:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "first projection dimension must be 384"
        )
    if second_projection_plan.get("dimension") != 384:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "second projection dimension must be 384"
        )

    digest = hashlib.sha256(
        (
            work_package_ref
            + "|"
            + first_ref
            + "|"
            + second_ref
            + "|"
            + command.query_text
        ).encode("utf-8")
    ).hexdigest()
    retrieval_filter = HybridRetrievalFilter(
        schema=HYBRID_FILTER_SCHEMA,
        context_revision_ref=revision_ref,
        branch_ref=_required_text(first_request, "branch_ref"),
        project_ref=_required_text(first_request, "project_ref"),
        security_scope=_required_text(first_request, "security_scope"),
        conversation_ref=_required_text(first_request, "conversation_ref"),
        laboratory_ref=_required_text(first_request, "laboratory_ref"),
        require_valid=True,
        include_superseded=False,
    )
    query = HybridRetrievalQuery(
        schema=HYBRID_QUERY_SCHEMA,
        query_ref=f"retrieval-query:github-love-pair-{digest[:24]}",
        task_ref=f"task:github-love-recall-{digest[:24]}",
        query_text=command.query_text,
        filter=retrieval_filter,
        dense_vector_name=dense_vector_name,
        sparse_vector_name=sparse_vector_name,
        dense_candidate_limit=command.dense_candidate_limit,
        sparse_candidate_limit=command.sparse_candidate_limit,
        final_limit=2,
        group_by="source_ref",
        reciprocal_rank_k=command.reciprocal_rank_k,
    )
    return GitHubResearchLoveTwoAnalysisRecallPlan(
        schema=PLAN_SCHEMA,
        work_package_ref=work_package_ref,
        sql_persistence_plan_digest=sql_plan_digest,
        projection_pair_plan_digest=pair_plan_digest,
        expected_sql_refs=(first_ref, second_ref),
        query=query,
    )


async def recall_github_research_love_analyses(
    command: GitHubResearchLoveTwoAnalysisRecallCommand,
) -> GitHubResearchLoveTwoAnalysisRecallResult:
    """Execute existing async hybrid retrieval and require the exact SQL pair."""

    try:
        ports = validate_imported_actions_runtime_ports(command.runtime_ports)
        plan = build_github_research_love_two_analysis_recall_plan(command)
        execution = await execute_love_async_hybrid_retrieval(
            plan.query,
            collection=ports.collection,
            embedder=ports.embedder,
            executor=ports.executor,
            authority_store=ports.authority_store,
        )
        retrieval = execution.retrieval
        recalled_refs = tuple(item.sql_ref for item in retrieval.items)
        if len(recalled_refs) != 2 or set(recalled_refs) != set(
            plan.expected_sql_refs
        ):
            raise GitHubResearchLoveTwoAnalysisRecallError(
                "hybrid recall did not rehydrate exactly both specialist analyses"
            )
        items_by_ref: dict[str, RehydratedAuthorityItem] = {}
        for item in retrieval.items:
            if item.authority_kind != "context_object":
                raise GitHubResearchLoveTwoAnalysisRecallError(
                    "recalled specialist analysis is not a context object"
                )
            if not item.body:
                raise GitHubResearchLoveTwoAnalysisRecallError(
                    "rehydrated specialist analysis body is empty"
                )
            if item.sql_ref in items_by_ref:
                raise GitHubResearchLoveTwoAnalysisRecallError(
                    "hybrid recall returned a duplicate SQL object"
                )
            items_by_ref[item.sql_ref] = item
        return GitHubResearchLoveTwoAnalysisRecallResult(
            schema=RESULT_SCHEMA,
            valid=True,
            status="recalled",
            issues=(),
            plan=plan,
            retrieval_execution=execution,
            items_by_sql_ref=items_by_ref,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        try:
            plan = build_github_research_love_two_analysis_recall_plan(command)
        except (TypeError, ValueError, RuntimeError):
            plan = _invalid_plan(command)
        return GitHubResearchLoveTwoAnalysisRecallResult(
            schema=RESULT_SCHEMA,
            valid=False,
            status="failed",
            issues=(f"{type(exc).__name__}: {exc}",),
            plan=plan,
        )


def _validate_projection_member(
    *,
    object_ref: str,
    revision_ref: str,
    plan: Mapping[str, Any],
    request: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> None:
    if request.get("object_ref") != object_ref:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "projection plan object_ref differs from SQL persistence"
        )
    if request.get("revision_ref") != revision_ref:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "projection plan revision_ref differs from SQL persistence"
        )
    if receipt.get("object_ref") != object_ref:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "projection receipt object_ref differs from SQL persistence"
        )
    if receipt.get("revision_ref") != revision_ref:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "projection receipt revision_ref differs from SQL persistence"
        )
    if receipt.get("plan_digest") != plan.get("plan_digest"):
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "projection receipt plan digest mismatch"
        )
    payload = _required_mapping(receipt, "qdrant_payload")
    if payload.get("sql_ref") != object_ref:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "Qdrant payload sql_ref differs from SQL persistence"
        )
    if payload.get("source_ref") != object_ref:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "Qdrant payload source_ref differs from SQL persistence"
        )
    forbidden = {
        "body",
        "content",
        "vector",
        "vectors",
        "values",
        "embedding",
        "local_path",
    }.intersection(payload)
    if forbidden:
        raise GitHubResearchLoveTwoAnalysisRecallError(
            "Qdrant payload contains forbidden authoritative/vector fields"
        )


def _invalid_plan(
    command: GitHubResearchLoveTwoAnalysisRecallCommand,
) -> GitHubResearchLoveTwoAnalysisRecallPlan:
    """Stable placeholder used only when lineage validation failed early."""

    digest = hashlib.sha256(command.query_text.encode("utf-8")).hexdigest()
    filter_ = HybridRetrievalFilter(
        schema=HYBRID_FILTER_SCHEMA,
        context_revision_ref="context-revision:invalid",
        branch_ref="branch:invalid",
        project_ref="project:invalid",
        security_scope="security:invalid",
    )
    query = HybridRetrievalQuery(
        schema=HYBRID_QUERY_SCHEMA,
        query_ref=f"retrieval-query:invalid-{digest[:24]}",
        task_ref=f"task:invalid-{digest[:24]}",
        query_text=command.query_text,
        filter=filter_,
        dense_candidate_limit=command.dense_candidate_limit,
        sparse_candidate_limit=command.sparse_candidate_limit,
        final_limit=2,
        group_by="source_ref",
        reciprocal_rank_k=command.reciprocal_rank_k,
    )
    return GitHubResearchLoveTwoAnalysisRecallPlan(
        schema=PLAN_SCHEMA,
        work_package_ref="research-work-package:invalid",
        sql_persistence_plan_digest="sha256:" + "0" * 64,
        projection_pair_plan_digest="sha256:" + "0" * 64,
        expected_sql_refs=(
            "context-object:invalid-first",
            "context-object:invalid-second",
        ),
        query=query,
    )


def _plan_digest(
    plan: GitHubResearchLoveTwoAnalysisRecallPlan,
) -> str:
    payload = {
        "schema": plan.schema,
        "work_package_ref": plan.work_package_ref,
        "sql_persistence_plan_digest": plan.sql_persistence_plan_digest,
        "projection_pair_plan_digest": plan.projection_pair_plan_digest,
        "expected_sql_refs": list(plan.expected_sql_refs),
        "query": plan.query.to_mapping(),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _required_mapping(
    value: Mapping[str, Any],
    name: str,
) -> Mapping[str, Any]:
    candidate = value.get(name)
    if not isinstance(candidate, Mapping):
        raise GitHubResearchLoveTwoAnalysisRecallError(
            f"{name} must be an object"
        )
    return candidate


def _required_text(
    value: Mapping[str, Any],
    name: str,
) -> str:
    candidate = value.get(name)
    if not isinstance(candidate, str) or not candidate.strip():
        raise GitHubResearchLoveTwoAnalysisRecallError(
            f"{name} must not be empty"
        )
    return candidate.strip()


__all__ = (
    "GitHubResearchLoveTwoAnalysisRecallCommand",
    "GitHubResearchLoveTwoAnalysisRecallError",
    "GitHubResearchLoveTwoAnalysisRecallPlan",
    "GitHubResearchLoveTwoAnalysisRecallResult",
    "PLAN_SCHEMA",
    "RESULT_SCHEMA",
    "build_github_research_love_two_analysis_recall_plan",
    "recall_github_research_love_analyses",
)
