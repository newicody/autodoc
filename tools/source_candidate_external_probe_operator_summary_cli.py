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

from context.source_candidate_external_probe_operator_summary import (  # noqa: E402
    build_source_candidate_external_probe_operator_summary_from_index_file,
    render_source_candidate_external_probe_operator_summary,
    write_source_candidate_external_probe_operator_summary,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize local SourceCandidate external probe bundle indexes.")
    parser.add_argument("--index", type=Path, required=True, help="external probe artifact index JSON")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("doc/maintenance/source_candidate_external_probe_operator_summary.json"),
        help="summary JSON output path",
    )
    parser.add_argument("--json", action="store_true", help="print JSON summary")
    args = parser.parse_args(argv)

    summary = build_source_candidate_external_probe_operator_summary_from_index_file(args.index)
    write_source_candidate_external_probe_operator_summary(args.output, summary)

    if args.json:
        print(json.dumps(summary.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_source_candidate_external_probe_operator_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
