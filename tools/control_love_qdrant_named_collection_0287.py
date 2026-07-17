#!/usr/bin/env python3
"""Preview or execute controlled creation of the hybrid Qdrant collection."""

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

from context.love_manual_runtime_configuration_0287 import (  # noqa: E402
    load_manual_installed_runtime_settings,
)
from context.love_qdrant_named_collection_control_0287 import (  # noqa: E402
    LoveQdrantNamedCollectionMutationGate,
    build_love_qdrant_named_collection_plan,
    execute_love_qdrant_named_collection_plan,
    inspect_love_qdrant_named_collection,
)
from inference.qdrant_client_named_collection_admin_0287 import (  # noqa: E402
    build_qdrant_client_named_collection_admin,
)
from inference.qdrant_client_projection_executor import (  # noqa: E402
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
)


MUTATION_ENV = "AUTODOC_QDRANT_COLLECTION_MUTATION_ALLOWED"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or create the canonical named dense+sparse Qdrant "
            "collection without deleting or switching aliases."
        )
    )
    parser.add_argument(
        "--config",
        default=".var/config/love_installed_runtime.ini",
    )
    parser.add_argument(
        "--policy-decision-id",
        default="policy:qdrant-named-collection-preview",
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
    plan = build_love_qdrant_named_collection_plan(settings)
    qdrant = settings.qdrant
    mutation_allowed = _truthy(os.environ.get(MUTATION_ENV, ""))
    connection = QdrantClientConnectionConfig(
        url=qdrant.url,
        timeout_seconds=qdrant.timeout_seconds,
        grpc_port=qdrant.grpc_port,
        prefer_grpc=False,
        wait_for_write=True,
        check_compatibility=True,
    )
    effect_gate = QdrantClientEffectGate(
        policy_decision_id=args.policy_decision_id,
        allow_write=bool(args.execute and mutation_allowed),
        allow_search=False,
    )
    api_key = (
        os.environ.get(qdrant.api_key_env, "")
        if qdrant.api_key_env
        else ""
    )
    admin = build_qdrant_client_named_collection_admin(
        connection,
        effect_gate,
        api_key=api_key or None,
    )
    try:
        readiness = inspect_love_qdrant_named_collection(admin, plan)
        execution = None
        if args.execute:
            gate = LoveQdrantNamedCollectionMutationGate(
                policy_decision_id=args.policy_decision_id,
                operator_decision=args.operator_decision,
                allow_create=mutation_allowed,
                confirm_plan_digest=args.confirm_plan_digest,
            )
            execution = execute_love_qdrant_named_collection_plan(
                admin,
                plan,
                gate,
            )
        payload = {
            "plan": plan.to_mapping(),
            "readiness": readiness.to_mapping(),
            "execution": (
                execution.to_mapping() if execution is not None else None
            ),
            "boundaries": {
                "execute_requested": bool(args.execute),
                "mutation_environment_allowed": mutation_allowed,
                "api_key_serialized": False,
                "point_write_performed": False,
                "alias_mutated": False,
                "delete_performed": False,
            },
        }
    finally:
        admin.close()

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            " ".join(
                (
                    f"plan_digest={plan.plan_digest}",
                    f"ready={readiness.valid}",
                    f"execute={bool(args.execute)}",
                    f"created={bool(execution and execution.created_collection)}",
                    "alias_mutated=False",
                    "delete_performed=False",
                )
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# r10-r1 preserves preview-first CLI behavior.
