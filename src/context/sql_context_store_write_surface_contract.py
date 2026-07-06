"""Pure SQLContextStore write-surface audit contracts.

0150 inspects the existing SQLContextStore source after the 0149 persistence
record smoke.  It deliberately does not import backend-specific SQL clients,
does not call OpenVINO or Qdrant, and does not create a SQL worker.  Its job is
to decide whether a later patch can perform a controlled write through an
explicit existing SQLContextStore method.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

_DEFAULT_CANDIDATE_WRITE_METHODS = (
    "persist_context_record",
    "persist_context",
    "upsert_context",
    "save_context",
    "write_context",
    "store_context",
    "put_context",
    "record_context",
    "create_context",
)

_WRITE_STATUS_READY = "ready_for_controlled_write_patch"
_WRITE_STATUS_BLOCKED = "blocked_no_explicit_sql_context_store_write_method"


def _require_non_empty(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_prefix(value: str, *, field_name: str, prefix: str) -> str:
    value = _require_non_empty(value, field_name=field_name)
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must start with {prefix!r}: {value!r}")
    return value


@dataclass(frozen=True, slots=True)
class SqlContextStoreMethodSignature:
    """A source-level method found on the SQLContextStore class."""

    name: str
    args: tuple[str, ...]
    has_varargs: bool
    has_kwargs: bool
    line_number: int

    def __post_init__(self) -> None:
        _require_non_empty(self.name, field_name="name")
        if self.line_number <= 0:
            raise ValueError("line_number must be positive")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "args": list(self.args),
            "has_varargs": self.has_varargs,
            "has_kwargs": self.has_kwargs,
            "line_number": self.line_number,
        }


@dataclass(frozen=True, slots=True)
class SqlContextStoreWriteSurfaceAudit:
    """Serializable audit for the existing SQLContextStore write surface."""

    sql_context_store_path: str
    exists: bool
    has_sql_context_store_class: bool
    method_signatures: tuple[SqlContextStoreMethodSignature, ...]
    candidate_write_methods: tuple[str, ...]
    selected_write_method: str | None
    requested_write_method: str | None = None
    write_status: str = _WRITE_STATUS_BLOCKED
    recommended_next_patch: str = "0151-sql_context_store_explicit_write_method"
    gap_reason: str = "no explicit SQLContextStore write method found"
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty(self.sql_context_store_path, field_name="sql_context_store_path")
        if self.selected_write_method is not None:
            _require_non_empty(self.selected_write_method, field_name="selected_write_method")
        if self.requested_write_method is not None:
            _require_non_empty(self.requested_write_method, field_name="requested_write_method")
        if self.write_status not in {_WRITE_STATUS_READY, _WRITE_STATUS_BLOCKED}:
            raise ValueError("unexpected write_status")
        _require_non_empty(self.recommended_next_patch, field_name="recommended_next_patch")
        _require_non_empty(self.gap_reason, field_name="gap_reason")

    @property
    def ready_for_controlled_write_patch(self) -> bool:
        return self.selected_write_method is not None

    def to_mapping(self) -> dict[str, Any]:
        return {
            "sql_context_store_path": self.sql_context_store_path,
            "exists": self.exists,
            "has_sql_context_store_class": self.has_sql_context_store_class,
            "method_signatures": [signature.to_mapping() for signature in self.method_signatures],
            "candidate_write_methods": list(self.candidate_write_methods),
            "selected_write_method": self.selected_write_method,
            "requested_write_method": self.requested_write_method,
            "ready_for_controlled_write_patch": self.ready_for_controlled_write_patch,
            "write_status": self.write_status,
            "recommended_next_patch": self.recommended_next_patch,
            "gap_reason": self.gap_reason,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True, slots=True)
class SqlContextStoreWriteSurfaceRecord:
    """Audit record tying a 0149 persistence record to SQLContextStore surface."""

    audit_ref: str
    persistence_ref: str
    sql_ref: str
    artifact_ref: str
    handoff_ref: str
    surface_audit: SqlContextStoreWriteSurfaceAudit
    persistence_mode: str = "sql_context_store_write_surface_audit"
    durable_authority: str = "sql"
    qdrant_role: str = "projection_recall_index"
    write_attempted: bool = False

    def __post_init__(self) -> None:
        _require_prefix(self.audit_ref, field_name="audit_ref", prefix="sql-context-write-surface:")
        _require_prefix(self.persistence_ref, field_name="persistence_ref", prefix="sql-context-persist:")
        _require_prefix(self.sql_ref, field_name="sql_ref", prefix="sql:")
        _require_prefix(self.artifact_ref, field_name="artifact_ref", prefix="artifact:")
        _require_prefix(self.handoff_ref, field_name="handoff_ref", prefix="sql-handoff:")
        if self.persistence_mode != "sql_context_store_write_surface_audit":
            raise ValueError("unexpected persistence_mode")
        if self.durable_authority != "sql":
            raise ValueError("SQL must remain durable authority")
        if self.qdrant_role != "projection_recall_index":
            raise ValueError("Qdrant must remain projection/recall only")
        if self.write_attempted:
            raise ValueError("0150 is audit-only and must not attempt a backend write")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "audit_ref": self.audit_ref,
            "persistence_ref": self.persistence_ref,
            "sql_ref": self.sql_ref,
            "artifact_ref": self.artifact_ref,
            "handoff_ref": self.handoff_ref,
            "surface_audit": self.surface_audit.to_mapping(),
            "persistence_mode": self.persistence_mode,
            "durable_authority": self.durable_authority,
            "qdrant_role": self.qdrant_role,
            "write_attempted": self.write_attempted,
            "write_status": self.surface_audit.write_status,
            "selected_write_method": self.surface_audit.selected_write_method,
            "recommended_next_patch": self.surface_audit.recommended_next_patch,
        }


def default_write_surface_audit_ref(*, persistence_ref: str, sql_ref: str) -> str:
    raw = f"{persistence_ref}/write-surface/{sql_ref}"
    safe = "".join(ch if ch.isalnum() else "-" for ch in raw).strip("-").lower()
    while "--" in safe:
        safe = safe.replace("--", "-")
    return f"sql-context-write-surface:{safe}"


def inspect_sql_context_store_write_surface(
    root: str | Path,
    *,
    requested_write_method: str | None = None,
    candidate_write_methods: Sequence[str] = _DEFAULT_CANDIDATE_WRITE_METHODS,
) -> SqlContextStoreWriteSurfaceAudit:
    """Inspect SQLContextStore source through AST without importing any backend."""

    path = Path(root) / "src" / "context" / "sql_context_store.py"
    if not path.exists():
        return SqlContextStoreWriteSurfaceAudit(
            sql_context_store_path=str(path),
            exists=False,
            has_sql_context_store_class=False,
            method_signatures=(),
            candidate_write_methods=(),
            selected_write_method=None,
            requested_write_method=requested_write_method,
            write_status=_WRITE_STATUS_BLOCKED,
            gap_reason="src/context/sql_context_store.py is missing",
            payload={"candidate_write_methods_checked": list(candidate_write_methods)},
        )

    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return SqlContextStoreWriteSurfaceAudit(
            sql_context_store_path=str(path),
            exists=True,
            has_sql_context_store_class="SQLContextStore" in source,
            method_signatures=(),
            candidate_write_methods=(),
            selected_write_method=None,
            requested_write_method=requested_write_method,
            write_status=_WRITE_STATUS_BLOCKED,
            gap_reason=f"SQLContextStore source is not parseable: {exc.msg}",
            payload={"candidate_write_methods_checked": list(candidate_write_methods)},
        )

    sql_store_classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "SQLContextStore"]
    if not sql_store_classes:
        return SqlContextStoreWriteSurfaceAudit(
            sql_context_store_path=str(path),
            exists=True,
            has_sql_context_store_class=False,
            method_signatures=(),
            candidate_write_methods=(),
            selected_write_method=None,
            requested_write_method=requested_write_method,
            write_status=_WRITE_STATUS_BLOCKED,
            gap_reason="SQLContextStore class not found",
            payload={"candidate_write_methods_checked": list(candidate_write_methods)},
        )

    signatures = tuple(_method_signature(node) for node in _class_methods(sql_store_classes[0]))
    method_names = {signature.name for signature in signatures}
    candidates = tuple(method for method in candidate_write_methods if method in method_names)
    selected = _select_write_method(
        candidates=candidates,
        method_names=method_names,
        requested_write_method=requested_write_method,
    )
    if selected is None:
        gap_reason = "no explicit SQLContextStore write method found"
        write_status = _WRITE_STATUS_BLOCKED
    elif requested_write_method and selected != requested_write_method:
        gap_reason = f"requested write method {requested_write_method!r} was not found"
        selected = None
        write_status = _WRITE_STATUS_BLOCKED
    else:
        gap_reason = "explicit SQLContextStore write method is present; next patch may bind it"
        write_status = _WRITE_STATUS_READY

    return SqlContextStoreWriteSurfaceAudit(
        sql_context_store_path=str(path),
        exists=True,
        has_sql_context_store_class=True,
        method_signatures=signatures,
        candidate_write_methods=candidates,
        selected_write_method=selected,
        requested_write_method=requested_write_method,
        write_status=write_status,
        gap_reason=gap_reason,
        payload={
            "candidate_write_methods_checked": list(candidate_write_methods),
            "all_method_names": sorted(method_names),
            "audit_only": True,
        },
    )


def build_sql_context_store_write_surface_record(
    *,
    persistence_record: Mapping[str, Any],
    surface_audit: SqlContextStoreWriteSurfaceAudit,
    audit_ref: str | None = None,
) -> SqlContextStoreWriteSurfaceRecord:
    persistence_ref = str(persistence_record.get("persistence_ref"))
    sql_ref = str(persistence_record.get("sql_ref"))
    audit_ref = audit_ref or default_write_surface_audit_ref(
        persistence_ref=persistence_ref,
        sql_ref=sql_ref,
    )
    return SqlContextStoreWriteSurfaceRecord(
        audit_ref=audit_ref,
        persistence_ref=persistence_ref,
        sql_ref=sql_ref,
        artifact_ref=str(persistence_record.get("artifact_ref")),
        handoff_ref=str(persistence_record.get("handoff_ref")),
        surface_audit=surface_audit,
    )


def read_json_mapping(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"expected JSON object in {path}")
    return loaded


def _class_methods(class_node: ast.ClassDef) -> Iterable[ast.FunctionDef | ast.AsyncFunctionDef]:
    for node in class_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def _method_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> SqlContextStoreMethodSignature:
    args = tuple(arg.arg for arg in node.args.args)
    return SqlContextStoreMethodSignature(
        name=node.name,
        args=args,
        has_varargs=node.args.vararg is not None,
        has_kwargs=node.args.kwarg is not None,
        line_number=int(getattr(node, "lineno", 1)),
    )


def _select_write_method(
    *,
    candidates: Sequence[str],
    method_names: set[str],
    requested_write_method: str | None,
) -> str | None:
    if requested_write_method:
        return requested_write_method if requested_write_method in method_names else None
    return candidates[0] if candidates else None
