#!/usr/bin/env python3
"""Audit existing runtime bricks before adding Scheduler-owned execution code.

This audit supports the "do not reinvent the wheel" rule.  It searches the
repository for existing Scheduler, EventBus, SQL, OpenVINO, Qdrant, GitHub, and
PassiveSupervisor surfaces that should be reused before adding any new runtime
component implementation.

The audit is read-only:
- no imports from target modules
- no component instantiation
- no Scheduler.run call
- no SQL/Qdrant/GitHub/OpenVINO call
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]


SEARCH_SURFACES: dict[str, tuple[str, ...]] = {
    "scheduler": (
        r"\bclass\s+Scheduler\b",
        r"\bdef\s+run\s*\(",
        r"Scheduler\s*=",
        r"scheduler\.",
    ),
    "eventbus": (
        r"\bclass\s+EventBus\b",
        r"event_bus",
        r"context\.bus",
        r"publish\(",
        r"subscribe\(",
    ),
    "passive_supervisor": (
        r"PassiveSupervisorSink",
        r"passive_supervisor",
        r"CellularState",
        r"cellular_snapshot",
    ),
    "sql_context_store": (
        r"DbApiSqlContextStore",
        r"SQLContextStore",
        r"context_records",
        r"controlled_write",
        r"sql_ref",
    ),
    "openvino_embedding": (
        r"OpenVINO",
        r"openvino",
        r"multilingual-e5-small",
        r"embed_query",
        r"embed_passage",
        r"mean pooling",
    ),
    "qdrant_projection": (
        r"Qdrant",
        r"qdrant",
        r"QDRANT",
        r"qdrant_ref",
        r"sql_ref",
    ),
    "github_artifact_exchange": (
        r"ProjectPushFrame",
        r"GitHubArtifact",
        r"github_artifact",
        r"GITHUB_TOKEN",
        r"publication_review_required",
    ),
}


RUNTIME_CREATION_RED_FLAGS: tuple[str, ...] = (
    "RuntimeManager",
    "RuntimeOrchestrator",
    "SQLOrchestrator",
    "LocalArtifactOrchestrator",
    "SchedulerOpenVINORunner",
    "VectorOpenVINOEmbeddingAdapter",
    "VectorQdrantProjectionAdapter",
)


DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    ".var",
    "patch",
    "dist",
    "build",
}


@dataclass(frozen=True)
class SurfaceFinding:
    surface: str
    path: str
    line: int
    pattern: str
    snippet: str

    def to_dict(self) -> dict[str, object]:
        return {
            "surface": self.surface,
            "path": self.path,
            "line": self.line,
            "pattern": self.pattern,
            "snippet": self.snippet,
        }


def iter_text_files(root: Path, *, include_docs: bool = True) -> Iterable[Path]:
    """Yield repository text files suitable for a read-only source audit."""

    suffixes = {".py", ".md", ".dot", ".ini", ".json", ".txt", ".yaml", ".yml", ".toml"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        parts = set(path.relative_to(root).parts)
        if parts & DEFAULT_EXCLUDED_DIRS:
            continue
        if not include_docs and ("doc" in parts or "docs" in parts):
            continue
        if path.suffix.lower() in suffixes:
            yield path


def scan_surface(root: Path, surface: str, patterns: Sequence[str]) -> tuple[SurfaceFinding, ...]:
    """Search one surface using regex patterns without importing target modules."""

    compiled = tuple((pattern, re.compile(pattern)) for pattern in patterns)
    findings: list[SurfaceFinding] = []
    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for pattern, regex in compiled:
                if regex.search(line):
                    findings.append(
                        SurfaceFinding(
                            surface=surface,
                            path=str(path.relative_to(root)),
                            line=line_no,
                            pattern=pattern,
                            snippet=line.strip()[:240],
                        )
                    )
    return tuple(findings)


def scan_red_flags(root: Path) -> tuple[dict[str, object], ...]:
    """Search for names that would suggest a new parallel runtime/orchestrator."""

    results: list[dict[str, object]] = []
    compiled = tuple((flag, re.compile(re.escape(flag))) for flag in RUNTIME_CREATION_RED_FLAGS)
    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for flag, regex in compiled:
                if regex.search(line):
                    results.append(
                        {
                            "flag": flag,
                            "path": str(path.relative_to(root)),
                            "line": line_no,
                            "snippet": line.strip()[:240],
                        }
                    )
    return tuple(results)


def summarize_findings(findings: Mapping[str, Sequence[SurfaceFinding]]) -> dict[str, object]:
    """Summarize reusable surfaces and next-action guidance."""

    surface_counts = {surface: len(items) for surface, items in findings.items()}
    reusable_surfaces = tuple(surface for surface, count in surface_counts.items() if count > 0)
    missing_surfaces = tuple(surface for surface, count in surface_counts.items() if count == 0)
    return {
        "reuse_audit_passed": len(reusable_surfaces) >= 5,
        "surface_counts": surface_counts,
        "reusable_surfaces": reusable_surfaces,
        "missing_surfaces": missing_surfaces,
        "recommendation": (
            "reuse_existing_surfaces_before_new_runtime_code"
            if reusable_surfaces
            else "manual_repository_review_required"
        ),
    }


def run_audit(root: Path) -> dict[str, object]:
    """Run the read-only Scheduler-owned runtime reuse audit."""

    findings = {
        surface: scan_surface(root, surface, patterns)
        for surface, patterns in SEARCH_SURFACES.items()
    }
    red_flags = scan_red_flags(root)
    summary = summarize_findings(findings)
    return {
        "scheduler_owned_runtime_reuse_audit": True,
        "read_only": True,
        "imports_target_modules": False,
        "instantiates_components": False,
        "calls_scheduler_run": False,
        "writes_sql": False,
        "writes_qdrant": False,
        "calls_github_api": False,
        "runs_openvino_inference": False,
        "summary": summary,
        "findings": {
            surface: [finding.to_dict() for finding in items[:50]]
            for surface, items in findings.items()
        },
        "red_flags": list(red_flags[:100]),
        "red_flag_count": len(red_flags),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--output", default="")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    payload = run_audit(root)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "summary":
        counts = payload["summary"]["surface_counts"]
        surface_summary = ",".join(f"{key}={value}" for key, value in sorted(counts.items()))
        print(
            "scheduler_owned_runtime_reuse_audit_passed="
            f"{payload['summary']['reuse_audit_passed']} "
            f"red_flags={payload['red_flag_count']} {surface_summary}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
