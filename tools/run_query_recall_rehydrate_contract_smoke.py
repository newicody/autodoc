#!/usr/bin/env python3
"""Query -> Qdrant-style recall payload -> SQL rehydrate contract smoke.

0160 locks the user-query boundary before the existing 0159 SQL rehydrate
operator. It does not add a new OpenVINO adapter, Qdrant adapter, SQL worker,
Scheduler runner, or orchestrator.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence


DEFAULT_OUTPUT_DIR = ".var/smoke/artifacts/0160"
DEFAULT_RECALL_JSON = ".var/smoke/artifacts/0158/p1_closed_loop_operator_result.json"
DEFAULT_DB_PATH = ".var/local/sql_context_store.sqlite3"
DEFAULT_QUERY_TEXT = "query: P1 closed loop artifact vector indexing SQL persistence"

_REUSED_SURFACES = (
    "tools/embed_e5.py",
    "tools/run_qdrant_recall_sql_rehydrate_smoke.py",
    "tools/run_qdrant_projection_live_smoke.py",
    "tools/search_e5_corpus.py",
    "src/inference/e5_pipeline.py",
    "src/inference/qdrant_projection_adapter.py",
    "src/context/sql_context_store.py",
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
    "QueryRecallOrchestrator",
)


@dataclass(frozen=True, slots=True)
class QueryRecallSurface:
    key: str
    path: Path
    reason: str
    required: bool = True

    def to_mapping(self, *, root: Path) -> dict[str, Any]:
        return {
            "key": self.key,
            "status": "present" if self.path.exists() else "missing",
            "path": _display_path(self.path, root=root),
            "reason": self.reason,
            "required": self.required,
        }


@dataclass(frozen=True, slots=True)
class QueryRecallContractPlan:
    repository_root: Path
    output_dir: Path
    rehydrate_output_dir: Path
    recall_json: Path
    query_embedding_json: Path | None
    db_path: Path
    query_text: str
    result_json: Path
    result_md: Path
    execute: bool
    surfaces: tuple[QueryRecallSurface, ...]

    @property
    def ready(self) -> bool:
        return all(surface.path.exists() for surface in self.surfaces if surface.required)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository_root": str(self.repository_root),
            "output_dir": str(self.output_dir),
            "rehydrate_output_dir": str(self.rehydrate_output_dir),
            "recall_json": str(self.recall_json),
            "query_embedding_json": str(self.query_embedding_json) if self.query_embedding_json is not None else None,
            "db_path": str(self.db_path),
            "query_text": self.query_text,
            "query_text_role": "query",
            "result_json": str(self.result_json),
            "result_md": str(self.result_md),
            "execute": self.execute,
            "ready_for_query_recall_rehydrate_contract": self.ready,
            "surfaces": [surface.to_mapping(root=self.repository_root) for surface in self.surfaces],
            "commands": {
                "optional_query_embedding": [sys.executable, str(self.repository_root / "tools" / "embed_e5.py"), self.query_text],
                "0159_rehydrate": _rehydrate_command(self),
            },
            "boundary": [
                "normalizes user query to the E5 query role",
                "accepts an existing query embedding artifact when provided",
                "accepts a Qdrant-style recall payload carrying sql_ref pointers",
                "delegates durable rehydrate to existing 0159 tool",
                "does not create SQLPersistenceWorker",
                "does not create SQLOrchestrator",
                "does not create LocalArtifactOrchestrator",
                "does not create LocalVectorIndexingOrchestrator",
                "does not create SchedulerOpenVINORunner",
                "does not create VectorOpenVINOEmbeddingAdapter",
                "does not create VectorQdrantProjectionAdapter",
                "does not create QdrantRecallOrchestrator",
                "does not create QueryRecallOrchestrator",
                "SQL remains durable authority",
                "Qdrant remains projection/recall metadata",
            ],
        }

    def to_markdown(self) -> str:
        rows = [
            "# Query recall rehydrate contract plan",
            "",
            f"repository_root: `{self.repository_root}`",
            f"output_dir: `{self.output_dir}`",
            f"rehydrate_output_dir: `{self.rehydrate_output_dir}`",
            f"recall_json: `{self.recall_json}`",
            f"query_embedding_json: `{self.query_embedding_json}`",
            f"db_path: `{self.db_path}`",
            f"query_text: `{self.query_text}`",
            f"ready_for_query_recall_rehydrate_contract: `{str(self.ready).lower()}`",
            f"execute: `{str(self.execute).lower()}`",
            "",
            "## Existing surfaces",
            "",
            "| key | status | required | path | reason |",
            "| --- | --- | --- | --- | --- |",
        ]
        for surface in self.surfaces:
            row = surface.to_mapping(root=self.repository_root)
            rows.append(f"| {row['key']} | {row['status']} | `{str(row['required']).lower()}` | `{row['path']}` | {row['reason']} |")
        rows.extend([
            "",
            "## Boundary",
            "",
            "- query text must use the E5 `query:` role",
            "- recall payload must carry `sql_ref` pointers",
            "- durable rehydrate is delegated to 0159",
            "- no new OpenVINO adapter, Qdrant adapter, Scheduler runner, SQL worker, or orchestrator",
            "",
        ])
        return "\n".join(rows)


@dataclass(frozen=True, slots=True)
class QueryRecallContractResult:
    result_json: Path
    result_md: Path
    query_text: str
    recall_json: Path
    query_embedding_json: Path | None
    db_path: Path
    rehydrate_result_json: Path
    rehydrate_status: str
    sql_refs: tuple[str, ...]
    hydrated_count: int
    missing_count: int
    status: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "result_json": str(self.result_json),
            "result_md": str(self.result_md),
            "query_text": self.query_text,
            "query_text_role": "query",
            "recall_json": str(self.recall_json),
            "query_embedding_json": str(self.query_embedding_json) if self.query_embedding_json is not None else None,
            "db_path": str(self.db_path),
            "rehydrate_result_json": str(self.rehydrate_result_json),
            "rehydrate_status": self.rehydrate_status,
            "sql_refs": list(self.sql_refs),
            "hydrated_count": self.hydrated_count,
            "missing_count": self.missing_count,
            "status": self.status,
            "boundary": "query recall contract delegates authority retrieval to 0159; SQL remains durable authority",
        }

    def to_markdown(self) -> str:
        rows = [
            "# Query recall rehydrate contract result",
            "",
            f"status: `{self.status}`",
            f"query_text: `{self.query_text}`",
            f"recall_json: `{self.recall_json}`",
            f"query_embedding_json: `{self.query_embedding_json}`",
            f"db_path: `{self.db_path}`",
            f"rehydrate_result_json: `{self.rehydrate_result_json}`",
            f"rehydrate_status: `{self.rehydrate_status}`",
            f"sql_ref_count: `{len(self.sql_refs)}`",
            f"hydrated_count: `{self.hydrated_count}`",
            f"missing_count: `{self.missing_count}`",
            "",
            "## SQL refs",
            "",
        ]
        rows.extend(f"- `{ref}`" for ref in self.sql_refs)
        rows.extend(["", "boundary: `SQL remains durable authority; Qdrant remains projection/recall metadata`", ""])
        return "\n".join(rows)


def build_query_recall_rehydrate_contract_plan(
    root: Path,
    *,
    output_dir: Path,
    recall_json: Path,
    query_embedding_json: Path | None,
    db_path: Path,
    query_text: str,
    execute: bool,
) -> QueryRecallContractPlan:
    root = root.resolve()
    output_dir = _resolve_repo_path(root, output_dir)
    rehydrate_output_dir = output_dir / "rehydrate-0159"
    recall_json = _resolve_repo_path(root, recall_json)
    query_embedding_json = _resolve_repo_path(root, query_embedding_json) if query_embedding_json is not None else None
    db_path = _resolve_repo_path(root, db_path)
    surfaces = [
        QueryRecallSurface("embed_e5_cli", root / "tools" / "embed_e5.py", "existing E5/OpenVINO query embedding CLI"),
        QueryRecallSurface("qdrant_projection_adapter", root / "src" / "inference" / "qdrant_projection_adapter.py", "existing Qdrant projection/recall helper vocabulary"),
        QueryRecallSurface("qdrant_projection_live_smoke", root / "tools" / "run_qdrant_projection_live_smoke.py", "existing live Qdrant projection smoke surface", required=False),
        QueryRecallSurface("search_e5_corpus", root / "tools" / "search_e5_corpus.py", "existing local E5 search CLI surface", required=False),
        QueryRecallSurface("rehydrate_0159_tool", root / "tools" / "run_qdrant_recall_sql_rehydrate_smoke.py", "existing 0159 recall payload to SQL rehydrate operator"),
        QueryRecallSurface("sql_context_store", root / "src" / "context" / "sql_context_store.py", "existing durable SQL authority"),
        QueryRecallSurface("recall_json", recall_json, "Qdrant-style recall payload carrying sql_ref pointers"),
    ]
    if query_embedding_json is not None:
        surfaces.append(QueryRecallSurface("query_embedding_json", query_embedding_json, "optional existing query embedding artifact"))
    return QueryRecallContractPlan(
        repository_root=root,
        output_dir=output_dir,
        rehydrate_output_dir=rehydrate_output_dir,
        recall_json=recall_json,
        query_embedding_json=query_embedding_json,
        db_path=db_path,
        query_text=_normalize_query_text(query_text),
        result_json=output_dir / "query_recall_rehydrate_contract_result.json",
        result_md=output_dir / "query_recall_rehydrate_contract_report.md",
        execute=execute,
        surfaces=tuple(surfaces),
    )


def execute_query_recall_rehydrate_contract_plan(plan: QueryRecallContractPlan) -> int:
    if not plan.ready:
        for surface in plan.surfaces:
            if surface.required and not surface.path.exists():
                print(f"missing required surface: {surface.path}", file=sys.stderr)
        return 2
    plan.output_dir.mkdir(parents=True, exist_ok=True)
    plan.rehydrate_output_dir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(_rehydrate_command(plan), cwd=plan.repository_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (plan.output_dir / "0160_0159_rehydrate.log").write_text(completed.stdout or "", encoding="utf-8")
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.returncode != 0:
        return completed.returncode
    rehydrate_result_json = plan.rehydrate_output_dir / "qdrant_recall_sql_rehydrate_result.json"
    rehydrate = _read_json_mapping(rehydrate_result_json)
    sql_refs = tuple(str(item) for item in rehydrate.get("sql_refs", []) if str(item).startswith("sql:"))
    hydrated_count = int(rehydrate.get("hydrated_count", 0))
    missing_count = int(rehydrate.get("missing_count", 0))
    rehydrate_status = str(rehydrate.get("status", "unknown"))
    status = "ok" if rehydrate_status == "ok" and hydrated_count > 0 and missing_count == 0 and sql_refs else "partial"
    result = QueryRecallContractResult(
        result_json=plan.result_json,
        result_md=plan.result_md,
        query_text=plan.query_text,
        recall_json=plan.recall_json,
        query_embedding_json=plan.query_embedding_json,
        db_path=plan.db_path,
        rehydrate_result_json=rehydrate_result_json,
        rehydrate_status=rehydrate_status,
        sql_refs=sql_refs,
        hydrated_count=hydrated_count,
        missing_count=missing_count,
        status=status,
    )
    plan.result_json.write_text(json.dumps(result.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.result_md.write_text(result.to_markdown(), encoding="utf-8")
    print("==> query_recall_rehydrate_contract")
    print(result.to_markdown(), end="")
    return 0 if status == "ok" else 1


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lock the query -> recall payload -> SQL rehydrate contract boundary.")
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--recall-json", type=Path, default=Path(DEFAULT_RECALL_JSON))
    parser.add_argument("--query-embedding-json", type=Path, default=None)
    parser.add_argument("--db-path", type=Path, default=Path(DEFAULT_DB_PATH))
    parser.add_argument("--query-text", default=DEFAULT_QUERY_TEXT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    plan = build_query_recall_rehydrate_contract_plan(
        args.repository_root,
        output_dir=args.output_dir,
        recall_json=args.recall_json,
        query_embedding_json=args.query_embedding_json,
        db_path=args.db_path,
        query_text=args.query_text,
        execute=args.execute,
    )
    if args.format == "json":
        print(json.dumps(plan.to_mapping(), indent=2, sort_keys=True))
    else:
        print(plan.to_markdown(), end="")
    if not args.execute:
        return 0 if plan.ready else 2
    return execute_query_recall_rehydrate_contract_plan(plan)


def _rehydrate_command(plan: QueryRecallContractPlan) -> list[str]:
    return [
        sys.executable,
        str(plan.repository_root / "tools" / "run_qdrant_recall_sql_rehydrate_smoke.py"),
        str(plan.repository_root),
        "--recall-json",
        str(plan.recall_json),
        "--output-dir",
        str(plan.rehydrate_output_dir),
        "--db-path",
        str(plan.db_path),
        "--query-text",
        plan.query_text,
        "--execute",
        "--format",
        "json",
    ]


def _read_json_mapping(path: Path) -> Mapping[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping):
        raise ValueError(f"expected JSON object in {path}")
    return loaded


def _resolve_repo_path(root: Path, path: Path | None) -> Path:
    if path is None:
        raise ValueError("path must not be None")
    path = path.expanduser()
    if path.is_absolute():
        return path
    return root / path


def _normalize_query_text(text: str) -> str:
    if text.startswith("query: "):
        return text
    if text.startswith("passage: "):
        raise ValueError("0160 query contract requires an E5 query role, not passage")
    return f"query: {text}"


def _display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
