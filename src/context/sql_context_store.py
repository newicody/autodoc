"""Minimal SQL context store boundary.

0116 introduces SQLContextStore as the durable context authority boundary.  The
module owns only a tiny DB-API persistence contract: it can initialize a schema,
upsert reference-only context records, and read them back deterministically.  It
is not a Scheduler component and it does not import Qdrant, OpenVINO, GitHub,
LLM runtimes, sockets, or PostgreSQL drivers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import sqlite3
from pathlib import Path
import re
from typing import Protocol, Sequence

_SCHEMA_VERSION = "missipy.sql_context_store.v1"
_ALLOWED_PARAMSTYLES = frozenset({"qmark", "format"})
_ALLOWED_KINDS = frozenset(
    {
        "source",
        "document",
        "chunk",
        "fact",
        "artifact",
        "objective",
        "axis",
        "trajectory",
        "inference_context",
        "specialist_output",
        "feedback",
        "github_artifact",
    }
)
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")


class _Cursor(Protocol):
    def execute(self, sql: str, parameters: Sequence[object] = ()) -> object: ...

    def fetchone(self) -> Sequence[object] | None: ...

    def fetchall(self) -> Sequence[Sequence[object]]: ...

    def close(self) -> object: ...


class _Connection(Protocol):
    def cursor(self) -> _Cursor: ...

    def commit(self) -> object: ...

    def close(self) -> object: ...


@dataclass(frozen=True, slots=True)
class SqlContextStorePolicy:
    """Execution policy for an injected DB-API SQL context store."""

    paramstyle: str = "qmark"
    auto_commit: bool = True

    def __post_init__(self) -> None:
        if self.paramstyle not in _ALLOWED_PARAMSTYLES:
            raise ValueError("paramstyle must be qmark or format")


@dataclass(frozen=True, slots=True)
class SqlContextRecord:
    """Small durable context record stored by typed reference.

    Heavy payloads stay outside Scheduler events.  The SQL store persists text,
    metadata, and parent references so later Qdrant/OpenVINO/specialist adapters
    can project or hydrate without becoming the source of authority.
    """

    context_ref: str
    kind: str
    title: str
    body: str
    parent_ref: str | None = None
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("context_ref", self.context_ref, required_prefix="sql:")
        if self.kind not in _ALLOWED_KINDS:
            raise ValueError("kind must be an allowed SQL context kind")
        _require_non_empty("title", self.title)
        _require_non_empty("body", self.body)
        if self.parent_ref is not None:
            _require_typed_ref("parent_ref", self.parent_ref)
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _SCHEMA_VERSION,
            "context_ref": self.context_ref,
            "kind": self.kind,
            "title": self.title,
            "body": self.body,
            "parent_ref": self.parent_ref,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class SqlContextQuery:
    """Deterministic query for context records."""

    kind: str | None = None
    parent_ref: str | None = None
    limit: int = 100

    def __post_init__(self) -> None:
        if self.kind is not None and self.kind not in _ALLOWED_KINDS:
            raise ValueError("kind must be an allowed SQL context kind")
        if self.parent_ref is not None:
            _require_typed_ref("parent_ref", self.parent_ref)
        if self.limit <= 0:
            raise ValueError("limit must be > 0")


@dataclass(frozen=True, slots=True)
class SqlContextStoreWriteResult:
    """Stable result for a SQL context upsert."""

    record: SqlContextRecord
    inserted: bool
    replaced: bool

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": "missipy.sql_context_store.write.v1",
            "context_ref": self.record.context_ref,
            "inserted": self.inserted,
            "replaced": self.replaced,
            "record": self.record.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class SqlContextStoreSnapshot:
    """Serializable snapshot of records returned by the SQL store boundary."""

    records: tuple[SqlContextRecord, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", tuple(self.records))

    @property
    def record_count(self) -> int:
        return len(self.records)

    @property
    def context_refs(self) -> tuple[str, ...]:
        return tuple(record.context_ref for record in self.records)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": "missipy.sql_context_store.snapshot.v1",
            "record_count": self.record_count,
            "context_refs": list(self.context_refs),
            "records": [record.to_mapping() for record in self.records],
        }


class DbApiSqlContextStore:
    """Minimal DB-API SQLContextStore over an injected connection.

    SQLite tests use qmark parameters.  A production caller may inject a
    PostgreSQL DB-API connection with format parameters from outside this module;
    no PostgreSQL package is imported here.
    """

    def __init__(
        self,
        connection: _Connection,
        policy: SqlContextStorePolicy | None = None,
    ) -> None:
        self._connection = connection
        self._policy = policy or SqlContextStorePolicy()

    @property
    def policy(self) -> SqlContextStorePolicy:
        return self._policy

    def initialize_schema(self) -> None:
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS sql_context_records (
                context_ref TEXT PRIMARY KEY,
                schema_version TEXT NOT NULL,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                parent_ref TEXT,
                metadata_json TEXT NOT NULL
            )
            """,
        )
        self._execute(
            "CREATE INDEX IF NOT EXISTS idx_sql_context_records_kind "
            "ON sql_context_records(kind)"
        )
        self._execute(
            "CREATE INDEX IF NOT EXISTS idx_sql_context_records_parent "
            "ON sql_context_records(parent_ref)"
        )
        self._commit_if_needed()

    def upsert_record(self, record: SqlContextRecord) -> SqlContextStoreWriteResult:
        existing = self.get_record(record.context_ref)
        p = self._placeholder
        self._execute(
            """
            INSERT INTO sql_context_records (
                context_ref,
                schema_version,
                kind,
                title,
                body,
                parent_ref,
                metadata_json
            ) VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p})
            ON CONFLICT(context_ref) DO UPDATE SET
                schema_version = excluded.schema_version,
                kind = excluded.kind,
                title = excluded.title,
                body = excluded.body,
                parent_ref = excluded.parent_ref,
                metadata_json = excluded.metadata_json
            """.format(p=p),
            (
                record.context_ref,
                _SCHEMA_VERSION,
                record.kind,
                record.title,
                record.body,
                record.parent_ref,
                _metadata_json(record.metadata),
            ),
        )
        self._commit_if_needed()
        return SqlContextStoreWriteResult(
            record=record,
            inserted=existing is None,
            replaced=existing is not None,
        )

    def get_record(self, context_ref: str) -> SqlContextRecord | None:
        _require_typed_ref("context_ref", context_ref, required_prefix="sql:")
        p = self._placeholder
        row = self._fetchone(
            """
            SELECT context_ref, kind, title, body, parent_ref, metadata_json
            FROM sql_context_records
            WHERE context_ref = {p}
            """.format(p=p),
            (context_ref,),
        )
        if row is None:
            return None
        return _record_from_row(row)

    def list_records(self, query: SqlContextQuery | None = None) -> SqlContextStoreSnapshot:
        effective = query or SqlContextQuery()
        clauses: list[str] = []
        params: list[object] = []
        p = self._placeholder
        if effective.kind is not None:
            clauses.append(f"kind = {p}")
            params.append(effective.kind)
        if effective.parent_ref is not None:
            clauses.append(f"parent_ref = {p}")
            params.append(effective.parent_ref)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(effective.limit)
        rows = self._fetchall(
            """
            SELECT context_ref, kind, title, body, parent_ref, metadata_json
            FROM sql_context_records{where}
            ORDER BY context_ref
            LIMIT {p}
            """.format(where=where, p=p),
            tuple(params),
        )
        return SqlContextStoreSnapshot(records=tuple(_record_from_row(row) for row in rows))

    def close(self) -> None:
        self._connection.close()

    @property
    def _placeholder(self) -> str:
        return "?" if self._policy.paramstyle == "qmark" else "%s"

    def _execute(self, sql: str, parameters: Sequence[object] = ()) -> None:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
        finally:
            cursor.close()

    def _fetchone(self, sql: str, parameters: Sequence[object]) -> Sequence[object] | None:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
            return cursor.fetchone()
        finally:
            cursor.close()

    def _fetchall(self, sql: str, parameters: Sequence[object]) -> Sequence[Sequence[object]]:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
            return cursor.fetchall()
        finally:
            cursor.close()

    def _commit_if_needed(self) -> None:
        if self._policy.auto_commit:
            self._connection.commit()


class SQLiteSqlContextStore(DbApiSqlContextStore):
    """SQLite convenience store for tests and local dry runs."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = path
        connection = sqlite3.connect(str(path))
        super().__init__(connection, SqlContextStorePolicy(paramstyle="qmark"))


@dataclass(frozen=True, slots=True)
class PostgresSqlContextStoreTarget:
    """Documented production target for injected PostgreSQL connections."""

    dsn: str = "dbname=autodoc user=autodoc host=127.0.0.1 port=5432"
    data_directory: str = "/srv/autodoc/postgres/data"
    active_pool: str = "fast_pool"
    backup_pool: str = "data_pool"

    def __post_init__(self) -> None:
        _require_non_empty("dsn", self.dsn)
        _require_non_empty("data_directory", self.data_directory)
        _require_non_empty("active_pool", self.active_pool)
        _require_non_empty("backup_pool", self.backup_pool)

    def to_mapping(self) -> dict[str, str]:
        return {
            "dsn": self.dsn,
            "data_directory": self.data_directory,
            "active_pool": self.active_pool,
            "backup_pool": self.backup_pool,
            "driver_import": "external",
        }


def build_sql_context_ref(kind: str, identity: str, *, prefix: str = "sql") -> str:
    """Build a deterministic typed SQL context reference."""

    if kind not in _ALLOWED_KINDS:
        raise ValueError("kind must be an allowed SQL context kind")
    _require_non_empty("identity", identity)
    _require_non_empty("prefix", prefix)
    digest = hashlib.sha256()
    digest.update(kind.encode("utf-8"))
    digest.update(b"\0")
    digest.update(identity.strip().encode("utf-8"))
    return f"{prefix}:{kind}:{digest.hexdigest()[:16]}"


def build_sql_context_record(
    *,
    kind: str,
    identity: str,
    title: str,
    body: str,
    parent_ref: str | None = None,
    metadata: tuple[tuple[str, str], ...] = (),
) -> SqlContextRecord:
    """Build a stable SqlContextRecord from local inputs."""

    return SqlContextRecord(
        context_ref=build_sql_context_ref(kind, identity),
        kind=kind,
        title=title,
        body=body,
        parent_ref=parent_ref,
        metadata=metadata,
    )


def allowed_sql_context_kinds() -> tuple[str, ...]:
    return tuple(sorted(_ALLOWED_KINDS))


def _record_from_row(row: Sequence[object]) -> SqlContextRecord:
    context_ref, kind, title, body, parent_ref, metadata_json = row
    return SqlContextRecord(
        context_ref=_as_str(context_ref, "context_ref"),
        kind=_as_str(kind, "kind"),
        title=_as_str(title, "title"),
        body=_as_str(body, "body"),
        parent_ref=None if parent_ref is None else _as_str(parent_ref, "parent_ref"),
        metadata=_metadata_from_json(_as_str(metadata_json, "metadata_json")),
    )


def _metadata_json(metadata: tuple[tuple[str, str], ...]) -> str:
    return json.dumps(dict(metadata), ensure_ascii=False, sort_keys=True)


def _metadata_from_json(payload: str) -> tuple[tuple[str, str], ...]:
    raw = json.loads(payload)
    if not isinstance(raw, dict):
        raise ValueError("metadata_json must decode to an object")
    return _normalize_metadata(tuple((str(key), str(value)) for key, value in raw.items()))


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


def _require_typed_ref(name: str, value: str, *, required_prefix: str | None = None) -> None:
    _require_non_empty(name, value)
    if required_prefix is not None and not value.startswith(required_prefix):
        raise ValueError(f"{name} must start with {required_prefix}")
    if not _TYPED_REF_RE.match(value):
        raise ValueError(f"{name} must be a typed reference")


def _require_non_empty(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _as_str(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    return value
