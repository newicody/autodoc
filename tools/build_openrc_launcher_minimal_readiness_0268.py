#!/usr/bin/env python3
"""Build OpenRC launcher minimal readiness from closed frame artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
for _path in (str(SRC_ROOT), str(ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from context.openrc_launcher_minimal_readiness_0268 import (  # noqa: E402
    OpenRcLauncherMinimalReadinessRequest,
    build_openrc_launcher_minimal_readiness,
    load_json,
    write_report,
)


DEFAULT_CLOSED_FRAME_REPORT = ROOT / ".var/reports/scheduler_managed_closed_result_frame_0264.json"
DEFAULT_GITHUB_HANDOFF = ROOT / ".var/reports/github_scan_once_handoff_0267.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closed-frame-report", default=str(DEFAULT_CLOSED_FRAME_REPORT))
    parser.add_argument("--github-handoff", default=str(DEFAULT_GITHUB_HANDOFF))
    parser.add_argument("--service-name", default="autodoc-local-runtime")
    parser.add_argument("--repository", default="newicody/autodoc")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--install-service", action="store_true")
    parser.add_argument("--start-service", action="store_true")
    parser.add_argument("--enable-service", action="store_true")
    parser.add_argument("--output", default="")
    parser.add_argument("--script-output", default="")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    closed_path = Path(args.closed_frame_report)
    handoff_path = Path(args.github_handoff)
    request = OpenRcLauncherMinimalReadinessRequest(
        service_name=args.service_name,
        repository=args.repository,
        policy_decision_id=args.policy_decision_id,
        install_service=args.install_service,
        start_service=args.start_service,
        enable_service=args.enable_service,
    )
    report = build_openrc_launcher_minimal_readiness(
        closed_frame=load_json(closed_path),
        github_handoff=load_json(handoff_path),
        request=request,
        source_reports={
            "closed_frame_report": str(closed_path),
            "github_scan_once_handoff": str(handoff_path),
        },
    )
    payload = report.to_mapping()

    if args.output:
        write_report(Path(args.output), payload)
    if args.script_output:
        script_path = Path(args.script_output)
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(report.rendered_openrc_script, encoding="utf-8")

    if args.format == "summary":
        print(
            "openrc_launcher_minimal_readiness_valid="
            f"{payload['valid']} issues={len(payload['issues'])} "
            f"readiness_ref={payload.get('readiness_ref') or '-'} "
            f"service={payload['service_spec']['service_name']} "
            f"readiness_only={payload['readiness_only']} "
            f"starts_postgresql={payload['starts_postgresql']} "
            f"starts_openvino={payload['starts_openvino']} "
            f"starts_qdrant={payload['starts_qdrant']} "
            f"calls_rc_service={payload['calls_rc_service']}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
