#!/usr/bin/env python3
"""Run the source-only 0287-r1 reuse audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (_REPO_ROOT, _SRC_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from context.multi_laboratory_evidence_aggregation_reuse_audit_0287 import (  # noqa: E402
    audit_multi_laboratory_evidence_aggregation_reuse,
    load_audit_sources,
)


def parse_args(argv: tuple[str, ...]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit reusable multi-laboratory evidence surfaces without "
            "importing or executing them."
        )
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=_REPO_ROOT,
    )
    parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="summary",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: tuple[str, ...] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    result = audit_multi_laboratory_evidence_aggregation_reuse(
        load_audit_sources(args.repository_root)
    )
    report = result.to_mapping()
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    if args.format == "json":
        print(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"valid: {result.valid}")
        print(f"scanned_file_count: {result.scanned_file_count}")
        print(f"completed_phases: {len(result.completed_phases)}")
        print(f"next_recommended_patch: {result.next_recommended_patch}")
        for issue in result.issues:
            print(f"issue: {issue}")
    return 0 if result.valid else 3


if __name__ == "__main__":
    raise SystemExit(main())
