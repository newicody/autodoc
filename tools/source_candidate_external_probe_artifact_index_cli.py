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

from context.source_candidate_external_probe_artifact_index import (  # noqa: E402
    build_source_candidate_external_probe_artifact_index,
    render_source_candidate_external_probe_artifact_index,
    write_source_candidate_external_probe_artifact_index,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index local SourceCandidate external probe bundles.")
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    parser.add_argument("--scan-root", type=Path, required=True, help="directory containing probe bundles")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("doc/maintenance/source_candidate_external_probe_artifact_index.json"),
        help="index JSON output path",
    )
    parser.add_argument("--json", action="store_true", help="print JSON index")
    args = parser.parse_args(argv)

    index = build_source_candidate_external_probe_artifact_index(
        args.root,
        scan_root=args.scan_root,
    )
    write_source_candidate_external_probe_artifact_index(args.output, index)

    if args.json:
        print(json.dumps(index.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_source_candidate_external_probe_artifact_index(index))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
