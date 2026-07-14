"""Real SQL/OpenVINO/Qdrant memory closure for one portable specialist.

Phase 0284-r6 composes the existing 0284-r5 portable-specialist smoke with the
existing 0283 scoped Qdrant executor factory.  It does not add a second memory
path: the r5 call still performs the existing 0274 SQL write, 0261 passage and
query embeddings, 0262 projection, 0263 reference-only recall and SQL
rehydration.

Preview is inspection-only.  Execute mode requires two explicit operator
acknowledgements because the Qdrant point is persistent and no automatic SQL or
Qdrant cleanup is performed.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from contracts.scheduler import SchedulerContract
from context.fake_laboratory_closed_local_handoff_0274 import (
    ExistingObservationBus,
    ExistingSqlContextStore,
)
from context.github_project_v2_source_candidate_vector_projection_0272 import (
    EmbeddingSpaceProfile,
)
from context.sql_context_store import DbApiSqlContextStore
from context.specialists_laboratories_existing_chain_smoke_0284 import (
    PortableSpecialistExistingChainSmokeCommand,
    PortableSpecialistExistingChainSmokeResult,
    run_portable_specialist_existing_chain_smoke,
)
from inference.qdrant_real_binding_configuration_0283 import (
    QdrantRealBindingConfigurationResult,
)
from inference.qdrant_scoped_executor_factory_0283 import (
    QdrantScopedExecutorBinding,
    QdrantScopedExecutorFactoryError,
    QdrantScopedExecutorFactoryPolicy,
    QdrantScopedExecutorFactoryReport,
    build_qdrant_scoped_executor_binding,
    inspect_qdrant_scoped_executor_factory,
)

PORTABLE_SPECIALIST_REAL_MEMORY_CLOSURE_VERSION = "0284.r6"
PORTABLE_SPECIALIST_REAL_MEMORY_COMMAND_SCHEMA = (
    "missipy.specialist.real_memory_closure_command.v1"
)
PORTABLE_SPECIALIST_REAL_MEMORY_RESULT_SCHEMA = (
    "missipy.specialist.real_memory_closure_result.v1"
)
EXPECTED_E5_DIMENSION = 384

EmbeddingCallable = Callable[[str, str, str | None, str], Mapping[str, Any]]
BindingBuilder = Callable[
    [QdrantRealBindingConfigurationResult, QdrantScopedExecutorFactoryPolicy | None],
    QdrantScopedExecutorBinding,
]
FactoryInspector = Callable[
    [QdrantRealBindingConfigurationResult, QdrantScopedExecutorFactoryPolicy | None],
    QdrantScopedExecutorFactoryReport,
]
SpecialistRunner = Callable[..., Any]


class PortableSpecialistRealMemoryClosureError(RuntimeError):
    """Raised when r6 would weaken the authority or effect boundaries."""


@dataclass(frozen=True, slots=True)
class PortableSpecialistRealMemoryClosureCommand:
    """One preview or explicitly authorised real-memory closure."""

    specialist_smoke: PortableSpecialistExistingChainSmokeCommand
    projection_configuration: QdrantRealBindingConfigurationResult
    recall_configuration: QdrantRealBindingConfigurationResult
    execute: bool = False
    authorize_real_memory: bool = False
    authorize_persistent_qdrant_point: bool = False
    schema: str = PORTABLE_SPECIALIST_REAL_MEMORY_COMMAND_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != PORTABLE_SPECIALIST_REAL_MEMORY_COMMAND_SCHEMA:
            raise PortableSpecialistRealMemoryClosureError(
                "unsupported portable specialist real-memory command schema"
            )
        if not isinstance(
            self.specialist_smoke,
            PortableSpecialistExistingChainSmokeCommand,
        ):
            raise PortableSpecialistRealMemoryClosureError(
                "specialist_smoke must be PortableSpecialistExistingChainSmokeCommand"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "specialist_smoke": self.specialist_smoke.to_mapping(),
            "projection_configuration": (
                self.projection_configuration.to_json_dict()
            ),
            "recall_configuration": self.recall_configuration.to_json_dict(),
            "execute": self.execute,
            "authorize_real_memory": self.authorize_real_memory,
            "authorize_persistent_qdrant_point": (
                self.authorize_persistent_qdrant_point
            ),
            "automatic_cleanup_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class PortableSpecialistRealMemoryClosureResult:
    """Serializable proof of the portable specialist memory path."""

    valid: bool
    issues: tuple[str, ...]
    command: PortableSpecialistRealMemoryClosureCommand
    specialist_smoke: PortableSpecialistExistingChainSmokeResult | None = None
    projection_factory: Mapping[str, Any] = field(default_factory=dict)
    recall_factory: Mapping[str, Any] = field(default_factory=dict)
    sql_ref: str = ""
    passage_embedding_ref: str = ""
    query_embedding_ref: str = ""
    projected_point_ids: tuple[str, ...] = ()
    returned_sql_refs: tuple[str, ...] = ()
    preview_only: bool = True
    real_sql_authority_used: bool = False
    real_openvino_e5_used: bool = False
    real_qdrant_projection_used: bool = False
    real_qdrant_recall_used: bool = False
    qdrant_returns_references_only: bool = False
    sql_rehydration_verified: bool = False
    portable_identity_preserved: bool = False
    memory_closed: bool = False
    projection_binding_constructed: bool = False
    recall_binding_constructed: bool = False
    projection_binding_closed: bool = False
    recall_binding_closed: bool = False
    persistent_qdrant_point_created: bool = False
    persistent_qdrant_point_may_exist: bool = False
    persistent_sql_record_may_exist: bool = False
    automatic_cleanup_performed: bool = False
    existing_scheduler_used: bool = True
    scheduler_created: bool = False
    scheduler_modified: bool = False
    new_qdrant_executor_added: bool = False
    new_transport_added: bool = False
    github_mutation_performed: bool = False
    embedding_runtime_injected: bool = False
    schema: str = PORTABLE_SPECIALIST_REAL_MEMORY_RESULT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != PORTABLE_SPECIALIST_REAL_MEMORY_RESULT_SCHEMA:
            raise PortableSpecialistRealMemoryClosureError(
                "unsupported portable specialist real-memory result schema"
            )
        forbidden = (
            not self.existing_scheduler_used,
            self.scheduler_created,
            self.scheduler_modified,
            self.new_qdrant_executor_added,
            self.new_transport_added,
            self.github_mutation_performed,
            self.automatic_cleanup_performed,
        )
        if any(forbidden):
            raise PortableSpecialistRealMemoryClosureError(
                "r6 must preserve Scheduler, transport and authority boundaries"
            )
        if self.valid and not self.preview_only:
            required = (
                self.specialist_smoke is not None,
                self.real_sql_authority_used,
                self.real_openvino_e5_used,
                self.real_qdrant_projection_used,
                self.real_qdrant_recall_used,
                self.qdrant_returns_references_only,
                self.sql_rehydration_verified,
                self.portable_identity_preserved,
                self.memory_closed,
                self.projection_binding_constructed,
                self.recall_binding_constructed,
                self.projection_binding_closed,
                self.recall_binding_closed,
                self.persistent_qdrant_point_created,
            )
            if not all(required):
                raise PortableSpecialistRealMemoryClosureError(
                    "valid execute result requires the complete real memory path"
                )

    def to_mapping(self) -> dict[str, object]:
        live_path_status = (
            "green"
            if self.valid and not self.preview_only
            else "n/a"
            if self.preview_only
            else "red"
        )
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "command": self.command.to_mapping(),
            "specialist_smoke": (
                None
                if self.specialist_smoke is None
                else self.specialist_smoke.to_mapping()
            ),
            "projection_factory": dict(self.projection_factory),
            "recall_factory": dict(self.recall_factory),
            "sql_ref": self.sql_ref,
            "passage_embedding_ref": self.passage_embedding_ref,
            "query_embedding_ref": self.query_embedding_ref,
            "projected_point_ids": list(self.projected_point_ids),
            "returned_sql_refs": list(self.returned_sql_refs),
            "preview_only": self.preview_only,
            "real_sql_authority_used": self.real_sql_authority_used,
            "real_openvino_e5_used": self.real_openvino_e5_used,
            "real_qdrant_projection_used": self.real_qdrant_projection_used,
            "real_qdrant_recall_used": self.real_qdrant_recall_used,
            "qdrant_returns_references_only": (
                self.qdrant_returns_references_only
            ),
            "sql_rehydration_verified": self.sql_rehydration_verified,
            "portable_identity_preserved": self.portable_identity_preserved,
            "memory_closed": self.memory_closed,
            "projection_binding_constructed": (
                self.projection_binding_constructed
            ),
            "recall_binding_constructed": self.recall_binding_constructed,
            "projection_binding_closed": self.projection_binding_closed,
            "recall_binding_closed": self.recall_binding_closed,
            "persistent_qdrant_point_created": (
                self.persistent_qdrant_point_created
            ),
            "persistent_qdrant_point_may_exist": (
                self.persistent_qdrant_point_may_exist
            ),
            "persistent_sql_record_may_exist": (
                self.persistent_sql_record_may_exist
            ),
            "cleanup_required": (
                self.persistent_qdrant_point_created
                or self.persistent_qdrant_point_may_exist
                or self.persistent_sql_record_may_exist
            ),
            "automatic_cleanup_performed": self.automatic_cleanup_performed,
            "embedding_runtime_injected": self.embedding_runtime_injected,
            "existing_scheduler_used": self.existing_scheduler_used,
            "scheduler_created": self.scheduler_created,
            "scheduler_modified": self.scheduler_modified,
            "new_qdrant_executor_added": self.new_qdrant_executor_added,
            "new_transport_added": self.new_transport_added,
            "github_mutation_performed": self.github_mutation_performed,
            "sql_remains_authority": True,
            "qdrant_projection_and_recall_only": True,
            "eventbus_observation_only": True,
            "live_path_status": live_path_status,
            "live_path_uses_real_backend": (
                self.valid and not self.preview_only
            ),
        }


async def run_portable_specialist_real_memory_closure(
    scheduler: SchedulerContract,
    command: PortableSpecialistRealMemoryClosureCommand,
    *,
    store: ExistingSqlContextStore,
    passage_profile: EmbeddingSpaceProfile,
    event_bus: ExistingObservationBus | None = None,
    factory_policy: QdrantScopedExecutorFactoryPolicy | None = None,
    embedding_runtime: EmbeddingCallable | None = None,
    factory_inspector: FactoryInspector = inspect_qdrant_scoped_executor_factory,
    binding_builder: BindingBuilder = build_qdrant_scoped_executor_binding,
    specialist_runner: SpecialistRunner = (
        run_portable_specialist_existing_chain_smoke
    ),
) -> PortableSpecialistRealMemoryClosureResult:
    """Preview or execute the existing specialist memory path with r3 bindings."""

    if not isinstance(scheduler, SchedulerContract):
        raise TypeError("scheduler must implement SchedulerContract")
    if not isinstance(command, PortableSpecialistRealMemoryClosureCommand):
        raise TypeError(
            "command must be PortableSpecialistRealMemoryClosureCommand"
        )

    issues = list(validate_portable_specialist_real_memory_command(command))
    if command.execute and not isinstance(store, DbApiSqlContextStore):
        issues.append(
            "execute requires the existing concrete DbApiSqlContextStore"
        )
    issues.extend(
        _passage_profile_issues(
            passage_profile,
            command.projection_configuration,
        )
    )
    projection_report = factory_inspector(
        command.projection_configuration,
        factory_policy,
    )
    recall_report = factory_inspector(
        command.recall_configuration,
        factory_policy,
    )
    issues.extend(projection_report.issues)
    issues.extend(recall_report.issues)

    if issues or not command.execute:
        return _result(
            command=command,
            issues=issues,
            projection_factory=projection_report.to_json_dict(),
            recall_factory=recall_report.to_json_dict(),
            preview_only=True,
            embedding_runtime_injected=embedding_runtime is not None,
        )

    projection_binding: QdrantScopedExecutorBinding | None = None
    recall_binding: QdrantScopedExecutorBinding | None = None
    projection_closed = False
    recall_closed = False
    specialist_result: PortableSpecialistExistingChainSmokeResult | None = None
    recall_factory_calls = 0

    try:
        projection_binding = binding_builder(
            command.projection_configuration,
            factory_policy,
        )
        recall_binding = binding_builder(
            command.recall_configuration,
            factory_policy,
        )

        def recall_executor_factory(sql_ref: str) -> Any:
            nonlocal recall_factory_calls
            recall_factory_calls += 1
            if recall_factory_calls > 1:
                raise PortableSpecialistRealMemoryClosureError(
                    "existing smoke requested more than one recall executor"
                )
            if not sql_ref.startswith("sql:"):
                raise PortableSpecialistRealMemoryClosureError(
                    "recall executor requires a typed sql_ref"
                )
            assert recall_binding is not None
            return recall_binding.executor

        specialist_result = await specialist_runner(
            scheduler,
            command.specialist_smoke,
            store=store,
            passage_profile=passage_profile,
            embedder=embedding_runtime,
            projection_executor=projection_binding.executor,
            recall_executor_factory=recall_executor_factory,
            event_bus=event_bus,
        )
    except QdrantScopedExecutorFactoryError as exc:
        issues.extend(exc.report.issues)
    except Exception as exc:
        issues.append(
            "portable specialist real-memory execution failed: "
            f"{type(exc).__name__}: {_safe_message(exc)}"
        )
    finally:
        if recall_binding is not None:
            try:
                recall_binding.close()
                recall_closed = True
            except Exception as exc:
                issues.append(
                    "recall binding close failed: "
                    f"{type(exc).__name__}: {_safe_message(exc)}"
                )
        if projection_binding is not None:
            try:
                projection_binding.close()
                projection_closed = True
            except Exception as exc:
                issues.append(
                    "projection binding close failed: "
                    f"{type(exc).__name__}: {_safe_message(exc)}"
                )

    projection_factory = (
        projection_report.to_json_dict()
        if projection_binding is None
        else projection_binding.report.to_json_dict()
    )
    recall_factory = (
        recall_report.to_json_dict()
        if recall_binding is None
        else recall_binding.report.to_json_dict()
    )
    if specialist_result is None:
        return _result(
            command=command,
            issues=issues,
            projection_factory=projection_factory,
            recall_factory=recall_factory,
            preview_only=False,
            projection_binding_constructed=projection_binding is not None,
            recall_binding_constructed=recall_binding is not None,
            projection_binding_closed=projection_closed,
            recall_binding_closed=recall_closed,
            persistent_qdrant_point_may_exist=(
                command.execute and projection_binding is not None
            ),
            persistent_sql_record_may_exist=command.execute,
            embedding_runtime_injected=embedding_runtime is not None,
        )

    verification = verify_portable_specialist_real_memory_result(
        specialist_result,
        embedding_runtime_injected=embedding_runtime is not None,
    )
    issues.extend(verification["issues"])
    if recall_factory_calls != 1:
        issues.append("existing smoke must request exactly one recall executor")

    return _result(
        command=command,
        issues=issues,
        specialist_smoke=specialist_result,
        projection_factory=projection_factory,
        recall_factory=recall_factory,
        sql_ref=str(verification["sql_ref"]),
        passage_embedding_ref=str(verification["passage_embedding_ref"]),
        query_embedding_ref=str(verification["query_embedding_ref"]),
        projected_point_ids=tuple(verification["projected_point_ids"]),
        returned_sql_refs=tuple(verification["returned_sql_refs"]),
        preview_only=False,
        real_sql_authority_used=bool(verification["real_sql_authority_used"]),
        real_openvino_e5_used=bool(verification["real_openvino_e5_used"]),
        real_qdrant_projection_used=bool(
            verification["real_qdrant_projection_used"]
        ),
        real_qdrant_recall_used=bool(verification["real_qdrant_recall_used"]),
        qdrant_returns_references_only=bool(
            verification["qdrant_returns_references_only"]
        ),
        sql_rehydration_verified=bool(
            verification["sql_rehydration_verified"]
        ),
        portable_identity_preserved=bool(
            verification["portable_identity_preserved"]
        ),
        memory_closed=bool(verification["memory_closed"]),
        projection_binding_constructed=projection_binding is not None,
        recall_binding_constructed=recall_binding is not None,
        projection_binding_closed=projection_closed,
        recall_binding_closed=recall_closed,
        persistent_qdrant_point_created=bool(
            verification["real_qdrant_projection_used"]
        ),
        persistent_qdrant_point_may_exist=bool(
            command.execute and projection_binding is not None
        ),
        persistent_sql_record_may_exist=command.execute,
        embedding_runtime_injected=embedding_runtime is not None,
    )


def validate_portable_specialist_real_memory_command(
    command: PortableSpecialistRealMemoryClosureCommand,
) -> tuple[str, ...]:
    """Validate the immutable configuration and double effect gate."""

    issues: list[str] = []
    projection = command.projection_configuration
    recall = command.recall_configuration
    if not projection.valid:
        issues.append("projection configuration must be valid")
    if not recall.valid:
        issues.append("recall configuration must be valid")
    if projection.requested_operations != ("projection",):
        issues.append("projection configuration must be projection-only")
    if recall.requested_operations != ("recall",):
        issues.append("recall configuration must be recall-only")
    if not projection.effect_gate.allow_write:
        issues.append("projection effect gate must allow write")
    if projection.effect_gate.allow_search:
        issues.append("projection effect gate must forbid search")
    if not recall.effect_gate.allow_search:
        issues.append("recall effect gate must allow search")
    if recall.effect_gate.allow_write:
        issues.append("recall effect gate must forbid write")
    if (
        projection.effect_gate.policy_decision_id
        != recall.effect_gate.policy_decision_id
    ):
        issues.append("projection and recall must share policy_decision_id")
    if projection.target.to_mapping() != recall.target.to_mapping():
        issues.append("projection and recall targets must match")
    if projection.target.vector_dimension != EXPECTED_E5_DIMENSION:
        issues.append("multilingual-e5-small dimension must be 384")
    if (
        projection.sql_authority_scope.to_mapping()
        != recall.sql_authority_scope.to_mapping()
    ):
        issues.append("projection and recall SQL authority scopes must match")
    if projection.connection.to_mapping() != recall.connection.to_mapping():
        issues.append("projection and recall connections must match")
    if (
        projection.transport_policy.to_mapping()
        != recall.transport_policy.to_mapping()
    ):
        issues.append("projection and recall transport policies must match")
    if projection.projection_policy != recall.projection_policy:
        issues.append("projection and recall projection policies must match")
    if projection.api_key_env_var != recall.api_key_env_var:
        issues.append("projection and recall API key sources must match")
    smoke = command.specialist_smoke.smoke
    policy_ids = {
        projection.effect_gate.policy_decision_id,
        recall.effect_gate.policy_decision_id,
        smoke.handoff.policy_decision_id,
        smoke.recall.policy_decision_id,
    }
    if len(policy_ids) != 1:
        issues.append(
            "specialist smoke, projection and recall must share policy_decision_id"
        )
    if smoke.handoff.model_dir != smoke.recall.model_dir:
        issues.append("passage and query OpenVINO model_dir values must match")
    if smoke.handoff.device != smoke.recall.device:
        issues.append("passage and query OpenVINO devices must match")
    if command.execute:
        if not command.authorize_real_memory:
            issues.append("execute requires authorize_real_memory")
        if not command.authorize_persistent_qdrant_point:
            issues.append(
                "execute requires authorize_persistent_qdrant_point"
            )
    elif (
        command.authorize_real_memory
        or command.authorize_persistent_qdrant_point
    ):
        issues.append("effect authorizations require execute")
    return tuple(issues)


def verify_portable_specialist_real_memory_result(
    specialist_result: Any,
    *,
    embedding_runtime_injected: bool,
) -> dict[str, Any]:
    """Verify real backend evidence without performing another effect."""

    issues: list[str] = []
    existing = specialist_result.existing_smoke
    handoff = _mapping(existing.handoff)
    recall = _mapping(existing.recall)
    passage_report = _mapping(handoff.get("embedding"))
    passage = _mapping(passage_report.get("embedding"))
    query_report = _mapping(recall.get("query_embedding"))
    query = _mapping(query_report.get("embedding"))
    projection = _mapping(handoff.get("projection"))
    projection_write = _mapping(projection.get("write_result"))
    recall_rehydrate = _mapping(recall.get("recall_rehydrate"))
    sql_ref = str(existing.sql_ref)
    returned_sql_refs = tuple(
        str(value) for value in recall_rehydrate.get("sql_refs", ())
    )
    hydrated_records = tuple(
        value
        for value in recall_rehydrate.get("hydrated_records", ())
        if isinstance(value, Mapping)
    )
    projected_point_ids = tuple(
        str(value) for value in projection_write.get("point_ids", ())
    )

    passage_issues = _real_embedding_issues(passage, role="passage")
    query_issues = _real_embedding_issues(query, role="query")
    issues.extend(passage_issues)
    issues.extend(query_issues)
    if embedding_runtime_injected:
        issues.append(
            "execute used an injected embedding runtime; real OpenVINO is not proven"
        )

    real_sql = bool(
        sql_ref.startswith("sql:")
        and handoff.get("sql_write_performed") is True
        and handoff.get("sql_readback_performed") is True
    )
    real_openvino = bool(
        not embedding_runtime_injected
        and not passage_issues
        and not query_issues
        and handoff.get("openvino_call_performed") is True
        and recall.get("query_openvino_call_performed") is True
    )
    real_projection = bool(
        handoff.get("qdrant_write_performed") is True
        and projection.get("valid") is True
        and projection.get("execute") is True
        and projection.get("dry_run") is False
        and projection_write.get("acknowledged") is True
        and projected_point_ids
    )
    refs_only = bool(
        recall_rehydrate.get("qdrant_recall_refs_only") is True
        and recall_rehydrate.get("sql_remains_authority") is True
    )
    real_recall = bool(
        recall.get("qdrant_recall_performed") is True
        and recall_rehydrate.get("valid") is True
        and recall_rehydrate.get("execute") is True
        and recall_rehydrate.get("dry_run") is False
        and refs_only
    )
    rehydrated = bool(
        recall.get("sql_rehydrate_performed") is True
        and sql_ref in returned_sql_refs
        and any(record.get("context_ref") == sql_ref for record in hydrated_records)
    )
    identity = bool(
        specialist_result.portable_identity_preserved
        and specialist_result.message_contract_closed
    )
    if not real_sql:
        issues.append("real SQL write/readback evidence is incomplete")
    if not real_projection:
        issues.append("real Qdrant projection evidence is incomplete")
    if not refs_only:
        issues.append("Qdrant recall must return references only")
    if not real_recall:
        issues.append("real Qdrant recall evidence is incomplete")
    if not rehydrated:
        issues.append("Qdrant sql_ref was not rehydrated from SQL authority")
    if not identity:
        issues.append("portable specialist identity was not preserved")

    memory_closed = bool(
        not issues
        and specialist_result.valid
        and real_sql
        and real_openvino
        and real_projection
        and real_recall
        and rehydrated
        and identity
    )
    return {
        "issues": tuple(dict.fromkeys(issues)),
        "sql_ref": sql_ref,
        "passage_embedding_ref": str(passage.get("embedding_ref", "")),
        "query_embedding_ref": str(query.get("embedding_ref", "")),
        "projected_point_ids": projected_point_ids,
        "returned_sql_refs": returned_sql_refs,
        "real_sql_authority_used": real_sql,
        "real_openvino_e5_used": real_openvino,
        "real_qdrant_projection_used": real_projection,
        "real_qdrant_recall_used": real_recall,
        "sql_rehydration_verified": rehydrated,
        "portable_identity_preserved": identity,
        "memory_closed": memory_closed,
        "qdrant_returns_references_only": refs_only,
    }


def _real_embedding_issues(
    embedding: Mapping[str, Any],
    *,
    role: str,
) -> tuple[str, ...]:
    issues: list[str] = []
    if not embedding:
        return (f"{role} embedding is missing",)
    if embedding.get("role") != role:
        issues.append(f"{role} embedding role mismatch")
    if embedding.get("dimension") != EXPECTED_E5_DIMENSION:
        issues.append(f"{role} embedding dimension must be 384")
    if embedding.get("normalized") is not True:
        issues.append(f"{role} embedding must be normalized")
    vector = embedding.get("vector")
    if not isinstance(vector, list) or len(vector) != EXPECTED_E5_DIMENSION:
        issues.append(f"{role} vector length must be 384")
    metadata = _mapping(embedding.get("metadata"))
    model = str(metadata.get("model", ""))
    model_path = str(metadata.get("model_path", ""))
    if not model or model.startswith("demo.") or "e5-small" not in model.lower():
        issues.append(f"{role} embedding must use the real E5-small model")
    if not model_path:
        issues.append(f"{role} embedding model_path must be recorded")
    elif "multilingual-e5-small" not in model_path.lower():
        issues.append(
            f"{role} embedding model_path must identify multilingual-e5-small"
        )
    return tuple(issues)


def _passage_profile_issues(
    profile: EmbeddingSpaceProfile,
    projection: QdrantRealBindingConfigurationResult,
) -> tuple[str, ...]:
    issues: list[str] = []
    if not isinstance(profile, EmbeddingSpaceProfile):
        return ("passage_profile must be EmbeddingSpaceProfile",)
    if profile.role != "passage":
        issues.append("passage_profile.role must be passage")
    if profile.dimension != EXPECTED_E5_DIMENSION:
        issues.append("passage_profile dimension must be 384")
    if profile.collection_name != projection.target.collection_name:
        issues.append(
            "passage_profile collection must match Qdrant projection target"
        )
    return tuple(issues)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _result(
    *,
    command: PortableSpecialistRealMemoryClosureCommand,
    issues: Sequence[str],
    specialist_smoke: PortableSpecialistExistingChainSmokeResult | None = None,
    projection_factory: Mapping[str, Any] | None = None,
    recall_factory: Mapping[str, Any] | None = None,
    sql_ref: str = "",
    passage_embedding_ref: str = "",
    query_embedding_ref: str = "",
    projected_point_ids: tuple[str, ...] = (),
    returned_sql_refs: tuple[str, ...] = (),
    preview_only: bool = True,
    real_sql_authority_used: bool = False,
    real_openvino_e5_used: bool = False,
    real_qdrant_projection_used: bool = False,
    real_qdrant_recall_used: bool = False,
    qdrant_returns_references_only: bool = False,
    sql_rehydration_verified: bool = False,
    portable_identity_preserved: bool = False,
    memory_closed: bool = False,
    projection_binding_constructed: bool = False,
    recall_binding_constructed: bool = False,
    projection_binding_closed: bool = False,
    recall_binding_closed: bool = False,
    persistent_qdrant_point_created: bool = False,
    persistent_qdrant_point_may_exist: bool = False,
    persistent_sql_record_may_exist: bool = False,
    embedding_runtime_injected: bool = False,
) -> PortableSpecialistRealMemoryClosureResult:
    normalized = tuple(dict.fromkeys(str(item) for item in issues if str(item)))
    return PortableSpecialistRealMemoryClosureResult(
        valid=not normalized,
        issues=normalized,
        command=command,
        specialist_smoke=specialist_smoke,
        projection_factory=dict(projection_factory or {}),
        recall_factory=dict(recall_factory or {}),
        sql_ref=sql_ref,
        passage_embedding_ref=passage_embedding_ref,
        query_embedding_ref=query_embedding_ref,
        projected_point_ids=projected_point_ids,
        returned_sql_refs=returned_sql_refs,
        preview_only=preview_only,
        real_sql_authority_used=real_sql_authority_used,
        real_openvino_e5_used=real_openvino_e5_used,
        real_qdrant_projection_used=real_qdrant_projection_used,
        real_qdrant_recall_used=real_qdrant_recall_used,
        qdrant_returns_references_only=qdrant_returns_references_only,
        sql_rehydration_verified=sql_rehydration_verified,
        portable_identity_preserved=portable_identity_preserved,
        memory_closed=memory_closed,
        projection_binding_constructed=projection_binding_constructed,
        recall_binding_constructed=recall_binding_constructed,
        projection_binding_closed=projection_binding_closed,
        recall_binding_closed=recall_binding_closed,
        persistent_qdrant_point_created=persistent_qdrant_point_created,
        persistent_qdrant_point_may_exist=persistent_qdrant_point_may_exist,
        persistent_sql_record_may_exist=persistent_sql_record_may_exist,
        embedding_runtime_injected=embedding_runtime_injected,
    )


def _safe_message(exc: Exception) -> str:
    text = str(exc).strip() or type(exc).__name__
    return text[:300]


__all__ = (
    "EXPECTED_E5_DIMENSION",
    "PORTABLE_SPECIALIST_REAL_MEMORY_CLOSURE_VERSION",
    "PORTABLE_SPECIALIST_REAL_MEMORY_COMMAND_SCHEMA",
    "PORTABLE_SPECIALIST_REAL_MEMORY_RESULT_SCHEMA",
    "PortableSpecialistRealMemoryClosureCommand",
    "PortableSpecialistRealMemoryClosureError",
    "PortableSpecialistRealMemoryClosureResult",
    "run_portable_specialist_real_memory_closure",
    "validate_portable_specialist_real_memory_command",
    "verify_portable_specialist_real_memory_result",
)
