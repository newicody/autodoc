#!/usr/bin/env python3
"""Bind existing DbApiSqlContextStore to Scheduler-managed SQL usage."""

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

from context.scheduler_managed_db_api_sql_context_store_binding_0260 import (  # noqa: E402
    load_json_payload,
    run_scheduler_managed_db_api_sql_context_store_binding,
)


DEFAULT_BOOTSTRAP = ROOT / ".var/reports/scheduler_runtime_bootstrap_registry_attachment_0258.json"
DEFAULT_DB_PATH = ROOT / ".var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--bootstrap", default=str(DEFAULT_BOOTSTRAP))
    parser.add_argument("--output", default="")
    parser.add_argument("--text", default="passage: Scheduler-managed DbApiSqlContextStore binding smoke")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    bootstrap_payload = load_json_payload(Path(args.bootstrap))
    result = run_scheduler_managed_db_api_sql_context_store_binding(
        root,
        bootstrap_payload,
        text=args.text,
        execute=args.execute,
        policy_decision_id=args.policy_decision_id,
        db_path=Path(args.db_path) if args.db_path else None,
    )
    payload = result.to_dict()

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "summary":
        binding = payload["binding"]
        usage = payload["usage"]
        selected = binding["selected_candidate"]["module_name"] if binding["selected_candidate"] else "-"
        issue_count = len(binding["issues"]) + len(usage.get("issues", []))
        print(
            "scheduler_managed_db_api_sql_context_store_binding_valid="
            f"{payload['valid']} binding_valid={binding['valid']} "
            f"candidates={binding['candidate_count']} selected={selected} "
            f"constructed={binding['constructed']} execute={usage.get('execute')} "
            f"sql_ref={usage.get('sql_ref', '-') or '-'} issues={issue_count}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
