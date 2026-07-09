"""Scheduler-managed SQLContextStore usage.

0259 adapts SQL usage under Scheduler ownership.  It does not create a new SQL
store and it does not start PostgreSQL.  PostgreSQL lifecycle remains owned by
OpenRC/host administration.  Scheduler owns the Autodoc runtime object usage:
``sql.context.write`` and ``sql.context.rehydrate``.

The module is intentionally dependency-injection based.  A real existing
DbApiSqlContextStore, or another existing compatible SQLContextStore object, is
provided by the Scheduler-owned runtime bootstrap in a later execution patch.
This patch validates the capability path and performs controlled execution only
when an existing store object is passed explicitly.

No RuntimeManager is created.  No Scheduler.run modification is made.  No
component-specific production CLI becomes the runtime API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Callable, Mapping, MutableMapping, Protocol
import uuid


SQL_WRITE_CAPABILITY = "sql.context.write"
SQL_REHYDRATE_CAPABILITY = "sql.context.rehydrate"
SQL_COMPONENT_ID = "sql_context_store"


class ExistingSqlContextStoreLike(Protocol):
    """Existing SQLContextStore protocol used by duck typing only."""

    def controlled_write(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        ...


@dataclass(frozen=True)
class SchedulerManagedSqlContextWriteRequest:
    """Controlled SQL context write request routed by Scheduler."""

    intent_id: str
    text: str
    text_kind: str = "passage"
    source_ref: str = "scheduler-managed-sql-context-store-usage-0259"
    table: str = "context_records"
    operation: str = "insert_if_absent"
    capability: str = SQL_WRITE_CAPABILITY
    component_id: str = SQL_COMPONENT_ID
    policy_decision_id: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "text": self.text,
            "text_kind": self.text_kind,
            "source_ref": self.source_ref,
            "table": self.table,
            "operation": self.operation,
            "capability": self.capability,
            "component_id": self.component_id,
            "policy_decision_id": self.policy_decision_id,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SchedulerManagedSqlContextStoreUsageResult:
    """Result for Scheduler-managed SQLContextStore usage."""

    valid: bool
    issues: tuple[str, ...]
    request: SchedulerManagedSqlContextWriteRequest
    execute: bool
    dry_run: bool
    scheduler_owned: bool = True
    uses_existing_store_object: bool = True
    starts_postgresql: bool = False
    creates_sql_store: bool = False
    creates_runtime_manager: bool = False
    modifies_scheduler_run: bool = False
    sql_ref: str = ""
    store_result: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scheduler_managed_sql_context_store_usage": True,
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "dry_run": self.dry_run,
            "scheduler_owned": self.scheduler_owned,
            "uses_existing_store_object": self.uses_existing_store_object,
            "starts_postgresql": self.starts_postgresql,
            "creates_sql_store": self.creates_sql_store,
            "creates_runtime_manager": self.creates_runtime_manager,
            "modifies_scheduler_run": self.modifies_scheduler_run,
            "sql_ref": self.sql_ref,
            "request": self.request.to_payload(),
            "store_result": dict(self.store_result),
        }


def _attachment_payload(bootstrap_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    attachment = bootstrap_payload.get("attachment", {})
    return attachment if isinstance(attachment, Mapping) else {}


def validate_scheduler_sql_capability_attachment(
    bootstrap_payload: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate that Scheduler bootstrap exposes SQL capabilities."""

    issues: list[str] = []
    if not bootstrap_payload.get("scheduler_runtime_bootstrap_registry_attachment", False):
        issues.append("bootstrap payload must be scheduler_runtime_bootstrap_registry_attachment")
    if not bootstrap_payload.get("valid", False):
        issues.append("bootstrap payload must be valid")
    attachment = _attachment_payload(bootstrap_payload)
    if attachment.get("owner") != "scheduler":
        issues.append("attachment owner must be scheduler")
    if not attachment.get("launcher_bootstrap_only", False):
        issues.append("launcher must remain bootstrap-only")
    if not attachment.get("no_cli_per_component", False):
        issues.append("runtime API must keep no CLI per component")
    if attachment.get("creates_runtime_manager", False):
        issues.append("must not create a RuntimeManager")
    if attachment.get("starts_components", False):
        issues.append("0259 must not start external services or runtime components")
    if attachment.get("modifies_scheduler_run", False):
        issues.append("must not modify Scheduler.run")

    capability_index = attachment.get("capability_index", {})
    if not isinstance(capability_index, Mapping):
        issues.append("capability_index must be present")
        capability_index = {}
    if capability_index.get(SQL_WRITE_CAPABILITY) != SQL_COMPONENT_ID:
        issues.append("sql.context.write must resolve to sql_context_store")
    if capability_index.get(SQL_REHYDRATE_CAPABILITY) != SQL_COMPONENT_ID:
        issues.append("sql.context.rehydrate must resolve to sql_context_store")

    dependency_index = attachment.get("dependency_index", {})
    if isinstance(dependency_index, Mapping):
        if dependency_index.get(SQL_COMPONENT_ID) not in ([], (), None):
            issues.append("sql_context_store usage must not depend on Qdrant or OpenVINO")
    else:
        issues.append("dependency_index must be present")
    return tuple(issues)


def build_scheduler_managed_sql_context_write_request(
    bootstrap_payload: Mapping[str, Any],
    *,
    text: str,
    intent_id: str = "",
    policy_decision_id: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> SchedulerManagedSqlContextWriteRequest:
    """Build a controlled SQL write request routed by Scheduler."""

    if not intent_id:
        intent_id = "intent:sql-context-write:" + uuid.uuid4().hex
    return SchedulerManagedSqlContextWriteRequest(
        intent_id=intent_id,
        text=text,
        policy_decision_id=policy_decision_id,
        metadata={
            "bootstrap_digest": bootstrap_payload.get("registry_payload_digest", ""),
            **dict(metadata or {}),
        },
    )


def _extract_sql_ref(result: Mapping[str, Any]) -> str:
    for key in ("sql_ref", "record_ref", "record_id", "id"):
        value = result.get(key)
        if value:
            return str(value)
    nested = result.get("record")
    if isinstance(nested, Mapping):
        return _extract_sql_ref(nested)
    return ""


def _call_existing_store(store: object, payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """Call an existing SQLContextStore-like object without knowing its class."""

    controlled_write = getattr(store, "controlled_write", None)
    if callable(controlled_write):
        result = controlled_write(payload)
        return dict(result) if isinstance(result, Mapping) else {"result": result}

    upsert_record = getattr(store, "upsert_record", None)
    if callable(upsert_record):
        try:
            result = upsert_record(payload)
        except TypeError:
            result = upsert_record(
                record_id=payload.get("intent_id"),
                content=payload.get("text"),
                metadata=dict(payload.get("metadata", {})),
            )
        return dict(result) if isinstance(result, Mapping) else {"result": result}

    raise TypeError("existing SQLContextStore object must expose controlled_write or upsert_record")


def run_scheduler_managed_sql_context_store_usage(
    bootstrap_payload: Mapping[str, Any],
    *,
    text: str,
    execute: bool = False,
    policy_decision_id: str = "",
    store: object | None = None,
    intent_id: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> SchedulerManagedSqlContextStoreUsageResult:
    """Route SQL context write usage through Scheduler-owned capability metadata."""

    request = build_scheduler_managed_sql_context_write_request(
        bootstrap_payload,
        text=text,
        intent_id=intent_id,
        policy_decision_id=policy_decision_id,
        metadata=metadata,
    )
    issues = list(validate_scheduler_sql_capability_attachment(bootstrap_payload))
    if execute and not policy_decision_id:
        issues.append("execute requires policy_decision_id")
    if execute and store is None:
        issues.append("execute requires an existing SQLContextStore object")
    if not text.strip():
        issues.append("text must not be empty")

    if issues:
        return SchedulerManagedSqlContextStoreUsageResult(
            valid=False,
            issues=tuple(issues),
            request=request,
            execute=execute,
            dry_run=not execute,
        )

    if not execute:
        return SchedulerManagedSqlContextStoreUsageResult(
            valid=True,
            issues=(),
            request=request,
            execute=False,
            dry_run=True,
        )

    assert store is not None
    store_result = _call_existing_store(store, request.to_payload())
    sql_ref = _extract_sql_ref(store_result)
    if not sql_ref:
        return SchedulerManagedSqlContextStoreUsageResult(
            valid=False,
            issues=("existing SQLContextStore result must expose sql_ref/record_ref/record_id/id",),
            request=request,
            execute=True,
            dry_run=False,
            store_result=store_result,
        )

    return SchedulerManagedSqlContextStoreUsageResult(
        valid=True,
        issues=(),
        request=request,
        execute=True,
        dry_run=False,
        sql_ref=sql_ref,
        store_result=store_result,
    )


def load_bootstrap_attachment_payload(path: Path) -> dict[str, Any]:
    """Load the 0258 Scheduler bootstrap attachment report."""

    return json.loads(path.read_text(encoding="utf-8"))


def write_scheduler_managed_sql_context_store_usage_report(
    output: Path,
    bootstrap_payload: Mapping[str, Any],
    *,
    text: str,
    execute: bool = False,
    policy_decision_id: str = "",
) -> dict[str, Any]:
    """Write a dry-run report for Scheduler-managed SQL usage.

    This report does not execute SQL because no existing store object is passed
    through the CLI smoke helper.
    """

    result = run_scheduler_managed_sql_context_store_usage(
        bootstrap_payload,
        text=text,
        execute=execute,
        policy_decision_id=policy_decision_id,
        store=None,
    )
    payload = result.to_dict()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
