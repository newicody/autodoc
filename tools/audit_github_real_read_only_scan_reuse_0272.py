#!/usr/bin/env python3
"""CLI adapter for the source-only 0272 GitHub read-only reuse audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_real_read_only_scan_reuse_audit_0272 import (  # noqa: E402
    GitHubReadOnlyScanAuditCommand,
    audit_github_real_read_only_scan_reuse,
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit existing GitHub surfaces before a real read-only issue scan."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--max-files", type=int, default=500)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    command = GitHubReadOnlyScanAuditCommand(
        repo_root=args.repo_root,
        max_files=args.max_files,
    )
    result = audit_github_real_read_only_scan_reuse(command)
    payload = result.to_json_dict()
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(args.output)
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(result.to_summary())
    return 0 if result.valid else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
