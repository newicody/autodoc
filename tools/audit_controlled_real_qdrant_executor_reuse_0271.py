#!/usr/bin/env python3
"""Read repository source files and write the passive 0271-r1 reuse audit."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Mapping

from context.controlled_real_qdrant_executor_reuse_audit_0271 import (
    audit_controlled_real_qdrant_executor_reuse,
)

DEFAULT_OUTPUT = Path(".var/reports/controlled_real_qdrant_executor_reuse_audit_0271.json")
SCAN_ROOTS = ("src", "tools")
SKIP_PARTS = {".git", ".var", "patch", "__pycache__", ".pytest_cache"}


def collect_python_sources(repo_root: Path) -> dict[str, str]:
    """Collect repository-relative Python text without importing modules."""

    sources: dict[str, str] = {}
    for root_name in SCAN_ROOTS:
        base = repo_root / root_name
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            relative = path.relative_to(repo_root)
            if any(part in SKIP_PARTS for part in relative.parts):
                continue
            sources[relative.as_posix()] = path.read_text(encoding="utf-8")
    return sources


def write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    """Write one JSON report atomically at the CLI/IO edge."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(dict(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit reuse surfaces before implementing a real Qdrant executor."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    result = audit_controlled_real_qdrant_executor_reuse(
        collect_python_sources(repo_root)
    )
    payload = result.to_mapping()
    write_json_atomic(Path(args.output), payload)

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            "controlled_real_qdrant_executor_reuse_audit_valid="
            f"{result.valid} issues={len(result.issues)} "
            f"scanned_files={result.scanned_file_count} "
            f"protocol_found={result.protocol_found} "
            f"live_executor_found={result.live_executor_found} "
            f"implementation_needed={result.implementation_needed} "
            f"new_executor_module_justified={result.new_executor_module_justified} "
            f"next={result.next_recommended_patch}"
        )
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
