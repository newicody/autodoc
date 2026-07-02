#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.source_candidate_phase7_closure_report import (  # noqa: E402
    build_source_candidate_phase7_closure_report,
    render_source_candidate_phase7_closure_report,
    write_source_candidate_phase7_closure_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the local SourceCandidate Phase 7 closure report.")
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("doc/maintenance/source_candidate_phase7_closure_report.json"),
        help="closure report JSON output path",
    )
    parser.add_argument("--json", action="store_true", help="print JSON report")
    parser.add_argument("--strict", action="store_true", help="return non-zero when required artifacts are missing")
    args = parser.parse_args(argv)

    report = build_source_candidate_phase7_closure_report(args.root)
    write_source_candidate_phase7_closure_report(args.output, report)

    if args.json:
        print(json.dumps(report.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_source_candidate_phase7_closure_report(report))

    if args.strict and report.missing_count:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
