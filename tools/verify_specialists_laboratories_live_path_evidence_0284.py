#!/usr/bin/env python3
"""Thin IO adapter for phase 0284-r9 live-path evidence verification."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from context.specialists_laboratories_chain_closure_audit_0284 import (
    FORBIDDEN_ACTIVE_AUTODOC_PROJECT_SURFACES,
    REQUIRED_CHAIN_SURFACES,
    REQUIRED_SUPPORT_SURFACES,
)
from context.specialists_laboratories_live_path_evidence_0284 import (
    SpecialistsLaboratoriesLivePathEvidenceCommand,
    build_specialists_laboratories_live_path_evidence,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify one saved 0284-r7 integrated result against the current "
            "repository surfaces without executing or mutating any backend."
        )
    )
    parser.add_argument("--integrated-result", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--evidence-ref", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-revision", default="working-tree")
    parser.add_argument("--report-file", type=Path)
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("integrated result must contain one JSON object")
    return value


def _load_sources(root: Path) -> dict[str, str]:
    requirements = REQUIRED_CHAIN_SURFACES + REQUIRED_SUPPORT_SURFACES
    paths = [requirement.path for requirement in requirements]
    paths.extend(FORBIDDEN_ACTIVE_AUTODOC_PROJECT_SURFACES)
    sources: dict[str, str] = {}
    for relative in dict.fromkeys(paths):
        path = root / relative
        if path.is_file():
            sources[relative] = path.read_text(encoding="utf-8")
    return sources


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _summary(mapping: dict[str, object]) -> str:
    issues = mapping.get("issues", [])
    lines = [
        f"valid: {str(mapping.get('valid', False)).lower()}",
        f"phase_0284_closed: {str(mapping.get('phase_0284_closed', False)).lower()}",
        f"live_path_status: {mapping.get('live_path_status', 'red')}",
        f"evidence_digest: {mapping.get('evidence_digest', '')}",
        f"sql_ref: {mapping.get('sql_ref', '')}",
        f"vector_dimensions: {mapping.get('vector_dimensions', [])}",
    ]
    if isinstance(issues, list) and issues:
        lines.append("issues:")
        lines.extend(f"- {issue}" for issue in issues)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    command = SpecialistsLaboratoriesLivePathEvidenceCommand(
        evidence_ref=args.evidence_ref,
        repository=args.repository,
        run_id=args.run_id,
        source_revision=args.source_revision,
    )
    result = build_specialists_laboratories_live_path_evidence(
        command,
        _load_json(args.integrated_result),
        _load_sources(args.repository_root),
    )
    mapping = result.to_mapping()
    if args.report_file is not None:
        _atomic_write_json(args.report_file, mapping)
    if args.format == "json":
        print(json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(_summary(mapping))
    return 0 if result.phase_0284_closed else 1


if __name__ == "__main__":
    raise SystemExit(main())
