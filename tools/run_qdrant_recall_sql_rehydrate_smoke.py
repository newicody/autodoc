#!/usr/bin/env python3
"""Qdrant recall payload to SQLContextStore rehydrate smoke.

0159 consumes an existing Qdrant-style recall payload, extracts sql_ref values,
then rehydrates records from the existing DbApiSqlContextStore.get_record path.

Boundary: Qdrant remains projection/recall metadata; SQL remains durable authority.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any, Iterable, Mapping, Sequence

DEFAULT_OUTPUT_DIR = ".var/smoke/artifacts/0159"
DEFAULT_RECALL_JSON = ".var/smoke/artifacts/0158/p1_closed_loop_operator_result.json"
DEFAULT_DB_PATH = ".var/local/sql_context_store.sqlite3"
DEFAULT_QUERY_TEXT = "query: P1 closed loop artifact vector indexing SQL persistence"
_SQL_CONTEXT_DB_ENV = "AUTODOC_SQL_CONTEXT_DB"

_REUSED_SURFACES = (
    "src/inference/qdrant_projection_adapter.py",
    "src/context/sql_context_store.py",
    "src/context/sql_context_hydrator.py",
    "DbApiSqlContextStore.get_record",
    "unique_sql_context_refs_from_recall",
)

_FORBIDDEN_PARALLEL_SURFACES = (
    "SQLPersistenceWorker",
    "SQLOrchestrator",
    "LocalArtifactOrchestrator",
    "LocalVectorIndexingOrchestrator",
    "SchedulerOpenVINORunner",
    "VectorOpenVINOEmbeddingAdapter",
    "VectorQdrantProjectionAdapter",
    "QdrantRecallOrchestrator",
)

@dataclass(frozen=True, slots=True)
class RecallSqlRehydrateSurface:
    key: str
    path: Path
    reason: str
    required: bool = True
    def to_mapping(self, *, root: Path) -> dict[str, Any]:
        return {"key": self.key, "status": "present" if self.path.exists() else "missing", "path": _display_path(self.path, root=root), "reason": self.reason, "required": self.required}

@dataclass(frozen=True, slots=True)
class RecallSqlRehydratePlan:
    repository_root: Path
    recall_json: Path
    output_dir: Path
    report_json: Path
    report_md: Path
    db_path: Path
    db_path_source: str
    query_text: str
    execute: bool
    surfaces: tuple[RecallSqlRehydrateSurface, ...]
    @property
    def ready(self) -> bool:
        return all(s.path.exists() for s in self.surfaces if s.required)
    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository_root": str(self.repository_root),
            "recall_json": str(self.recall_json),
            "output_dir": str(self.output_dir),
            "report_json": str(self.report_json),
            "report_md": str(self.report_md),
            "db_path": str(self.db_path),
            "db_path_source": self.db_path_source,
            "query_text": self.query_text,
            "execute": self.execute,
            "ready_for_qdrant_recall_sql_rehydrate": self.ready,
            "surfaces": [s.to_mapping(root=self.repository_root) for s in self.surfaces],
            "boundary": [
                "consumes a Qdrant-style recall payload or previous P1 result artifact",
                "extracts sql_ref values via existing qdrant_projection_adapter helper when compatible",
                "falls back to read-only sql_ref extraction from payload mappings",
                "rehydrates through existing DbApiSqlContextStore.get_record",
                "does not create SQLPersistenceWorker",
                "does not create SQLOrchestrator",
                "does not create LocalArtifactOrchestrator",
                "does not create LocalVectorIndexingOrchestrator",
                "does not create SchedulerOpenVINORunner",
                "does not create VectorOpenVINOEmbeddingAdapter",
                "does not create VectorQdrantProjectionAdapter",
                "does not create QdrantRecallOrchestrator",
                "SQL remains durable authority",
                "Qdrant remains projection/recall metadata",
            ],
        }
    def to_markdown(self) -> str:
        lines = [
            "# Qdrant recall -> SQL rehydrate plan", "",
            f"repository_root: `{self.repository_root}`",
            f"recall_json: `{self.recall_json}`",
            f"output_dir: `{self.output_dir}`",
            f"report_json: `{self.report_json}`",
            f"report_md: `{self.report_md}`",
            f"db_path: `{self.db_path}`",
            f"db_path_source: `{self.db_path_source}`",
            f"query_text: `{self.query_text}`",
            f"ready_for_qdrant_recall_sql_rehydrate: `{str(self.ready).lower()}`",
            f"execute: `{str(self.execute).lower()}`", "",
            "## Existing surfaces", "", "| key | status | required | path | reason |", "| --- | --- | --- | --- | --- |",
        ]
        for s in self.surfaces:
            row = s.to_mapping(root=self.repository_root)
            lines.append(f"| {row['key']} | {row['status']} | `{str(row['required']).lower()}` | `{row['path']}` | {row['reason']} |")
        lines += ["", "## Boundary", "", "- reuses `src/inference/qdrant_projection_adapter.py` helper vocabulary", "- reuses `DbApiSqlContextStore.get_record`", "- SQL remains durable authority", "- Qdrant remains projection/recall metadata", "- no new Qdrant adapter, SQL worker, orchestrator, Scheduler runner, or OpenVINO runner", ""]
        return "\n".join(lines)

@dataclass(frozen=True, slots=True)
class RehydratedSqlRecord:
    sql_ref: str
    found: bool
    title: str | None
    content_preview: str | None
    metadata_keys: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class RecallSqlRehydrateResult:
    report_json: Path
    report_md: Path
    query_text: str
    recall_json: Path
    db_path: Path
    sql_refs: tuple[str, ...]
    hydrated_count: int
    missing_count: int
    records: tuple[RehydratedSqlRecord, ...]
    status: str
    def to_mapping(self) -> dict[str, Any]:
        return {"report_json": str(self.report_json), "report_md": str(self.report_md), "query_text": self.query_text, "recall_json": str(self.recall_json), "db_path": str(self.db_path), "sql_refs": list(self.sql_refs), "hydrated_count": self.hydrated_count, "missing_count": self.missing_count, "records": [asdict(r) for r in self.records], "status": self.status, "boundary": "Qdrant recall payload only provides sql_ref pointers; DbApiSqlContextStore.get_record rehydrates durable SQL records"}
    def to_markdown(self) -> str:
        lines = ["# Qdrant recall -> SQL rehydrate result", "", f"status: `{self.status}`", f"query_text: `{self.query_text}`", f"recall_json: `{self.recall_json}`", f"db_path: `{self.db_path}`", f"sql_ref_count: `{len(self.sql_refs)}`", f"hydrated_count: `{self.hydrated_count}`", f"missing_count: `{self.missing_count}`", "", "## SQL refs", ""]
        for ref in self.sql_refs:
            lines.append(f"- `{ref}`")
        lines += ["", "## Hydrated records", ""]
        for r in self.records:
            lines.append(f"### `{r.sql_ref}`")
            lines.append(f"- found: `{str(r.found).lower()}`")
            if r.title: lines.append(f"- title: `{r.title}`")
            if r.content_preview: lines.append(f"- content_preview: `{r.content_preview}`")
            if r.metadata_keys: lines.append(f"- metadata_keys: `{', '.join(r.metadata_keys)}`")
            lines.append("")
        lines.append("boundary: `SQL remains durable authority; Qdrant remains projection/recall metadata`")
        lines.append("")
        return "\n".join(lines)

def build_qdrant_recall_sql_rehydrate_plan(root: Path, *, recall_json: Path, output_dir: Path, db_path: Path | None, environ: Mapping[str, str] | None = None, query_text: str, execute: bool) -> RecallSqlRehydratePlan:
    root = root.resolve()
    recall_json = _resolve_repo_path(root, recall_json)
    output_dir = _resolve_repo_path(root, output_dir)
    resolved_db_path, db_source = resolve_sql_context_db_path(root, db_path, environ=environ)
    return RecallSqlRehydratePlan(
        repository_root=root,
        recall_json=recall_json,
        output_dir=output_dir,
        report_json=output_dir / "qdrant_recall_sql_rehydrate_result.json",
        report_md=output_dir / "qdrant_recall_sql_rehydrate_report.md",
        db_path=resolved_db_path,
        db_path_source=db_source,
        query_text=_normalize_query_text(query_text),
        execute=execute,
        surfaces=(
            RecallSqlRehydrateSurface("qdrant_projection_adapter", root / "src" / "inference" / "qdrant_projection_adapter.py", "existing Qdrant projection/recall helper surface"),
            RecallSqlRehydrateSurface("sql_context_store", root / "src" / "context" / "sql_context_store.py", "existing durable SQL authority with DbApiSqlContextStore.get_record"),
            RecallSqlRehydrateSurface("sql_context_hydrator", root / "src" / "context" / "sql_context_hydrator.py", "existing SQL rehydration vocabulary", required=False),
            RecallSqlRehydrateSurface("recall_json", recall_json, "Qdrant-style recall payload or P1 result artifact"),
        ),
    )

def execute_qdrant_recall_sql_rehydrate_plan(plan: RecallSqlRehydratePlan) -> int:
    if not plan.ready:
        for s in plan.surfaces:
            if s.required and not s.path.exists(): print(f"missing required surface: {s.path}", file=sys.stderr)
        return 2
    plan.output_dir.mkdir(parents=True, exist_ok=True)
    payload = _read_json_mapping(plan.recall_json)
    sql_refs = extract_sql_refs_from_recall_payload(payload)
    records = rehydrate_sql_refs_from_store(plan.repository_root, plan.db_path, sql_refs)
    hydrated_count = sum(1 for r in records if r.found)
    missing_count = sum(1 for r in records if not r.found)
    status = "ok" if sql_refs and missing_count == 0 else "partial" if sql_refs else "empty"
    result = RecallSqlRehydrateResult(plan.report_json, plan.report_md, plan.query_text, plan.recall_json, plan.db_path, tuple(sql_refs), hydrated_count, missing_count, tuple(records), status)
    plan.report_json.write_text(json.dumps(result.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.report_md.write_text(result.to_markdown(), encoding="utf-8")
    print("==> qdrant_recall_sql_rehydrate")
    print(result.to_markdown(), end="")
    return 0 if status in {"ok", "partial"} else 1

def extract_sql_refs_from_recall_payload(payload: Mapping[str, Any]) -> list[str]:
    refs = _extract_with_existing_qdrant_helper(payload) or list(_walk_sql_refs(payload))
    return _unique_preserving_order(refs)

def _extract_with_existing_qdrant_helper(payload: Mapping[str, Any]) -> list[str]:
    try:
        from inference.qdrant_projection_adapter import unique_sql_context_refs_from_recall  # type: ignore
    except Exception:
        return []
    try:
        refs = unique_sql_context_refs_from_recall(payload)  # type: ignore[arg-type]
    except Exception:
        return []
    return [str(ref) for ref in (refs or []) if str(ref).startswith("sql:")]

def _walk_sql_refs(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if key in {"sql_ref", "context_ref"} and isinstance(nested, str) and nested.startswith("sql:"):
                yield nested
            yield from _walk_sql_refs(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from _walk_sql_refs(nested)

def rehydrate_sql_refs_from_store(root: Path, db_path: Path, sql_refs: Sequence[str]) -> list[RehydratedSqlRecord]:
    _ensure_src_on_path(root)
    from context.sql_context_store import DbApiSqlContextStore  # noqa: WPS433
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path))
    try:
        store = DbApiSqlContextStore(connection)
        if hasattr(store, "initialize_schema"):
            store.initialize_schema()
        return [_record_to_rehydrated(ref, store.get_record(ref)) for ref in sql_refs]
    finally:
        connection.close()

def _record_to_rehydrated(sql_ref: str, record: Any) -> RehydratedSqlRecord:
    if record is None:
        return RehydratedSqlRecord(sql_ref, False, None, None, ())
    title = _first_attr(record, ("title", "artifact_ref", "source_ref", "context_ref"))
    content = _first_attr(record, ("content", "text", "body", "payload"))
    metadata = _first_attr(record, ("metadata", "payload", "extra"))
    keys = tuple(sorted(metadata.keys())) if isinstance(metadata, Mapping) else ()
    return RehydratedSqlRecord(sql_ref, True, str(title) if title is not None else None, _preview_text(content), keys)

def resolve_sql_context_db_path(root: Path, db_path: Path | None, *, environ: Mapping[str, str] | None = None) -> tuple[Path, str]:
    if db_path is not None:
        return _resolve_repo_path(root, db_path), "cli:--db-path"
    env = dict(environ or {})
    if env.get(_SQL_CONTEXT_DB_ENV):
        return _resolve_repo_path(root, Path(env[_SQL_CONTEXT_DB_ENV])), f"env:{_SQL_CONTEXT_DB_ENV}"
    return _resolve_repo_path(root, Path(DEFAULT_DB_PATH)), "default:.var/local/sql_context_store.sqlite3"

def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rehydrate SQL context records from a Qdrant-style recall payload.")
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("--recall-json", type=Path, default=Path(DEFAULT_RECALL_JSON))
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--db-path", type=Path, default=None)
    parser.add_argument("--query-text", default=DEFAULT_QUERY_TEXT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)

def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    plan = build_qdrant_recall_sql_rehydrate_plan(args.repository_root, recall_json=args.recall_json, output_dir=args.output_dir, db_path=args.db_path, environ=None, query_text=args.query_text, execute=args.execute)
    print(json.dumps(plan.to_mapping(), indent=2, sort_keys=True) if args.format == "json" else plan.to_markdown(), end="\n" if args.format == "json" else "")
    if not args.execute:
        return 0 if plan.ready else 2
    return execute_qdrant_recall_sql_rehydrate_plan(plan)

def _read_json_mapping(path: Path) -> Mapping[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping): raise ValueError(f"expected JSON object in {path}")
    return loaded

def _ensure_src_on_path(root: Path) -> None:
    src = str(root / "src")
    if src not in sys.path: sys.path.insert(0, src)

def _resolve_repo_path(root: Path, path: Path) -> Path:
    path = path.expanduser()
    return path if path.is_absolute() else root / path

def _normalize_query_text(text: str) -> str:
    return text if text.startswith("query: ") else f"query: {text}"

def _unique_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set(); result: list[str] = []
    for value in values:
        if value not in seen: seen.add(value); result.append(value)
    return result

def _first_attr(record: Any, names: Sequence[str]) -> Any:
    for name in names:
        if hasattr(record, name): return getattr(record, name)
    if isinstance(record, Mapping):
        for name in names:
            if name in record: return record[name]
    return None

def _preview_text(value: Any, *, limit: int = 220) -> str | None:
    if value is None: return None
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"

def _display_path(path: Path, *, root: Path) -> str:
    try: return str(path.relative_to(root))
    except ValueError: return str(path)

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
