#!/usr/bin/env python3
"""Build the Scheduler runtime bootstrap registry attachment report."""

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

from context.scheduler_runtime_bootstrap_registry_attachment_0258 import (  # noqa: E402
    build_scheduler_runtime_bootstrap_attachment,
    load_registry_payload,
    write_scheduler_runtime_bootstrap_attachment_report,
)


DEFAULT_REGISTRY = ROOT / ".var/reports/scheduler_owned_runtime_registry_0257.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--output", default="")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry_payload = load_registry_payload(Path(args.registry))

    if args.output:
        payload = write_scheduler_runtime_bootstrap_attachment_report(
            Path(args.output),
            registry_payload,
        )
    else:
        payload = build_scheduler_runtime_bootstrap_attachment(registry_payload).to_dict()

    if args.format == "summary":
        attachment = payload["attachment"]
        print(
            "scheduler_runtime_bootstrap_registry_attachment_valid="
            f"{payload['valid']} issues={len(payload['issues'])} "
            f"dry_run={payload['dry_run']} "
            f"components={','.join(attachment['registry_component_ids'])}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
