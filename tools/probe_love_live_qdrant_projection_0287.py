#!/usr/bin/env python3
"""Preview or execute one controlled SQL -> E5 -> Qdrant projection probe."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.love_live_qdrant_projection_probe_0287 import (  # noqa: E402
    LoveLiveProjectionProbeGate,
    LoveLiveProjectionProbeRequest,
    build_love_live_projection_probe_plan,
    execute_love_live_projection_probe,
    inspect_love_live_projection_probe,
)
from context.love_manual_runtime_configuration_0287 import (  # noqa: E402
    load_manual_installed_runtime_settings,
)
from context.love_postgresql_authority_binding_0287 import (  # noqa: E402
    open_love_postgresql_authority,
)
from context.love_qdrant_live_analysis_projection_0287 import (  # noqa: E402
    LoveQdrantLiveAnalysisProjection,
    LoveQdrantLiveAnalysisProjectionSettings,
)
from inference.e5_pipeline import (  # noqa: E402
    MultilingualE5SmallPipelineConfig,
    build_multilingual_e5_small_pipeline,
)
from inference.e5_profile import MultilingualE5SmallLocalConfig  # noqa: E402
from inference.qdrant_client_projection_executor import (  # noqa: E402
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
    build_qdrant_client_projection_executor,
)

POINT_WRITE_ENV = "AUTODOC_QDRANT_POINT_WRITE_ALLOWED"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or execute one real SQL-authoritative analysis projection "
            "through OpenVINO E5 and the canonical named Qdrant collection."
        )
    )
    parser.add_argument(
        "--config",
        default=".var/config/love_installed_runtime.ini",
    )
    parser.add_argument("--object-ref", required=True)
    parser.add_argument("--revision-ref", required=True)
    parser.add_argument("--branch-ref", required=True)
    parser.add_argument("--project-ref", required=True)
    parser.add_argument("--conversation-ref", required=True)
    parser.add_argument("--specialist-ref", required=True)
    parser.add_argument("--laboratory-ref", required=True)
    parser.add_argument("--security-scope", required=True)
    parser.add_argument("--projected-at", default="")
    parser.add_argument(
        "--policy-decision-id",
        default="policy:love-live-projection-preview",
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
    qdrant = settings.qdrant
    request = LoveLiveProjectionProbeRequest(
        object_ref=args.object_ref,
        revision_ref=args.revision_ref,
        branch_ref=args.branch_ref,
        project_ref=args.project_ref,
        conversation_ref=args.conversation_ref,
        specialist_ref=args.specialist_ref,
        laboratory_ref=args.laboratory_ref,
        security_scope=args.security_scope,
        projected_at=args.projected_at,
    )
    plan = build_love_live_projection_probe_plan(
        request,
        collection_name=qdrant.physical_collection,
        dense_vector_name=qdrant.dense_vector_name,
        sparse_vector_name=qdrant.sparse_vector_name,
        model_ref=settings.model_ref,
        model_revision=settings.model_revision,
        dimension=settings.openvino.dimension,
    )
    write_allowed = _truthy(os.environ.get(POINT_WRITE_ENV, ""))
    authority_binding = open_love_postgresql_authority(settings)
    executor = None
    try:
        readiness = inspect_love_live_projection_probe(
            authority_binding.authority_store,
            plan,
        )
        execution = None
        if args.execute:
            gate = LoveLiveProjectionProbeGate(
                policy_decision_id=args.policy_decision_id,
                operator_decision=args.operator_decision,
                allow_write=write_allowed,
                confirm_plan_digest=args.confirm_plan_digest,
            )
            gate.require_allows(plan)
            if not readiness.ready:
                raise RuntimeError(
                    "live projection readiness failed: "
                    + "; ".join(readiness.issues)
                )

            local = MultilingualE5SmallLocalConfig(
                model_dir=settings.openvino.model_dir,
                device=settings.openvino.device,
            )
            e5_bundle = build_multilingual_e5_small_pipeline(
                MultilingualE5SmallPipelineConfig(
                    local=local,
                    require_model_exists=True,
                )
            )
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
                allow_write=True,
                allow_search=True,
            )
            api_key = (
                os.environ.get(qdrant.api_key_env, "")
                if qdrant.api_key_env
                else ""
            )
            executor = build_qdrant_client_projection_executor(
                connection,
                effect_gate,
                api_key=api_key or None,
            )
            projector = LoveQdrantLiveAnalysisProjection(
                pipeline=e5_bundle.pipeline,
                writer=executor,
                settings=LoveQdrantLiveAnalysisProjectionSettings(
                    collection_name=qdrant.physical_collection,
                    dense_vector_name=qdrant.dense_vector_name,
                    sparse_vector_name=qdrant.sparse_vector_name,
                    model_ref=settings.model_ref,
                    model_revision=settings.model_revision,
                    passage_prefix=settings.openvino.passage_prefix,
                    dimension=settings.openvino.dimension,
                ),
            )
            execution = asyncio.run(
                execute_love_live_projection_probe(
                    authority_binding.authority_store,
                    projector,
                    executor,
                    plan,
                    gate,
                )
            )

        payload = {
            "plan": plan.to_mapping(),
            "readiness": readiness.to_mapping(),
            "execution": execution.to_mapping() if execution else None,
            "boundaries": {
                "execute_requested": bool(args.execute),
                "point_write_environment_allowed": write_allowed,
                "preview_constructed_openvino": False,
                "preview_constructed_qdrant_client": False,
                "secret_value_serialized": False,
                "vectors_serialized": False,
                "authoritative_body_serialized": False,
                "delete_performed": False,
                "alias_mutated": False,
            },
        }
    finally:
        if executor is not None:
            executor.close()
        authority_binding.close()

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            " ".join(
                (
                    f"plan_digest={plan.plan_digest}",
                    f"ready={readiness.ready}",
                    f"execute={bool(args.execute)}",
                    f"projected={execution is not None}",
                    "vectors_serialized=False",
                    "sql_remains_authority=True",
                )
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
