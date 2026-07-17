#!/usr/bin/env python3
"""Check manual PostgreSQL/Qdrant/OpenVINO readiness without writes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.love_manual_runtime_configuration_0287 import (  # noqa: E402
    ManualRuntimeConfigurationError,
    load_manual_installed_runtime_settings,
)
from context.love_manual_runtime_readiness_0287 import (  # noqa: E402
    inspect_manual_runtime_readiness,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the installed PostgreSQL, Qdrant and OpenVINO E5-384 "
            "configuration without SQL/Qdrant writes or model inference."
        )
    )
    parser.add_argument("--config", help="manual runtime INI path")
    parser.add_argument(
        "--skip-openvino-compile",
        action="store_true",
        help="read the OpenVINO model without compiling it",
    )
    parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="json",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        settings = load_manual_installed_runtime_settings(args.config)
        report = inspect_manual_runtime_readiness(
            settings,
            compile_openvino_model=not args.skip_openvino_compile,
        )
        payload = {
            "configuration": dict(settings.to_public_mapping()),
            "readiness": report.to_mapping(),
        }
    except ManualRuntimeConfigurationError as exc:
        payload = {
            "configuration": None,
            "readiness": {
                "valid": False,
                "issues": [str(exc)],
                "boundaries": {
                    "secret_value_serialized": False,
                    "write_performed": False,
                },
            },
        }
        report = None

    if args.format == "summary":
        if report is None:
            print("manual_runtime_valid=False configuration_error=True")
        else:
            print(report.to_summary())
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report is not None and report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
