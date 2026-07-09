#!/usr/bin/env python3
"""Build a phase 0250 Scheduler intention event envelope."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for _path in (str(SRC_ROOT), str(REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from context.prod_server_scheduler_intention_event_emission_0250 import (  # noqa: E402
    SCHEDULER_INTENTION_EVENT_EMISSION_BOUNDARY,
    event_envelope_from_intention,
    sample_scheduler_intention,
    scheduler_intention_event_emission_to_dict,
    write_scheduler_intention_event_emission_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server-config", default="doc/examples/autodoc_prod_server_initial_0241.ini")
    parser.add_argument("--openvino-config", default="doc/examples/autodoc_openvino_embedding_e5_small_0246.ini")
    parser.add_argument(
        "--output",
        default=".var/reports/prod_server_scheduler_intention_event_emission_0250.json",
    )
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server_config_path = Path(args.server_config)
    openvino_config_path = Path(args.openvino_config)
    output_path = Path(args.output)

    if args.check_only:
        report = event_envelope_from_intention(
            sample_scheduler_intention(),
            server_config_path=server_config_path,
            openvino_config_path=openvino_config_path,
        )
        payload = {
            "production_server_scheduler_intention_event_emission_valid": report.valid,
            "scheduler_intention_event_emission": scheduler_intention_event_emission_to_dict(report),
            "boundary": dict(SCHEDULER_INTENTION_EVENT_EMISSION_BOUNDARY),
        }
    else:
        payload = write_scheduler_intention_event_emission_report(
            server_config_path=server_config_path,
            openvino_config_path=openvino_config_path,
            output_path=output_path,
        )
        report = event_envelope_from_intention(
            sample_scheduler_intention(),
            server_config_path=server_config_path,
            openvino_config_path=openvino_config_path,
        )

    if args.format == "summary":
        issue_count = len(report.issues)
        event_id = report.envelope.event_id if report.envelope is not None else "missing"
        if args.check_only:
            print(
                "production_server_scheduler_intention_event_emission_valid="
                f"{str(report.valid)} issues={issue_count} event_id={event_id}"
            )
        else:
            print(
                "production_server_scheduler_intention_event_emission_written=True "
                f"valid={str(report.valid)} issues={issue_count} output={output_path}"
            )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
