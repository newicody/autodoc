#!/usr/bin/env python3
"""Audit architecture docs, DOT graphs, and reusable runtime surfaces.

0153 is intentionally audit-only. It inventories current documentation and code
surfaces after the P1 local vector/SQL path landed, without rewriting historical
docs or creating new orchestrators.
"""
from __future__ import annotations

def _call_signature(name: str) -> str:
    return name + "("

import argparse
import ast
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

DEFAULT_OUTPUT_DIR = Path(".var/smoke/artifacts/0153")

SURFACES: dict[str, dict[str, object]] = {
    "openvino_e5_embedding": {
        "phase": "P1",
        "paths": [
            "tools/embed_e5.py",
            "tools/run_openvino_e5_live_smoke.py",
            "src/inference/openvino_embedding_adapter.py",
            "src/inference/openvino_runtime.py",
        ],
        "required_strings": {
            "tools/embed_e5.py": ["--full-vector", "--format"],
            "src/inference/openvino_runtime.py": [],
        },
    },
    "qdrant_projection": {
        "phase": "P1",
        "paths": [
            "tools/run_qdrant_projection_live_smoke.py",
            "src/inference/qdrant_projection_adapter.py",
            "src/context/vector_collection_registry.py",
        ],
        "required_strings": {
            "tools/run_qdrant_projection_live_smoke.py": ["--vector-json", "HTTP 409"],
            "src/inference/qdrant_projection_adapter.py": ["QdrantProjectionExecutor"],
        },
    },
    "scheduler_routeproxy_frames": {
        "phase": "P1",
        "paths": [
            "src/runtime/scheduler_route_handler_minimal.py",
            "src/runtime/route_proxy_runtime_minimal.py",
            "tools/run_scheduler_vector_indexing_smoke.py",
        ],
        "required_strings": {
            "tools/run_scheduler_vector_indexing_smoke.py": [
                "vector_embedding_request",
                "vector_indexing_result",
                "--request-route-ref",
                "--result-route-ref",
            ],
        },
    },
    "artifact_intake_and_refs": {
        "phase": "P1",
        "paths": [
            "src/context/artifact_intake_contract.py",
            "src/context/artifact_route_refs.py",
            "tools/run_local_artifact_vector_indexing_runner.py",
        ],
        "required_strings": {
            "tools/run_local_artifact_vector_indexing_runner.py": [
                "artifact_intake_contract.json",
                "artifact_route_refs",
            ],
        },
    },
    "sql_context_store_persistence": {
        "phase": "P1",
        "paths": [
            "src/context/sql_context_store.py",
            "src/context/sql_context_store_controlled_write_contract.py",
            "tools/run_sql_context_store_controlled_write_smoke.py",
        ],
        "required_strings": {
            "src/context/sql_context_store.py": ["DbApiSqlContextStore", "upsert_record"],
            "tools/run_sql_context_store_controlled_write_smoke.py": [
                "AUTODOC_SQL_CONTEXT_DB",
                "DbApiSqlContextStore(connection)",
            ],
        },
    },
    "p1_single_runner": {
        "phase": "P1",
        "paths": ["tools/run_p1_local_artifact_pipeline.py"],
        "required_strings": {},
    },
    "filesystem_ingestion": {
        "phase": "P2",
        "paths": ["tools/run_filesystem_intake.py", "src/context/filesystem_intake_contract.py"],
        "required_strings": {},
    },
    "chunking_and_hashing": {
        "phase": "P2",
        "paths": ["src/context/chunking_contract.py", "src/context/content_hash_contract.py"],
        "required_strings": {},
    },
    "scheduler_operational_jobs": {
        "phase": "P3",
        "paths": ["src/runtime/scheduler.py", "src/runtime/dispatcher.py", "src/context/vector_indexing_job_plan.py"],
        "required_strings": {},
    },
    "vispy_observability": {
        "phase": "P3/P6",
        "paths": ["tools/run_vispy_observer.py", "src/observability/vispy"],
        "required_strings": {},
    },
    "github_artifact_exchange": {
        "phase": "P4/P7",
        "paths": ["src/integrations/github", ".github/workflows"],
        "required_strings": {},
    },
    "distributed_routeproxy": {
        "phase": "P5",
        "paths": ["src/runtime/distributed_route_proxy.py", "src/context/node_identity_contract.py"],
        "required_strings": {},
    },
}

PHASES = ("P1", "P2", "P3", "P4/P7", "P3/P6", "P5")

FORBIDDEN_LIVE_RUNTIME_STRINGS = (
    "Scheduler" + ".run(",
    _call_signature("LocalVectorIndexingOrchestrator"),
    _call_signature("LocalArtifactOrchestrator"),
    _call_signature("VectorOpenVINOEmbeddingAdapter"),
    _call_signature("VectorQdrantProjectionAdapter"),
    _call_signature("SQLPersistenceWorker"),
    _call_signature("SQLOrchestrator"),
)


@dataclass(frozen=True)
class SurfaceAudit:
    key: str
    phase: str
    present_paths: tuple[str, ...]
    missing_paths: tuple[str, ...]
    missing_required_strings: tuple[str, ...]
    completeness_percent: int
    status: str


@dataclass(frozen=True)
class DocsAudit:
    markdown_count: int
    dot_count: int
    architecture_markdown_count: int
    runtime_dot_count: int
    docs_with_forbidden_live_runtime_strings: tuple[str, ...]
    dot_parse_warnings: tuple[str, ...]
    stale_static_ref_mentions: tuple[str, ...]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _existing(path: Path) -> bool:
    return path.exists()


def _audit_surface(root: Path, key: str, spec: dict[str, object]) -> SurfaceAudit:
    paths = tuple(str(p) for p in spec.get("paths", ()))
    present: list[str] = []
    missing: list[str] = []
    for rel in paths:
        if _existing(root / rel):
            present.append(rel)
        else:
            missing.append(rel)

    missing_strings: list[str] = []
    required_strings = spec.get("required_strings", {})
    if isinstance(required_strings, dict):
        for rel, phrases in required_strings.items():
            path = root / str(rel)
            if not path.exists():
                continue
            text = _read(path)
            for phrase in phrases or []:
                if str(phrase) not in text:
                    missing_strings.append(f"{rel}: {phrase}")

    total_units = max(1, len(paths) + sum(len(v or []) for v in (required_strings or {}).values()))
    missing_units = len(missing) + len(missing_strings)
    completeness = max(0, round(100 * (total_units - missing_units) / total_units))
    status = "complete" if completeness == 100 else "partial" if present else "missing"
    return SurfaceAudit(
        key=key,
        phase=str(spec.get("phase", "unknown")),
        present_paths=tuple(present),
        missing_paths=tuple(missing),
        missing_required_strings=tuple(missing_strings),
        completeness_percent=int(completeness),
        status=status,
    )


def _iter_docs(root: Path) -> Iterable[Path]:
    doc_root = root / "doc"
    if not doc_root.exists():
        return ()
    return tuple(p for p in doc_root.rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".dot"})


def _audit_docs(root: Path) -> DocsAudit:
    docs = tuple(_iter_docs(root))
    markdown = tuple(p for p in docs if p.suffix.lower() == ".md")
    dots = tuple(p for p in docs if p.suffix.lower() == ".dot")
    architecture_md = tuple(p for p in markdown if "architecture" in p.parts)
    runtime_dots = tuple(p for p in dots if "runtime" in p.parts)

    forbidden_hits: list[str] = []
    stale_hits: list[str] = []
    for path in docs:
        rel = path.relative_to(root).as_posix()
        text = _read(path)
        for phrase in FORBIDDEN_LIVE_RUNTIME_STRINGS:
            if phrase in text:
                forbidden_hits.append(f"{rel}: {phrase}")
        # Historical docs may mention old refs. This is a warning, not a failure.
        for phrase in ("vector-route:smoke/0143", "vector-route:smoke/0144"):
            if phrase in text:
                stale_hits.append(f"{rel}: {phrase}")

    dot_warnings: list[str] = []
    for path in dots:
        text = _read(path).strip()
        if not text.startswith("digraph") and not text.startswith("graph"):
            dot_warnings.append(f"{path.relative_to(root).as_posix()}: missing graph/digraph header")
        if "{" not in text or "}" not in text:
            dot_warnings.append(f"{path.relative_to(root).as_posix()}: missing braces")

    return DocsAudit(
        markdown_count=len(markdown),
        dot_count=len(dots),
        architecture_markdown_count=len(architecture_md),
        runtime_dot_count=len(runtime_dots),
        docs_with_forbidden_live_runtime_strings=tuple(sorted(set(forbidden_hits))),
        dot_parse_warnings=tuple(sorted(set(dot_warnings))),
        stale_static_ref_mentions=tuple(sorted(set(stale_hits))),
    )


def _audit_ast_sql_store(root: Path) -> dict[str, object]:
    path = root / "src/context/sql_context_store.py"
    if not path.exists():
        return {"path": str(path), "exists": False, "classes": [], "functions": []}
    tree = ast.parse(_read(path))
    classes: dict[str, list[str]] = {}
    functions: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [item.name for item in node.body if isinstance(item, ast.FunctionDef)]
            classes[node.name] = methods
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
    return {"path": "src/context/sql_context_store.py", "exists": True, "classes": classes, "functions": functions}


def _phase_rollup(surfaces: list[SurfaceAudit]) -> dict[str, int]:
    phases: dict[str, list[int]] = {}
    for item in surfaces:
        phases.setdefault(item.phase, []).append(item.completeness_percent)
    return {phase: round(sum(values) / len(values)) for phase, values in sorted(phases.items())}


def _to_markdown(root: Path, surfaces: list[SurfaceAudit], docs: DocsAudit, sql_ast: dict[str, object]) -> str:
    lines: list[str] = ["# Architecture docs and surface audit — 0153", ""]
    lines += [
        f"repository_root: `{root}`",
        "audit_mode: `read_only`",
        "boundary: `documentation/surface audit only; no runtime orchestration added`",
        "",
        "## Surface completeness",
        "",
        "| key | phase | status | completeness | missing paths | missing strings |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for item in surfaces:
        missing_paths = ", ".join(f"`{p}`" for p in item.missing_paths) or "-"
        missing_strings = ", ".join(f"`{p}`" for p in item.missing_required_strings) or "-"
        lines.append(
            f"| `{item.key}` | `{item.phase}` | `{item.status}` | `{item.completeness_percent}%` | {missing_paths} | {missing_strings} |"
        )
    lines += ["", "## Phase rollup", ""]
    for phase, percent in _phase_rollup(surfaces).items():
        lines.append(f"- `{phase}`: `{percent}%`")
    lines += [
        "",
        "## Documentation inventory",
        "",
        f"markdown_count: `{docs.markdown_count}`",
        f"dot_count: `{docs.dot_count}`",
        f"architecture_markdown_count: `{docs.architecture_markdown_count}`",
        f"runtime_dot_count: `{docs.runtime_dot_count}`",
        f"dot_parse_warnings: `{len(docs.dot_parse_warnings)}`",
        f"forbidden_live_runtime_string_hits: `{len(docs.docs_with_forbidden_live_runtime_strings)}`",
        f"stale_static_ref_mentions: `{len(docs.stale_static_ref_mentions)}`",
        "",
        "## SQL store AST inventory",
        "",
        "```json",
        json.dumps(sql_ast, indent=2, sort_keys=True),
        "```",
        "",
        "## Recommended next docs work",
        "",
        "1. keep historical phase docs, but add current-state index pages that point to canonical surfaces.",
        "2. normalize stale boundary phrases that contain forbidden live-runtime strings.",
        "3. preserve hierarchy under `doc/architecture`, `doc/code-rules`, `doc/docs/architecture/runtime`, and `doc/manifests`.",
        "4. update DOT graphs by adding summary graphs instead of deleting phase graphs.",
    ]
    return "\n".join(lines) + "\n"


def run(root: Path, output_dir: Path, execute: bool) -> dict[str, object]:
    root = root.resolve()
    output_dir = (root / output_dir).resolve() if not output_dir.is_absolute() else output_dir
    surfaces = [_audit_surface(root, key, spec) for key, spec in SURFACES.items()]
    docs = _audit_docs(root)
    sql_ast = _audit_ast_sql_store(root)
    payload = {
        "schema": "missipy.architecture_docs_surface_audit.v1",
        "repository_root": str(root),
        "execute": execute,
        "audit_mode": "read_only",
        "surface_audits": [asdict(item) for item in surfaces],
        "phase_rollup": _phase_rollup(surfaces),
        "docs_audit": asdict(docs),
        "sql_context_store_ast": sql_ast,
        "recommended_next_patch": "0154-architecture_docs_current_state_refresh",
    }
    report = _to_markdown(root, surfaces, docs, sql_ast)
    if execute:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "architecture_docs_surface_audit.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (output_dir / "architecture_docs_surface_audit_report.md").write_text(report, encoding="utf-8")
    return payload | {"report_markdown": report, "output_dir": str(output_dir)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository_root", nargs="?", default=".")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)

    result = run(Path(args.repository_root), Path(args.output_dir), args.execute)
    if args.format == "json":
        clean = {k: v for k, v in result.items() if k != "report_markdown"}
        print(json.dumps(clean, indent=2, sort_keys=True))
    else:
        print(result["report_markdown"], end="")
        if args.execute:
            out = Path(result["output_dir"])
            print("==> architecture_docs_surface_audit")
            print(f"audit_json: `{out / 'architecture_docs_surface_audit.json'}`")
            print(f"audit_report: `{out / 'architecture_docs_surface_audit_report.md'}`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
