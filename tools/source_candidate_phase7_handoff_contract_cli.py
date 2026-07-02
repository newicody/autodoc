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

from context.source_candidate_phase7_handoff_contract import (  # noqa: E402
    build_source_candidate_phase7_handoff_contract,
    build_source_candidate_phase7_handoff_contract_from_closure_report,
    render_source_candidate_phase7_handoff_contract,
    write_source_candidate_phase7_handoff_contract,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the local SourceCandidate Phase 7 handoff contract.")
    parser.add_argument(
        "--closure-report",
        type=Path,
        default=None,
        help="optional Phase 7 closure report JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("doc/maintenance/source_candidate_phase7_handoff_contract.json"),
        help="handoff contract JSON output path",
    )
    parser.add_argument("--next-phase", default="8", help="next phase label")
    parser.add_argument("--json", action="store_true", help="print JSON contract")
    args = parser.parse_args(argv)

    if args.closure_report is None:
        contract = build_source_candidate_phase7_handoff_contract(next_phase=args.next_phase)
    else:
        contract = build_source_candidate_phase7_handoff_contract_from_closure_report(
            args.closure_report,
            next_phase=args.next_phase,
        )

    write_source_candidate_phase7_handoff_contract(args.output, contract)

    if args.json:
        print(json.dumps(contract.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_source_candidate_phase7_handoff_contract(contract))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
