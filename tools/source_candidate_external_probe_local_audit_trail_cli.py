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

from context.source_candidate_external_probe_local_audit_trail import (  # noqa: E402
    build_source_candidate_external_probe_local_audit_report,
    record_source_candidate_external_probe_operator_summary,
    render_source_candidate_external_probe_local_audit_report,
    write_source_candidate_external_probe_local_audit_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record local SourceCandidate external probe audit events.")
    parser.add_argument("--summary", type=Path, required=True, help="operator summary JSON")
    parser.add_argument(
        "--audit-log",
        type=Path,
        default=Path("doc/maintenance/source_candidate_external_probe_local_audit.jsonl"),
        help="local JSONL audit log path",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("doc/maintenance/source_candidate_external_probe_local_audit_report.json"),
        help="local audit report output path",
    )
    parser.add_argument("--created-at", default=None, help="optional deterministic timestamp")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args(argv)

    record_source_candidate_external_probe_operator_summary(
        audit_log_path=args.audit_log,
        summary_path=args.summary,
        created_at=args.created_at,
    )
    report = build_source_candidate_external_probe_local_audit_report(args.audit_log)
    write_source_candidate_external_probe_local_audit_report(args.report, report)

    if args.json:
        print(json.dumps(report.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_source_candidate_external_probe_local_audit_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
