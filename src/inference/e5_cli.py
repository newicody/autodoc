from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from io import TextIOBase
from typing import Protocol

from .e5_pipeline import (
    MultilingualE5SmallPipelineBundle,
    MultilingualE5SmallPipelineConfig,
    build_multilingual_e5_small_pipeline,
)
from .e5_profile import MULTILINGUAL_E5_SMALL_ENV, MultilingualE5SmallLocalConfig
from .e5_text import ensure_e5_text
from .embedding_pipeline import OpenVINOEmbeddingPipelineResult


class E5PipelineBuilder(Protocol):
    """Fonction injectable qui construit un bundle E5 exécutable."""

    def __call__(self, config: MultilingualE5SmallPipelineConfig) -> MultilingualE5SmallPipelineBundle:
        """Construit le pipeline depuis une configuration explicite."""


@dataclass(frozen=True, slots=True)
class E5CliOutput:
    """Projection stable d'un résultat embedding vers la CLI."""

    text: str
    model: str
    backend: str
    tokenizer: str
    dimension: int
    normalized: bool
    l2_norm: float
    values_preview: tuple[float, ...]
    values: tuple[float, ...] | None
    model_path: str
    device: str

    @classmethod
    def from_result(
        cls,
        result: OpenVINOEmbeddingPipelineResult,
        bundle: MultilingualE5SmallPipelineBundle,
        *,
        preview_size: int,
        include_values: bool,
    ) -> E5CliOutput:
        """Construit une sortie CLI depuis le résultat pipeline."""

        if preview_size < 0:
            raise ValueError("preview_size must be >= 0")
        values = result.vector.values
        return cls(
            text=result.text,
            model=result.model,
            backend=result.backend,
            tokenizer=result.tokenizer_name,
            dimension=result.vector.dimension,
            normalized=result.vector.normalized,
            l2_norm=result.vector.l2_norm,
            values_preview=tuple(values[:preview_size]),
            values=values if include_values else None,
            model_path=bundle.summary.model_path,
            device=bundle.summary.device,
        )

    def to_json_dict(self) -> dict[str, object]:
        """Convertit la sortie vers un objet JSON stable."""

        payload: dict[str, object] = {
            "text": self.text,
            "model": self.model,
            "backend": self.backend,
            "tokenizer": self.tokenizer,
            "dimension": self.dimension,
            "normalized": self.normalized,
            "l2_norm": self.l2_norm,
            "values_preview": list(self.values_preview),
            "model_path": self.model_path,
            "device": self.device,
        }
        if self.values is not None:
            payload["values"] = list(self.values)
        return payload

    def to_text(self) -> str:
        """Produit une sortie texte lisible pour le développement."""

        preview = ", ".join(f"{value:.8f}" for value in self.values_preview)
        return "\n".join(
            (
                f"model: {self.model}",
                f"backend: {self.backend}",
                f"tokenizer: {self.tokenizer}",
                f"device: {self.device}",
                f"model_path: {self.model_path}",
                f"dimension: {self.dimension}",
                f"normalized: {self.normalized}",
                f"l2_norm: {self.l2_norm:.8f}",
                f"values_preview: [{preview}]",
            )
        )


def build_parser() -> argparse.ArgumentParser:
    """Construit le parser CLI du test embedding E5 local."""

    parser = argparse.ArgumentParser(
        prog="missipy-embed-e5",
        description="Calcule un embedding local multilingual-e5-small via OpenVINO.",
    )
    parser.add_argument(
        "text",
        help=(
            "Texte à encoder. Si le préfixe E5 'query:' ou 'passage:' est absent, "
            "--role est appliqué."
        ),
    )
    parser.add_argument(
        "--role",
        choices=("auto", "query", "passage"),
        default="auto",
        help=(
            "Rôle E5 à appliquer au texte brut. 'auto' respecte un préfixe existant "
            "et applique 'query:' par défaut."
        ),
    )
    parser.add_argument(
        "--model-dir",
        default=None,
        help=(
            "Dossier du modèle OpenVINO exporté. Par défaut: variable "
            f"{MULTILINGUAL_E5_SMALL_ENV} ou chemin local configuré."
        ),
    )
    parser.add_argument("--device", default="CPU", help="Device OpenVINO, par exemple CPU ou GPU.")
    parser.add_argument("--max-length", type=int, default=128, help="Longueur maximale de tokenization.")
    parser.add_argument("--preview", type=int, default=8, help="Nombre de valeurs du vecteur à afficher.")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Format de sortie.",
    )
    parser.add_argument(
        "--full-vector",
        action="store_true",
        help="Inclure le vecteur complet en JSON. Ignoré en sortie text.",
    )
    return parser


async def run_async(
    argv: Sequence[str],
    *,
    stdout: TextIOBase,
    stderr: TextIOBase,
    builder: E5PipelineBuilder = build_multilingual_e5_small_pipeline,
) -> int:
    """Exécute la CLI avec une factory injectable pour les tests."""

    parser = build_parser()
    args = parser.parse_args(list(argv))

    if args.max_length <= 0:
        stderr.write("--max-length must be positive\n")
        return 2
    if args.preview < 0:
        stderr.write("--preview must be >= 0\n")
        return 2

    config = MultilingualE5SmallPipelineConfig(
        local=MultilingualE5SmallLocalConfig(
            model_dir=args.model_dir,
            device=args.device,
            max_length=args.max_length,
        ),
        require_model_exists=True,
        metadata={"cli": "missipy-embed-e5"},
    )

    try:
        bundle = builder(config)
        role = "query" if args.role == "auto" else args.role
        e5_text = ensure_e5_text(args.text, default_role=role)
        result = await bundle.pipeline.embed_text(e5_text.prefixed)
    except Exception as exc:  # pragma: no cover - message dépend des dépendances locales.
        stderr.write(f"missipy-embed-e5 failed: {exc}\n")
        return 1

    output = E5CliOutput.from_result(
        result,
        bundle,
        preview_size=args.preview,
        include_values=args.full_vector and args.format == "json",
    )
    if args.format == "json":
        stdout.write(json.dumps(output.to_json_dict(), ensure_ascii=False, sort_keys=True))
        stdout.write("\n")
    else:
        stdout.write(output.to_text())
        stdout.write("\n")
    return 0


def run(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIOBase | None = None,
    stderr: TextIOBase | None = None,
    builder: E5PipelineBuilder = build_multilingual_e5_small_pipeline,
) -> int:
    """Point d'entrée testable synchrone."""

    return asyncio.run(
        run_async(
            tuple(argv if argv is not None else sys.argv[1:]),
            stdout=stdout or sys.stdout,
            stderr=stderr or sys.stderr,
            builder=builder,
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée console."""

    return run(argv)


if __name__ == "__main__":  # pragma: no cover - délégation CLI.
    raise SystemExit(main())
