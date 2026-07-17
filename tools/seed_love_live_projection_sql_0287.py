#!/usr/bin/env python3
"""Preview or execute the SQL-only seed required by the live projection probe."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.love_controlled_sql_projection_seed_0287 import (  # noqa: E402
    LoveControlledSqlProjectionSeedGate,
    build_love_controlled_sql_projection_seed_plan,
    execute_love_controlled_sql_projection_seed,
    inspect_love_controlled_sql_projection_seed,
)
from context.love_manual_runtime_configuration_0287 import (  # noqa: E402
    load_manual_installed_runtime_settings,
)
from context.love_postgresql_authority_binding_0287 import (  # noqa: E402
    open_love_postgresql_authority,
)

SQL_SEED_WRITE_ENV = "AUTODOC_SQL_PROJECTION_SEED_WRITE_ALLOWED"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or execute the deterministic SQL-only object and accepted "
            "child revision required by the first live Qdrant projection probe."
        )
    )
    parser.add_argument(
        "--config",
        default=".var/config/love_installed_runtime.ini",
    )
    parser.add_argument(
        "--policy-decision-id",
        default="policy:love-controlled-sql-seed-preview",
    )
    parser.add_argument(
        "--operator-decision",
        choices=("approve", "reject"),
        default="reject",
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-plan-digest", default="")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser


def _truthy(value: str) -> bool:
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_manual_installed_runtime_settings(args.config)
    plan = build_love_controlled_sql_projection_seed_plan(
        parent_revision_ref=settings.base_revision_ref,
    )
    write_allowed = _truthy(os.environ.get(SQL_SEED_WRITE_ENV, ""))

    authority_binding = open_love_postgresql_authority(settings)
    try:
        readiness = inspect_love_controlled_sql_projection_seed(
            authority_binding.authority_store,
            plan,
        )
        execution = None
        if args.execute:
            gate = LoveControlledSqlProjectionSeedGate(
                policy_decision_id=args.policy_decision_id,
                operator_decision=args.operator_decision,
                allow_write=write_allowed,
                confirm_plan_digest=args.confirm_plan_digest,
            )
            execution = execute_love_controlled_sql_projection_seed(
                authority_binding.authority_store,
                plan,
                gate,
            )
        payload = {
            "plan": plan.to_mapping(),
            "readiness": readiness.to_mapping(),
            "execution": execution.to_mapping() if execution else None,
            "boundaries": {
                "execute_requested": bool(args.execute),
                "sql_seed_write_environment_allowed": write_allowed,
                "base_revision_mutated": False,
                "qdrant_client_constructed": False,
                "qdrant_write_performed": False,
                "openvino_constructed": False,
                "openvino_inference_performed": False,
                "scheduler_constructed": False,
                "authoritative_body_serialized_in_execution_receipt": False,
                "secret_value_serialized": False,
            },
        }
    finally:
        authority_binding.close()

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            " ".join(
                (
                    f"plan_digest={plan.plan_digest}",
                    f"ready={readiness.ready}",
                    f"object_state={readiness.object_state}",
                    f"revision_state={readiness.revision_state}",
                    f"execute={bool(args.execute)}",
                    f"seeded={execution is not None}",
                    "qdrant_write_performed=False",
                    "sql_remains_authority=True",
                )
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
