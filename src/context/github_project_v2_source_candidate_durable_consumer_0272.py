"""Durably consume one approved ProjectV2 SourceCandidate gate record.

0272-r8 is the first durable consumer after the local r7 operator gate. It
reuses the existing SQL context-store contract and writes one immutable
``github_artifact`` record addressed from the gate reference.

Boundaries:
- only ``promote`` and ``merge`` gate records are accepted;
- SQL is the durable authority;
- OpenVINO/E5 and Qdrant remain closed in this phase;
- GitHub remains read-only and no network call is performed;
- Scheduler.run and SHM surfaces are not modified;
- the persisted record is laboratory-neutral and can be oriented later.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
import hashlib
import json
from typing import Any, Mapping, Protocol, Sequence

from context.github_project_v2_source_candidate_gate_0272 import GATE_RECORD_SCHEMA
from context.sql_context_store import SqlContextRecord, build_sql_context_record

DURABLE_CONSUMER_REPORT_SCHEMA = (
    "missipy.github.project_v2_source_candidate_durable_consumer_report.v1"
)
_ALLOWED_INGESTION_MODES = frozenset({"promote", "merge"})
_EXPECTED_STATUS = {"promote": "promoted", "merge": "merged"}


class ExistingSqlContextStore(Protocol):
    """Existing SQLContextStore surface used by dependency injection."""

    def initialize_schema(self) -> None: ...

    def upsert_record(self, record: SqlContextRecord) -> object: ...

    def get_record(self, context_ref: str) -> object | None: ...


@dataclass(frozen=True, slots=True)
class GitHubProjectV2DurableConsumerCommand:
    """Controlled durable-consumption command."""

    execute: bool = False
    policy_decision_id: str = ""


@dataclass(frozen=True, slots=True)
class GitHubProjectV2DurableConsumerPlan:
    """Pure plan built before SQL access."""

    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    gate_record_path: str
    boundaries: Mapping[str, bool]


@dataclass(frozen=True, slots=True)
class GitHubProjectV2DurableConsumerResult:
    """Serializable result of the r8 durable-consumption gate."""

    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    gate_ref: str
    candidate_id: str
    ingestion_mode: str
    target_context_id: str
    sql_ref: str
    durable_record: Mapping[str, Any] = field(default_factory=dict)
    readback_record: Mapping[str, Any] = field(default_factory=dict)
    sql_write_performed: bool = False
    idempotent_replay: bool = False
    rehydrated: bool = False
    boundaries: Mapping[str, bool] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": DURABLE_CONSUMER_REPORT_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "gate_ref": self.gate_ref,
            "candidate_id": self.candidate_id,
            "ingestion_mode": self.ingestion_mode,
            "target_context_id": self.target_context_id,
            "sql_ref": self.sql_ref,
            "durable_record": dict(self.durable_record),
            "readback_record": dict(self.readback_record),
            "sql_write_performed": self.sql_write_performed,
            "idempotent_replay": self.idempotent_replay,
            "rehydrated": self.rehydrated,
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"github_project_v2_durable_consumer_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"execute={self.execute}",
                f"candidate_id={self.candidate_id or '-'}",
                f"ingestion_mode={self.ingestion_mode or '-'}",
                f"sql_ref={self.sql_ref or '-'}",
                f"sql_write_performed={self.sql_write_performed}",
                f"idempotent_replay={self.idempotent_replay}",
                f"rehydrated={self.rehydrated}",
                "openvino_call_performed=False",
                "qdrant_write_performed=False",
                "remote_mutation_allowed=False",
            )
        )


def build_durable_consumer_plan(
    command: GitHubProjectV2DurableConsumerCommand,
    *,
    gate_record_path: str,
) -> GitHubProjectV2DurableConsumerPlan:
    """Build a pure execution plan before reading or writing SQL."""

    issues: list[str] = []
    if not gate_record_path.strip():
        issues.append("gate record path is required")
    if command.execute and not command.policy_decision_id.strip():
        issues.append("policy_decision_id is required for execute mode")
    return GitHubProjectV2DurableConsumerPlan(
        valid=not issues,
        issues=tuple(issues),
        execute=command.execute,
        policy_decision_id=command.policy_decision_id,
        gate_record_path=gate_record_path,
        boundaries=_boundaries(sql_write_allowed=command.execute),
    )


def validate_approved_gate_record(gate_record: Mapping[str, Any]) -> tuple[str, ...]:
    """Validate that one immutable r7 record authorizes durable ingestion."""

    issues: list[str] = []
    if str(gate_record.get("schema", "")) != GATE_RECORD_SCHEMA:
        issues.append("gate record schema mismatch")
    if not str(gate_record.get("gate_ref", "")).startswith(
        "github-project-v2-source-candidate-gate:"
    ):
        issues.append("gate_ref is invalid")

    decision = _mapping(gate_record.get("decision"))
    approval = _mapping(gate_record.get("approval"))
    candidate_after = _mapping(gate_record.get("candidate_after"))
    boundaries = _mapping(gate_record.get("boundaries"))

    action = str(decision.get("action", ""))
    if action not in _ALLOWED_INGESTION_MODES:
        issues.append("gate action must be promote or merge")
    if approval.get("durable_ingestion_allowed") is not True:
        issues.append("gate must explicitly allow durable ingestion")
    if approval.get("durable_ingestion_performed") is not False:
        issues.append("r7 gate must not have performed durable ingestion")
    if str(approval.get("ingestion_mode", "")) != action:
        issues.append("approval ingestion_mode must match decision action")
    if str(candidate_after.get("status", "")) != _EXPECTED_STATUS.get(action, ""):
        issues.append("candidate_after status does not match approved action")
    if str(candidate_after.get("candidate_id", "")) != str(
        gate_record.get("candidate_id", "")
    ):
        issues.append("candidate_id mismatch between gate and candidate_after")
    if action == "merge" and not str(
        approval.get("target_context_id", "")
    ).strip():
        issues.append("merge approval requires target_context_id")

    for key in (
        "sql_write_allowed",
        "sql_write_performed",
        "qdrant_write_allowed",
        "qdrant_write_performed",
        "remote_mutation_allowed",
    ):
        if boundaries.get(key) is not False:
            issues.append(f"r7 boundary must keep {key} false")
    return tuple(dict.fromkeys(issues))


def build_durable_sql_record(gate_record: Mapping[str, Any]) -> SqlContextRecord:
    """Build one deterministic, laboratory-neutral SQL authority record."""

    issues = validate_approved_gate_record(gate_record)
    if issues:
        raise ValueError("; ".join(issues))

    candidate = _mapping(gate_record.get("candidate_after"))
    decision = _mapping(gate_record.get("decision"))
    approval = _mapping(gate_record.get("approval"))
    origin = _mapping(candidate.get("origin"))
    gate_ref = str(gate_record.get("gate_ref", ""))
    candidate_id = str(candidate.get("candidate_id", ""))
    title = str(candidate.get("title", "")).strip()
    body = str(candidate.get("body", ""))
    if not body.strip():
        body = title

    content_digest = hashlib.sha256(
        _canonical_json(candidate).encode("utf-8")
    ).hexdigest()
    metadata = _metadata_tuple(
        {
            "source": "github_project_v2_source_candidate_gate_0272",
            "gate_ref": gate_ref,
            "candidate_id": candidate_id,
            "handoff_ref": str(gate_record.get("handoff_ref", "")),
            "handoff_batch_ref": str(gate_record.get("handoff_batch_ref", "")),
            "change_kind": str(gate_record.get("change_kind", "")),
            "decision_action": str(decision.get("action", "")),
            "target_context_id": str(approval.get("target_context_id", "") or ""),
            "origin_kind": str(origin.get("kind", "")),
            "origin_reference": str(origin.get("reference", "")),
            "origin_repository": str(origin.get("repository", "") or ""),
            "content_digest": f"sha256:{content_digest}",
            "embedding_projection_state": "pending",
            "laboratory_assignment_state": "unassigned",
        }
    )
    return build_sql_context_record(
        kind="github_artifact",
        identity=gate_ref,
        title=title,
        body=body,
        metadata=metadata,
    )


def consume_approved_gate_record(
    gate_record: Mapping[str, Any],
    command: GitHubProjectV2DurableConsumerCommand,
    *,
    store: ExistingSqlContextStore | None = None,
) -> GitHubProjectV2DurableConsumerResult:
    """Plan or execute one immutable SQL ingestion from an approved r7 gate."""

    issues = list(validate_approved_gate_record(gate_record))
    if command.execute and not command.policy_decision_id.strip():
        issues.append("policy_decision_id is required for execute mode")
    if command.execute and store is None:
        issues.append("execute mode requires an existing SQLContextStore object")

    gate_ref = str(gate_record.get("gate_ref", ""))
    candidate_id = str(gate_record.get("candidate_id", ""))
    approval = _mapping(gate_record.get("approval"))
    ingestion_mode = str(approval.get("ingestion_mode", ""))
    target_context_id = str(approval.get("target_context_id", "") or "")

    durable_record: Mapping[str, Any] = {}
    try:
        if not issues:
            durable_record = build_durable_sql_record(gate_record).to_mapping()
    except ValueError as exc:
        issues.append(str(exc))

    if issues or not command.execute:
        return GitHubProjectV2DurableConsumerResult(
            valid=not issues,
            issues=tuple(dict.fromkeys(issues)),
            execute=command.execute,
            policy_decision_id=command.policy_decision_id,
            gate_ref=gate_ref,
            candidate_id=candidate_id,
            ingestion_mode=ingestion_mode,
            target_context_id=target_context_id,
            sql_ref=str(durable_record.get("context_ref", "")),
            durable_record=durable_record,
            boundaries=_boundaries(sql_write_allowed=command.execute),
        )

    assert store is not None
    record = build_durable_sql_record(gate_record)
    _initialize_existing_schema(store)
    existing = store.get_record(record.context_ref)
    write_performed = False
    idempotent_replay = False

    if existing is None:
        store.upsert_record(record)
        write_performed = True
    else:
        existing_mapping = _public_mapping(existing)
        if existing_mapping != record.to_mapping():
            issues.append("immutable durable-record collision")
        else:
            idempotent_replay = True

    readback = store.get_record(record.context_ref)
    readback_mapping = _public_mapping(readback)
    rehydrated = readback_mapping == record.to_mapping()
    if not rehydrated:
        issues.append("SQL readback does not match the durable record")

    return GitHubProjectV2DurableConsumerResult(
        valid=not issues,
        issues=tuple(dict.fromkeys(issues)),
        execute=True,
        policy_decision_id=command.policy_decision_id,
        gate_ref=gate_ref,
        candidate_id=candidate_id,
        ingestion_mode=ingestion_mode,
        target_context_id=target_context_id,
        sql_ref=record.context_ref,
        durable_record=record.to_mapping(),
        readback_record=readback_mapping,
        sql_write_performed=write_performed,
        idempotent_replay=idempotent_replay,
        rehydrated=rehydrated,
        boundaries=_boundaries(
            sql_write_allowed=True,
            sql_write_performed=write_performed,
        ),
    )


def close_durable_consumer_result(
    plan: GitHubProjectV2DurableConsumerPlan,
    *,
    result: GitHubProjectV2DurableConsumerResult | None,
    errors: Sequence[str] = (),
) -> GitHubProjectV2DurableConsumerResult:
    """Close plan and execution errors into one stable result."""

    issues = list(plan.issues)
    issues.extend(str(error) for error in errors if str(error))
    if result is not None:
        issues.extend(result.issues)
        payload = result
    else:
        payload = GitHubProjectV2DurableConsumerResult(
            valid=False,
            issues=(),
            execute=plan.execute,
            policy_decision_id=plan.policy_decision_id,
            gate_ref="",
            candidate_id="",
            ingestion_mode="",
            target_context_id="",
            sql_ref="",
            boundaries=_boundaries(sql_write_allowed=plan.execute),
        )
    if plan.execute and result is None:
        issues.append("execute mode must produce a durable-consumer result")
    return GitHubProjectV2DurableConsumerResult(
        valid=not issues and payload.valid,
        issues=tuple(dict.fromkeys(issues)),
        execute=payload.execute,
        policy_decision_id=payload.policy_decision_id,
        gate_ref=payload.gate_ref,
        candidate_id=payload.candidate_id,
        ingestion_mode=payload.ingestion_mode,
        target_context_id=payload.target_context_id,
        sql_ref=payload.sql_ref,
        durable_record=payload.durable_record,
        readback_record=payload.readback_record,
        sql_write_performed=payload.sql_write_performed,
        idempotent_replay=payload.idempotent_replay,
        rehydrated=payload.rehydrated,
        boundaries=payload.boundaries,
    )


def _initialize_existing_schema(store: ExistingSqlContextStore) -> None:
    initialize = getattr(store, "initialize_schema", None)
    if not callable(initialize):
        raise TypeError("existing SQLContextStore must expose initialize_schema")
    initialize()


def _public_mapping(value: object | None) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    to_mapping = getattr(value, "to_mapping", None)
    if callable(to_mapping):
        payload = to_mapping()
        if isinstance(payload, Mapping):
            return dict(payload)
    if is_dataclass(value) and not isinstance(value, type):
        return dict(asdict(value))
    raise TypeError("SQL record must expose to_mapping or be a mapping/dataclass")


def _metadata_tuple(values: Mapping[str, object]) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (str(key), str(value))
            for key, value in values.items()
            if str(key).strip() and str(value).strip()
        )
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _boundaries(
    *,
    sql_write_allowed: bool,
    sql_write_performed: bool = False,
) -> dict[str, bool]:
    return {
        "existing_sql_context_store_reused": True,
        "r7_gate_record_required": True,
        "durable_ingestion_allowed": sql_write_allowed,
        "sql_write_allowed": sql_write_allowed,
        "sql_write_performed": sql_write_performed,
        "sql_readback_required": True,
        "openvino_call_allowed": False,
        "openvino_call_performed": False,
        "qdrant_write_allowed": False,
        "qdrant_write_performed": False,
        "external_call_performed": False,
        "graphql_query_performed": False,
        "graphql_mutation_allowed": False,
        "remote_mutation_allowed": False,
        "scheduler_modified": False,
        "shm_modified": False,
        "laboratory_neutral_record": True,
        "local_authority_preserved": True,
    }
