"""SQL context hydration boundary for 0117.

SQLContextHydrator converts sql:* refs into lightweight hydrated context
fragments. SQLContextStore remains durable context authority. The hydrator
only consumes an injected store interface and produces immutable fragments;
it does not import PostgreSQL, Qdrant, OpenVINO, LLM runtimes, sockets, or
Scheduler internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from context.sql_context_store import (
    SqlContextQuery,
    SqlContextRecord,
    SqlContextStoreSnapshot,
    allowed_sql_context_kinds,
)

_ALLOWED_KINDS = frozenset(allowed_sql_context_kinds())
_FRAGMENT_SCHEMA = "missipy.sql_context_hydrator.fragment.v1"
_BUNDLE_SCHEMA = "missipy.sql_context_hydrator.bundle.v1"


class SqlContextReadableStore(Protocol):
    """Read-only subset required by the SQL hydrator."""

    def get_record(self, context_ref: str) -> SqlContextRecord | None: ...

    def list_records(self, query: SqlContextQuery | None = None) -> SqlContextStoreSnapshot: ...


@dataclass(frozen=True, slots=True)
class SqlContextHydrationPolicy:
    """Bounded deterministic hydration policy."""

    max_records: int = 64
    max_body_chars: int = 8_192
    max_children_per_parent: int = 16

    def __post_init__(self) -> None:
        if self.max_records <= 0:
            raise ValueError("max_records must be > 0")
        if self.max_body_chars <= 0:
            raise ValueError("max_body_chars must be > 0")
        if self.max_children_per_parent <= 0:
            raise ValueError("max_children_per_parent must be > 0")


@dataclass(frozen=True, slots=True)
class SqlContextHydrationRequest:
    """Request to hydrate SQL context refs into lightweight fragments."""

    context_refs: tuple[str, ...]
    include_children: bool = False
    child_kinds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        refs = _normalize_refs(self.context_refs)
        if not refs:
            raise ValueError("context_refs must not be empty")
        object.__setattr__(self, "context_refs", refs)
        object.__setattr__(self, "child_kinds", _normalize_kinds(self.child_kinds))


@dataclass(frozen=True, slots=True)
class HydratedSqlContextFragment:
    """Lightweight fragment hydrated from SQL authority."""

    context_ref: str
    kind: str
    title: str
    body: str
    parent_ref: str | None = None
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    relation: str = "requested"
    truncated: bool = False

    def __post_init__(self) -> None:
        _require_sql_ref(self.context_ref)
        _require_kind(self.kind)
        _require_non_empty("title", self.title)
        _require_non_empty("body", self.body)
        if self.parent_ref is not None:
            _require_typed_ref("parent_ref", self.parent_ref)
        if self.relation not in {"requested", "child"}:
            raise ValueError("relation must be requested or child")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def projection_ref(self) -> str:
        """Stable ref that later projection adapters may use without authority."""

        return f"ctx-fragment:{self.context_ref}"

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _FRAGMENT_SCHEMA,
            "context_ref": self.context_ref,
            "projection_ref": self.projection_ref,
            "kind": self.kind,
            "title": self.title,
            "body": self.body,
            "parent_ref": self.parent_ref,
            "metadata": dict(self.metadata),
            "relation": self.relation,
            "truncated": self.truncated,
        }


@dataclass(frozen=True, slots=True)
class SqlHydratedContextBundle:
    """Deterministic hydration result for specialist/context adapters."""

    fragments: tuple[HydratedSqlContextFragment, ...]
    missing_context_refs: tuple[str, ...] = ()
    capped: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "fragments", tuple(self.fragments))
        object.__setattr__(self, "missing_context_refs", _normalize_refs(self.missing_context_refs, allow_empty=True))

    @property
    def fragment_count(self) -> int:
        return len(self.fragments)

    @property
    def context_refs(self) -> tuple[str, ...]:
        return tuple(fragment.context_ref for fragment in self.fragments)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _BUNDLE_SCHEMA,
            "fragment_count": self.fragment_count,
            "context_refs": list(self.context_refs),
            "missing_context_refs": list(self.missing_context_refs),
            "capped": self.capped,
            "fragments": [fragment.to_mapping() for fragment in self.fragments],
        }


class SQLContextHydrator:
    """Hydrate sql:* refs from an injected SQLContextStore read boundary."""

    def __init__(
        self,
        store: SqlContextReadableStore,
        policy: SqlContextHydrationPolicy | None = None,
    ) -> None:
        self._store = store
        self._policy = policy or SqlContextHydrationPolicy()

    @property
    def policy(self) -> SqlContextHydrationPolicy:
        return self._policy

    def hydrate(self, request: SqlContextHydrationRequest) -> SqlHydratedContextBundle:
        fragments: list[HydratedSqlContextFragment] = []
        missing: list[str] = []
        seen: set[str] = set()
        capped = False

        for ref in request.context_refs:
            record = self._store.get_record(ref)
            if record is None:
                missing.append(ref)
                continue
            capped = self._append_fragment(fragments, seen, record, "requested") or capped
            if capped:
                break
            if request.include_children:
                capped = self._append_children(fragments, seen, record.context_ref, request.child_kinds) or capped
                if capped:
                    break

        return SqlHydratedContextBundle(
            fragments=tuple(fragments),
            missing_context_refs=tuple(missing),
            capped=capped,
        )

    def _append_children(
        self,
        fragments: list[HydratedSqlContextFragment],
        seen: set[str],
        parent_ref: str,
        child_kinds: tuple[str, ...],
    ) -> bool:
        if child_kinds:
            snapshots = tuple(
                self._store.list_records(
                    SqlContextQuery(
                        kind=kind,
                        parent_ref=parent_ref,
                        limit=self._policy.max_children_per_parent,
                    )
                )
                for kind in child_kinds
            )
        else:
            snapshots = (
                self._store.list_records(
                    SqlContextQuery(
                        parent_ref=parent_ref,
                        limit=self._policy.max_children_per_parent,
                    )
                ),
            )
        capped = False
        for snapshot in snapshots:
            for record in snapshot.records:
                capped = self._append_fragment(fragments, seen, record, "child") or capped
                if capped:
                    return True
        return capped

    def _append_fragment(
        self,
        fragments: list[HydratedSqlContextFragment],
        seen: set[str],
        record: SqlContextRecord,
        relation: str,
    ) -> bool:
        if record.context_ref in seen:
            return False
        if len(fragments) >= self._policy.max_records:
            return True
        fragments.append(fragment_from_sql_record(record, self._policy, relation=relation))
        seen.add(record.context_ref)
        return len(fragments) >= self._policy.max_records


def fragment_from_sql_record(
    record: SqlContextRecord,
    policy: SqlContextHydrationPolicy | None = None,
    *,
    relation: str = "requested",
) -> HydratedSqlContextFragment:
    """Convert a durable SQL record into a bounded hydration fragment."""

    effective = policy or SqlContextHydrationPolicy()
    body, truncated = _truncate(record.body, effective.max_body_chars)
    return HydratedSqlContextFragment(
        context_ref=record.context_ref,
        kind=record.kind,
        title=record.title,
        body=body,
        parent_ref=record.parent_ref,
        metadata=record.metadata,
        relation=relation,
        truncated=truncated,
    )


def build_sql_context_hydration_request(
    *context_refs: str,
    include_children: bool = False,
    child_kinds: tuple[str, ...] = (),
) -> SqlContextHydrationRequest:
    """Convenience builder for a deterministic hydration request."""

    return SqlContextHydrationRequest(
        context_refs=tuple(context_refs),
        include_children=include_children,
        child_kinds=child_kinds,
    )


def _truncate(value: str, max_chars: int) -> tuple[str, bool]:
    if len(value) <= max_chars:
        return value, False
    return value[:max_chars], True


def _normalize_refs(values: tuple[str, ...], *, allow_empty: bool = False) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        _require_sql_ref(value)
        if value not in seen:
            normalized.append(value)
            seen.add(value)
    if not allow_empty and not normalized:
        raise ValueError("context_refs must not be empty")
    return tuple(normalized)


def _normalize_kinds(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        _require_kind(value)
        if value not in seen:
            normalized.append(value)
            seen.add(value)
    return tuple(normalized)


def _normalize_metadata(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    seen: set[str] = set()
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        if key in seen:
            raise ValueError("metadata keys must be unique")
        seen.add(key)
        normalized.append((key, value))
    return tuple(sorted(normalized))


def _require_sql_ref(value: str) -> None:
    _require_typed_ref("context_ref", value)
    if not value.startswith("sql:"):
        raise ValueError("context_ref must start with sql:")


def _require_typed_ref(name: str, value: str) -> None:
    _require_non_empty(name, value)
    if ":" not in value or value.split(":", 1)[0] == "":
        raise ValueError(f"{name} must be a typed reference")


def _require_kind(value: str) -> None:
    if value not in _ALLOWED_KINDS:
        raise ValueError("kind must be an allowed SQL context kind")


def _require_non_empty(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must not be empty")
