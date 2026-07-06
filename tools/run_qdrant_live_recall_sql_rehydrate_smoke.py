#!/usr/bin/env python3
"""Live Qdrant recall -> SQL rehydrate smoke.

0161 proves the live recall boundary without introducing a new adapter,
worker, runner or orchestrator. It consumes a query embedding JSON produced by
the existing E5/OpenVINO CLI, calls Qdrant REST `/points/search`, writes the
recall payload, then delegates durable SQL rehydrate to the existing 0159 tool.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence
from urllib import error, request


DEFAULT_OUTPUT_DIR = ".var/smoke/artifacts/0161"
DEFAULT_QUERY_VECTOR_JSON = ".var/smoke/artifacts/0161/0161_query_embedding.json"
DEFAULT_DB_PATH = ".var/local/sql_context_store.sqlite3"
DEFAULT_QDRANT_URL = "http://127.0.0.1:6333"
DEFAULT_COLLECTION = "autodoc_smoke_e5_384"
DEFAULT_LIMIT = 5
DEFAULT_QUERY_TEXT = "query: P1 closed loop artifact vector indexing SQL persistence"

_REUSED_SURFACES = (
    "tools/embed_e5.py",
    "tools/run_qdrant_projection_live_smoke.py",
    "tools/run_qdrant_recall_sql_rehydrate_smoke.py",
    "src/inference/qdrant_projection_adapter.py",
    "src/context/sql_context_store.py",
    "QdrantProjectionExecutor.search_vector",
    "QdrantProjectionAdapter.recall_by_vector",
    "QdrantRecallQuery",
    "QdrantRecallResult",
    "unique_sql_context_refs_from_recall",
    "/collections/{collection}/points/search",
    "DbApiSqlContextStore.get_record",
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
class QdrantLiveRecallSurface:
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
class QdrantLiveRecallPlan:
    repository_root: Path
    output_dir: Path
    rehydrate_output_dir: Path
    query_vector_json: Path
    recall_json: Path
    result_json: Path
    result_md: Path
    db_path: Path
    qdrant_url: str
    collection: str
    limit: int
    score_threshold: float | None
    query_text: str
    execute: bool
    surfaces: tuple[QdrantLiveRecallSurface, ...]

    @property
    def ready(self) -> bool:
        return all(surface.path.exists() for surface in self.surfaces if surface.required)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository_root": str(self.repository_root),
            "output_dir": str(self.output_dir),
            "rehydrate_output_dir": str(self.rehydrate_output_dir),
            "query_vector_json": str(self.query_vector_json),
            "recall_json": str(self.recall_json),
            "result_json": str(self.result_json),
            "result_md": str(self.result_md),
            "db_path": str(self.db_path),
            "qdrant_url": self.qdrant_url,
            "collection": self.collection,
            "limit": self.limit,
            "score_threshold": self.score_threshold,
            "query_text": self.query_text,
            "query_text_role": "query",
            "execute": self.execute,
            "ready_for_qdrant_live_recall_sql_rehydrate": self.ready,
            "surfaces": [surface.to_mapping(root=self.repository_root) for surface in self.surfaces],
            "commands": {
                "query_embedding": [
                    sys.executable,
                    str(self.repository_root / "tools" / "embed_e5.py"),
                    "--role",
                    "query",
                    "--format",
                    "json",
                    "--full-vector",
                    self.query_text,
                ],
                "qdrant_rest_search": [
                    "POST",
                    _qdrant_url(self.qdrant_url, f"/collections/{self.collection}/points/search"),
                ],
                "0159_rehydrate": _rehydrate_command(self),
            },
            "boundary": [
                "uses query embedding JSON produced by existing tools/embed_e5.py",
                "calls Qdrant REST /points/search like the existing live projection smoke",
                "writes a Qdrant-style recall payload carrying sql_ref pointers",
                "delegates durable SQL rehydrate to existing 0159 tool",
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
        lines = [
            "# Qdrant live recall -> SQL rehydrate plan",
            "",
            f"repository_root: `{self.repository_root}`",
            f"query_vector_json: `{self.query_vector_json}`",
            f"recall_json: `{self.recall_json}`",
            f"db_path: `{self.db_path}`",
            f"qdrant_url: `{self.qdrant_url}`",
            f"collection: `{self.collection}`",
            f"limit: `{self.limit}`",
            f"score_threshold: `{self.score_threshold}`",
            f"query_text: `{self.query_text}`",
            f"ready_for_qdrant_live_recall_sql_rehydrate: `{str(self.ready).lower()}`",
            f"execute: `{str(self.execute).lower()}`",
            "",
            "## Existing surfaces",
            "",
            "| key | status | required | path | reason |",
            "| --- | --- | --- | --- | --- |",
        ]
        for surface in self.surfaces:
            row = surface.to_mapping(root=self.repository_root)
            lines.append(f"| {row['key']} | {row['status']} | `{str(row['required']).lower()}` | `{row['path']}` | {row['reason']} |")
        lines.extend([
            "",
            "## Boundary",
            "",
            "- query vector comes from existing E5/OpenVINO CLI output",
            "- Qdrant live recall uses REST `/points/search`",
            "- SQL rehydrate is delegated to 0159",
            "- no new adapter, worker, runner, backend, or orchestrator",
            "",
        ])
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class QdrantLiveRecallResult:
    result_json: Path
    result_md: Path
    query_vector_json: Path
    recall_json: Path
    db_path: Path
    qdrant_url: str
    collection: str
    query_vector_dimension: int
    recall_hit_count: int
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
            "query_vector_json": str(self.query_vector_json),
            "recall_json": str(self.recall_json),
            "db_path": str(self.db_path),
            "qdrant_url": self.qdrant_url,
            "collection": self.collection,
            "query_vector_dimension": self.query_vector_dimension,
            "recall_hit_count": self.recall_hit_count,
            "rehydrate_result_json": str(self.rehydrate_result_json),
            "rehydrate_status": self.rehydrate_status,
            "sql_refs": list(self.sql_refs),
            "hydrated_count": self.hydrated_count,
            "missing_count": self.missing_count,
            "status": self.status,
            "boundary": "live Qdrant recall returns sql_ref pointers; SQL remains durable authority",
        }

    def to_markdown(self) -> str:
        lines = [
            "# Qdrant live recall -> SQL rehydrate result",
            "",
            f"status: `{self.status}`",
            f"query_vector_dimension: `{self.query_vector_dimension}`",
            f"recall_hit_count: `{self.recall_hit_count}`",
            f"rehydrate_status: `{self.rehydrate_status}`",
            f"hydrated_count: `{self.hydrated_count}`",
            f"missing_count: `{self.missing_count}`",
            f"collection: `{self.collection}`",
            "",
            "## SQL refs",
            "",
        ]
        for sql_ref in self.sql_refs:
            lines.append(f"- `{sql_ref}`")
        lines.extend(["", "boundary: `SQL remains durable authority; Qdrant remains projection/recall metadata`", ""])
        return "\n".join(lines)


def build_qdrant_live_recall_sql_rehydrate_plan(
    root: Path,
    *,
    output_dir: Path,
    query_vector_json: Path,
    db_path: Path,
    qdrant_url: str,
    collection: str,
    limit: int,
    score_threshold: float | None,
    query_text: str,
    execute: bool,
) -> QdrantLiveRecallPlan:
    root = root.resolve()
    output_dir = _resolve_repo_path(root, output_dir)
    query_vector_json = _resolve_repo_path(root, query_vector_json)
    db_path = _resolve_repo_path(root, db_path)

    return QdrantLiveRecallPlan(
        repository_root=root,
        output_dir=output_dir,
        rehydrate_output_dir=output_dir / "rehydrate-0159",
        query_vector_json=query_vector_json,
        recall_json=output_dir / "qdrant_live_recall_payload.json",
        result_json=output_dir / "qdrant_live_recall_sql_rehydrate_result.json",
        result_md=output_dir / "qdrant_live_recall_sql_rehydrate_report.md",
        db_path=db_path,
        qdrant_url=qdrant_url.rstrip("/"),
        collection=collection,
        limit=limit,
        score_threshold=score_threshold,
        query_text=_normalize_query_text(query_text),
        execute=execute,
        surfaces=(
            QdrantLiveRecallSurface("embed_e5_cli", root / "tools" / "embed_e5.py", "existing E5/OpenVINO query embedding CLI"),
            QdrantLiveRecallSurface("qdrant_projection_live_smoke", root / "tools" / "run_qdrant_projection_live_smoke.py", "existing Qdrant REST smoke surface with /points/search pattern"),
            QdrantLiveRecallSurface("rehydrate_0159_tool", root / "tools" / "run_qdrant_recall_sql_rehydrate_smoke.py", "existing 0159 recall payload to SQL rehydrate operator"),
            QdrantLiveRecallSurface("qdrant_projection_adapter", root / "src" / "inference" / "qdrant_projection_adapter.py", "existing QdrantRecallQuery/QdrantRecallResult vocabulary"),
            QdrantLiveRecallSurface("sql_context_store", root / "src" / "context" / "sql_context_store.py", "existing durable SQL authority"),
            QdrantLiveRecallSurface("query_vector_json", query_vector_json, "existing full-vector query embedding artifact"),
        ),
    )


def execute_qdrant_live_recall_sql_rehydrate_plan(plan: QdrantLiveRecallPlan) -> int:
    if not plan.ready:
        for surface in plan.surfaces:
            if surface.required and not surface.path.exists():
                print(f"missing required surface: {surface.path}", file=sys.stderr)
        return 2

    plan.output_dir.mkdir(parents=True, exist_ok=True)
    plan.rehydrate_output_dir.mkdir(parents=True, exist_ok=True)

    query_vector = read_query_vector(plan.query_vector_json)
    search_payload = qdrant_search_payload(query_vector, limit=plan.limit, score_threshold=plan.score_threshold)
    qdrant_payload = qdrant_search(qdrant_url=plan.qdrant_url, collection=plan.collection, payload=search_payload)
    normalized_recall = normalize_qdrant_recall_payload(qdrant_payload)
    plan.recall_json.write_text(json.dumps(normalized_recall, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    completed = subprocess.run(
        _rehydrate_command(plan),
        cwd=plan.repository_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    (plan.output_dir / "0161_0159_rehydrate.log").write_text(completed.stdout or "", encoding="utf-8")
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
    recall_hit_count = len(normalized_recall.get("result", [])) if isinstance(normalized_recall.get("result"), list) else 0
    status = "ok" if rehydrate_status == "ok" and hydrated_count > 0 and missing_count == 0 and sql_refs else "partial"

    result = QdrantLiveRecallResult(
        result_json=plan.result_json,
        result_md=plan.result_md,
        query_vector_json=plan.query_vector_json,
        recall_json=plan.recall_json,
        db_path=plan.db_path,
        qdrant_url=plan.qdrant_url,
        collection=plan.collection,
        query_vector_dimension=len(query_vector),
        recall_hit_count=recall_hit_count,
        rehydrate_result_json=rehydrate_result_json,
        rehydrate_status=rehydrate_status,
        sql_refs=sql_refs,
        hydrated_count=hydrated_count,
        missing_count=missing_count,
        status=status,
    )
    plan.result_json.write_text(json.dumps(result.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.result_md.write_text(result.to_markdown(), encoding="utf-8")
    print("==> qdrant_live_recall_sql_rehydrate")
    print(result.to_markdown(), end="")
    return 0 if status == "ok" else 1


def read_query_vector(path: Path) -> list[float]:
    payload = _read_json_mapping(path)
    values = payload.get("values", payload.get("vector"))
    if not isinstance(values, list) or not values:
        raise ValueError("query vector JSON must contain non-empty 'values' or 'vector' list")
    vector = [float(value) for value in values]
    dimension = payload.get("dimension")
    if dimension is not None and int(dimension) != len(vector):
        raise ValueError("query vector dimension does not match vector length")
    return vector


def qdrant_search_payload(vector: Sequence[float], *, limit: int, score_threshold: float | None) -> dict[str, Any]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    payload: dict[str, Any] = {"vector": list(vector), "limit": limit, "with_payload": True, "with_vector": False}
    if score_threshold is not None:
        payload["score_threshold"] = score_threshold
    return payload


def qdrant_search(*, qdrant_url: str, collection: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
    url = _qdrant_url(qdrant_url, f"/collections/{collection}/points/search")
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=30) as response:  # noqa: S310 - local operator smoke URL supplied by CLI
            loaded = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise RuntimeError(f"Qdrant search HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Qdrant search failed: {exc}") from exc
    if not isinstance(loaded, Mapping):
        raise ValueError("Qdrant response must be a JSON object")
    return loaded


def normalize_qdrant_recall_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = payload.get("result", [])
    if not isinstance(result, list):
        result = []
    normalized: list[dict[str, Any]] = []
    for hit in result:
        if not isinstance(hit, Mapping):
            continue
        hit_payload = hit.get("payload", {})
        if not isinstance(hit_payload, Mapping):
            hit_payload = {}
        normalized.append({"id": hit.get("id"), "score": hit.get("score"), "payload": dict(hit_payload)})
    return {"status": payload.get("status", "ok"), "time": payload.get("time"), "result": normalized}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live Qdrant recall and delegate SQL rehydrate to the existing 0159 tool.")
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--query-vector-json", type=Path, default=Path(DEFAULT_QUERY_VECTOR_JSON))
    parser.add_argument("--db-path", type=Path, default=Path(DEFAULT_DB_PATH))
    parser.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--score-threshold", type=float, default=None)
    parser.add_argument("--query-text", default=DEFAULT_QUERY_TEXT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    plan = build_qdrant_live_recall_sql_rehydrate_plan(
        args.repository_root,
        output_dir=args.output_dir,
        query_vector_json=args.query_vector_json,
        db_path=args.db_path,
        qdrant_url=args.qdrant_url,
        collection=args.collection,
        limit=args.limit,
        score_threshold=args.score_threshold,
        query_text=args.query_text,
        execute=args.execute,
    )

    if args.format == "json":
        print(json.dumps(plan.to_mapping(), indent=2, sort_keys=True))
    else:
        print(plan.to_markdown(), end="")

    if not args.execute:
        return 0 if plan.ready else 2

    return execute_qdrant_live_recall_sql_rehydrate_plan(plan)


def _rehydrate_command(plan: QdrantLiveRecallPlan) -> list[str]:
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


def _resolve_repo_path(root: Path, path: Path) -> Path:
    path = path.expanduser()
    if path.is_absolute():
        return path
    return root / path


def _normalize_query_text(text: str) -> str:
    if text.startswith("query: "):
        return text
    if text.startswith("passage: "):
        raise ValueError("0161 live recall requires an E5 query role, not passage")
    return f"query: {text}"


def _qdrant_url(qdrant_url: str, path: str) -> str:
    return qdrant_url.rstrip("/") + path


def _display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
