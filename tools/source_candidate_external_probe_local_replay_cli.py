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

from context.source_candidate_external_probe_local_replay import (  # noqa: E402
    build_source_candidate_external_probe_local_replay_report,
    render_source_candidate_external_probe_local_replay_report,
    write_source_candidate_external_probe_local_replay_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay local SourceCandidate external probe audit events.")
    parser.add_argument(
        "--audit-log",
        type=Path,
        default=Path("doc/maintenance/source_candidate_external_probe_local_audit.jsonl"),
        help="local JSONL audit log path",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("doc/maintenance/source_candidate_external_probe_local_replay_report.json"),
        help="local replay report output path",
    )
    parser.add_argument("--limit", type=int, default=None, help="optional number of latest events to replay")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args(argv)

    report = build_source_candidate_external_probe_local_replay_report(
        args.audit_log,
        limit=args.limit,
    )
    write_source_candidate_external_probe_local_replay_report(args.report, report)

    if args.json:
        print(json.dumps(report.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_source_candidate_external_probe_local_replay_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
