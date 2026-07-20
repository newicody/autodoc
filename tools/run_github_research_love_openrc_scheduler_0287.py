#!/usr/bin/env python3
"""Run the explicit externally-managed GitHub research Scheduler service."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Callable, Mapping
from importlib import import_module
import inspect
import json
import os
from pathlib import Path
import signal
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
for _path in (str(SRC_ROOT), str(ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from context.github_research_love_openrc_scheduler_service_0287 import (  # noqa: E402
    GitHubResearchLoveOpenRcSchedulerServiceError,
    GitHubResearchLoveOpenRcServiceBundle,
)

DEFAULT_RUNTIME_CONFIG = ROOT / ".var/config/love_installed_runtime.ini"
FACTORY_ENV = "AUTODOC_GITHUB_RESEARCH_OPENRC_SERVICE_FACTORY"
CONFIG_ENV = "AUTODOC_LOVE_INSTALLED_RUNTIME_CONFIG"


class OpenRcSchedulerServiceCliError(RuntimeError):
    """Operator-facing service bootstrap error."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--factory", default=os.environ.get(FACTORY_ENV, ""))
    parser.add_argument(
        "--config",
        default=os.environ.get(CONFIG_ENV, str(DEFAULT_RUNTIME_CONFIG)),
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args()


def _load_factory(reference: str) -> Callable[..., object]:
    module_name, separator, function_name = reference.partition(":")
    if not separator or not module_name.strip() or not function_name.strip():
        raise OpenRcSchedulerServiceCliError(
            f"{FACTORY_ENV} doit utiliser module:function"
        )
    try:
        module = import_module(module_name.strip())
    except Exception as exc:
        raise OpenRcSchedulerServiceCliError(
            f"impossible d'importer la fabrique {module_name.strip()}"
        ) from exc
    factory = getattr(module, function_name.strip(), None)
    if factory is None or not callable(factory):
        raise OpenRcSchedulerServiceCliError(
            "la fabrique OpenRC configurée n'est pas callable"
        )
    return factory


def _supported_keywords(
    factory: Callable[..., object],
    available: Mapping[str, object],
) -> Mapping[str, object]:
    try:
        signature = inspect.signature(factory)
    except (TypeError, ValueError):
        return available
    if any(
        value.kind is inspect.Parameter.VAR_KEYWORD
        for value in signature.parameters.values()
    ):
        return available
    supported = {
        name
        for name, value in signature.parameters.items()
        if value.kind
        in {
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }
    }
    return {name: value for name, value in available.items() if name in supported}


def _build_bundle(args: argparse.Namespace) -> GitHubResearchLoveOpenRcServiceBundle:
    reference = str(args.factory).strip()
    if not reference:
        raise OpenRcSchedulerServiceCliError(
            f"fabrique absente: définir {FACTORY_ENV} ou --factory"
        )
    config_path = Path(args.config).expanduser().resolve()
    if not config_path.is_file():
        raise OpenRcSchedulerServiceCliError(
            f"configuration runtime introuvable: {config_path}"
        )
    factory = _load_factory(reference)
    bundle = factory(
        **_supported_keywords(
            factory,
            {
                "config_path": config_path,
                "environment": os.environ,
            },
        )
    )
    if not isinstance(bundle, GitHubResearchLoveOpenRcServiceBundle):
        raise OpenRcSchedulerServiceCliError(
            "la fabrique doit retourner GitHubResearchLoveOpenRcServiceBundle"
        )
    return bundle


def _install_signal_handlers(stop_event: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signum, stop_event.set)
        except (NotImplementedError, RuntimeError):
            signal.signal(signum, lambda _signum, _frame: stop_event.set())


def _emit(payload: Mapping[str, object], *, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(dict(payload), indent=2, sort_keys=True))
        return
    print(
        "openrc_scheduler_service_status="
        f"{payload.get('status', 'ready')} "
        f"service_ref={payload.get('service_ref', '-')} "
        f"scheduler_ref={payload.get('scheduler_ref', '-')} "
        f"ticks={payload.get('tick_count', 0)} "
        f"running_after={payload.get('running_after', False)}"
    )


async def _run(args: argparse.Namespace) -> int:
    bundle = _build_bundle(args)
    payload: Mapping[str, object]
    if args.check:
        payload = {
            "status": "ready",
            **dict(bundle.to_mapping()),
        }
    else:
        stop_event = asyncio.Event()
        _install_signal_handlers(stop_event)
        receipt = await bundle.service.run(stop_event)
        payload = dict(receipt.to_mapping())

    close_errors = await bundle.close()
    if close_errors:
        print(
            "openrc scheduler backend close errors: " + ",".join(close_errors),
            file=sys.stderr,
        )
        return 3
    _emit(payload, output_format=args.format)
    return 0


def main() -> int:
    args = parse_args()
    try:
        return asyncio.run(_run(args))
    except (
        GitHubResearchLoveOpenRcSchedulerServiceError,
        OpenRcSchedulerServiceCliError,
        ValueError,
        TypeError,
    ) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
