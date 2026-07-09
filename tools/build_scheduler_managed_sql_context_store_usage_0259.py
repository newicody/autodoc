#!/usr/bin/env python3
"""Build the Scheduler-managed SQLContextStore usage report."""

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

from context.scheduler_managed_sql_context_store_usage_0259 import (  # noqa: E402
    load_bootstrap_attachment_payload,
    run_scheduler_managed_sql_context_store_usage,
)


DEFAULT_BOOTSTRAP = ROOT / ".var/reports/scheduler_runtime_bootstrap_registry_attachment_0258.json"


class DemoExistingSqlContextStore:
    """Small smoke-only existing-store stand-in; not a runtime SQL implementation."""

    def controlled_write(self, payload):
        return {
            "sql_ref": "sql:demo/" + str(payload["intent_id"]).split(":")[-1],
            "selected_store_class": "DemoExistingSqlContextStore",
            "request_table": payload["table"],
            "request_operation": payload["operation"],
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", default=str(DEFAULT_BOOTSTRAP))
    parser.add_argument("--output", default="")
    parser.add_argument("--text", default="passage: Scheduler-managed SQLContextStore usage smoke")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--demo-existing-store", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bootstrap_payload = load_bootstrap_attachment_payload(Path(args.bootstrap))
    store = DemoExistingSqlContextStore() if args.demo_existing_store else None
    result = run_scheduler_managed_sql_context_store_usage(
        bootstrap_payload,
        text=args.text,
        execute=args.execute,
        policy_decision_id=args.policy_decision_id,
        store=store,
    )
    payload = result.to_dict()

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "summary":
        print(
            "scheduler_managed_sql_context_store_usage_valid="
            f"{payload['valid']} issues={len(payload['issues'])} "
            f"execute={payload['execute']} dry_run={payload['dry_run']} "
            f"sql_ref={payload['sql_ref'] or '-'}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
