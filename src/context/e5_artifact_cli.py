from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from .e5_artifact_loader import build_e5_runtime_bridge_from_directory
from .e5_runtime_bridge import E5RuntimeBridgePolicy, E5RuntimeBridgeResult


@dataclass(frozen=True, slots=True)
class E5ArtifactContextRenderPolicy:
    """Politique de rendu CLI pour inspecter un InferenceContext E5 local."""

    output_format: str = "text"

    def __post_init__(self) -> None:
        if self.output_format not in {"text", "json"}:
            raise ValueError("output_format must be text or json")


@dataclass(frozen=True, slots=True)
class E5ArtifactContextCommand:
    """Commande typée pour charger un artifact-dir et afficher le contexte runtime."""

    artifact_dir: Path
    bridge_policy: E5RuntimeBridgePolicy = E5RuntimeBridgePolicy()
    render: E5ArtifactContextRenderPolicy = E5ArtifactContextRenderPolicy()

    def __post_init__(self) -> None:
        if not str(self.artifact_dir).strip():
            raise ValueError("artifact_dir must not be empty")


def build_e5_artifact_context_parser() -> argparse.ArgumentParser:
    """Construit le parser CLI de la bordure locale artifact-dir -> InferenceContext."""
    parser = argparse.ArgumentParser(
        prog="missipy-e5-artifact-context",
        description="Charge un artifact-dir E5 Phase 4 et affiche l'InferenceContext Phase 5.",
    )
    parser.add_argument("artifact_dir", help="Dossier contenant report.json, context.json, consumed_context.json et prompt.json.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Format de sortie.")
    parser.add_argument("--component-name", default="e5_local_context", help="Nom du composant dans InferenceContext.features.")
    parser.add_argument("--priority", type=int, default=20, help="Priorité associée au contexte E5.")
    parser.add_argument("--include-context-text", action="store_true", help="Inclut context_text dans la feature produite.")
    parser.add_argument("--hide-prompt-text", action="store_true", help="N'inclut pas prompt_text dans la feature produite.")
    return parser


def command_from_args(args: argparse.Namespace) -> E5ArtifactContextCommand:
    """Traduit argparse.Namespace en commande typée, à la frontière CLI uniquement."""
    if args.priority < 0:
        raise ValueError("--priority must not be negative")

    return E5ArtifactContextCommand(
        artifact_dir=Path(args.artifact_dir),
        bridge_policy=E5RuntimeBridgePolicy(
            component_name=args.component_name,
            priority=args.priority,
            include_prompt_text=not args.hide_prompt_text,
            include_context_text=args.include_context_text,
        ),
        render=E5ArtifactContextRenderPolicy(output_format=args.format),
    )


def run_e5_artifact_context(
    argv: list[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Point d'entrée testable : artifact-dir local -> rendu InferenceContext."""
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    parser = build_e5_artifact_context_parser()

    try:
        command = command_from_args(parser.parse_args(argv))
        result = build_e5_runtime_bridge_from_directory(
            command.artifact_dir,
            bridge_policy=command.bridge_policy,
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        err.write(f"missipy-e5-artifact-context failed: {exc}\n")
        return 1

    _write_output(out, command, result)
    return 0


def main() -> int:
    """Entrée console pour `python -m context.e5_artifact_cli`."""
    return run_e5_artifact_context()


def _write_output(out: TextIO, command: E5ArtifactContextCommand, result: E5RuntimeBridgeResult) -> None:
    payload = _payload(command, result)
    if command.render.output_format == "json":
        out.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        out.write("\n")
        return
    out.write(_to_text(payload))
    out.write("\n")


def _payload(command: E5ArtifactContextCommand, result: E5RuntimeBridgeResult) -> dict[str, object]:
    return {
        "schema": "missipy.e5.artifact_context_cli.v1",
        "artifact_dir": str(command.artifact_dir),
        "bridge": result.to_json_dict(),
    }


def _to_text(payload: dict[str, object]) -> str:
    bridge = payload["bridge"]
    if not isinstance(bridge, dict):
        raise TypeError("bridge payload must be a mapping")

    component = str(bridge.get("component_name", ""))
    features = bridge.get("features", {})
    feature: object = {}
    if isinstance(features, dict):
        feature = features.get(component, {})
    if not isinstance(feature, dict):
        feature = {}

    lines = [
        "schema: missipy.e5.artifact_context_cli.v1",
        f"artifact_dir: {payload['artifact_dir']}",
        f"component: {component}",
        f"status: {feature.get('status', '')}",
        f"query: {feature.get('query', '')}",
        f"hit_count: {feature.get('hit_count', 0)}",
        f"selected_item_count: {feature.get('selected_item_count', 0)}",
        f"prompt_chars: {feature.get('prompt_chars', 0)}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
