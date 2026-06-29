from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from io import TextIOBase
from pathlib import Path
from typing import Protocol

from .e5_pipeline import (
    MultilingualE5SmallPipelineBundle,
    MultilingualE5SmallPipelineConfig,
    build_multilingual_e5_small_pipeline,
)
from .e5_profile import MULTILINGUAL_E5_SMALL_ENV, MultilingualE5SmallLocalConfig
from .e5_ranker import E5LocalRanker, E5RankedResults
from .e5_text import ensure_e5_text


class E5RankPipelineBuilder(Protocol):
    """Fonction injectable qui construit un bundle E5 exécutable."""

    def __call__(self, config: MultilingualE5SmallPipelineConfig) -> MultilingualE5SmallPipelineBundle:
        """Construit le pipeline E5 depuis une configuration explicite."""


@dataclass(frozen=True, slots=True)
class E5RankCliPassageOutput:
    """Projection stable d'un passage classé vers la CLI."""

    rank: int
    score: float
    text: str
    prefixed_text: str
    dimension: int
    normalized: bool
    l2_norm: float

    def to_json_dict(self) -> dict[str, object]:
        """Convertit le passage classé vers un objet JSON stable."""

        return {
            "rank": self.rank,
            "score": self.score,
            "text": self.text,
            "prefixed_text": self.prefixed_text,
            "dimension": self.dimension,
            "normalized": self.normalized,
            "l2_norm": self.l2_norm,
        }


@dataclass(frozen=True, slots=True)
class E5RankCliOutput:
    """Projection stable d'un ranking local vers la CLI."""

    query: str
    prefixed_query: str
    model: str
    backend: str
    tokenizer: str
    model_path: str
    device: str
    result_count: int
    passages: tuple[E5RankCliPassageOutput, ...]

    @classmethod
    def from_results(
        cls,
        results: E5RankedResults,
        bundle: MultilingualE5SmallPipelineBundle,
    ) -> E5RankCliOutput:
        """Construit une sortie CLI depuis un résultat de ranking."""

        query_embedding = results.query_embedding
        passages = tuple(
            E5RankCliPassageOutput(
                rank=item.rank,
                score=item.score,
                text=item.passage.content,
                prefixed_text=item.passage.prefixed,
                dimension=item.embedding.vector.dimension,
                normalized=item.embedding.vector.normalized,
                l2_norm=item.embedding.vector.l2_norm,
            )
            for item in results.passages
        )
        return cls(
            query=results.query.content,
            prefixed_query=results.query.prefixed,
            model=query_embedding.model,
            backend=query_embedding.backend,
            tokenizer=query_embedding.tokenizer_name,
            model_path=bundle.summary.model_path,
            device=bundle.summary.device,
            result_count=len(passages),
            passages=passages,
        )

    def to_json_dict(self) -> dict[str, object]:
        """Convertit le ranking vers un objet JSON stable."""

        return {
            "query": self.query,
            "prefixed_query": self.prefixed_query,
            "model": self.model,
            "backend": self.backend,
            "tokenizer": self.tokenizer,
            "model_path": self.model_path,
            "device": self.device,
            "result_count": self.result_count,
            "passages": [item.to_json_dict() for item in self.passages],
        }

    def to_text(self) -> str:
        """Produit une sortie texte lisible pour le développement."""

        lines = [
            f"query: {self.query}",
            f"prefixed_query: {self.prefixed_query}",
            f"model: {self.model}",
            f"backend: {self.backend}",
            f"tokenizer: {self.tokenizer}",
            f"device: {self.device}",
            f"model_path: {self.model_path}",
            f"result_count: {self.result_count}",
        ]
        for passage in self.passages:
            lines.extend(
                (
                    "",
                    f"#{passage.rank} score={passage.score:.8f}",
                    f"text: {passage.text}",
                    f"prefixed: {passage.prefixed_text}",
                    f"dimension: {passage.dimension}",
                    f"normalized: {passage.normalized}",
                    f"l2_norm: {passage.l2_norm:.8f}",
                )
            )
        return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Construit le parser CLI du ranking local E5."""

    parser = argparse.ArgumentParser(
        prog="missipy-rank-e5",
        description="Classe des passages locaux avec multilingual-e5-small via OpenVINO.",
    )
    parser.add_argument(
        "query",
        help=(
            "Requête à encoder. Si le préfixe E5 'query:' ou 'passage:' est absent, "
            "le rôle query est appliqué."
        ),
    )
    parser.add_argument(
        "--passage",
        action="append",
        default=[],
        help=(
            "Passage candidat. Peut être répété. Si le préfixe E5 est absent, "
            "le rôle passage est appliqué."
        ),
    )
    parser.add_argument(
        "--passages-file",
        default=None,
        help="Fichier texte contenant un passage par ligne. Les lignes vides sont ignorées.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Nombre maximal de passages à afficher.",
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
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Format de sortie.",
    )
    return parser


async def run_async(
    argv: Sequence[str],
    *,
    stdout: TextIOBase,
    stderr: TextIOBase,
    builder: E5RankPipelineBuilder = build_multilingual_e5_small_pipeline,
) -> int:
    """Exécute la CLI de ranking avec une factory injectable pour les tests."""

    parser = build_parser()
    args = parser.parse_args(list(argv))

    if args.max_length <= 0:
        stderr.write("--max-length must be positive\n")
        return 2
    if args.limit is not None and args.limit <= 0:
        stderr.write("--limit must be positive\n")
        return 2

    try:
        passages = _collect_passages(args.passage, args.passages_file)
    except OSError as exc:
        stderr.write(f"missipy-rank-e5 failed to read passages: {exc}\n")
        return 1

    if not passages:
        stderr.write("at least one --passage or --passages-file line is required\n")
        return 2

    config = MultilingualE5SmallPipelineConfig(
        local=MultilingualE5SmallLocalConfig(
            model_dir=args.model_dir,
            device=args.device,
            max_length=args.max_length,
        ),
        require_model_exists=True,
        metadata={"cli": "missipy-rank-e5"},
    )

    try:
        query = ensure_e5_text(args.query, default_role="query")
        bundle = builder(config)
        ranker = E5LocalRanker(bundle.pipeline)
        results = await ranker.rank(query, passages, limit=args.limit)
    except Exception as exc:  # pragma: no cover - message dépend des dépendances locales.
        stderr.write(f"missipy-rank-e5 failed: {exc}\n")
        return 1

    output = E5RankCliOutput.from_results(results, bundle)
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
    builder: E5RankPipelineBuilder = build_multilingual_e5_small_pipeline,
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


def _collect_passages(cli_passages: Sequence[str], passages_file: str | None) -> tuple[str, ...]:
    passages = [item for item in cli_passages if item.strip()]
    if passages_file is not None:
        passages.extend(_read_passages_file(Path(passages_file)))
    return tuple(passages)


def _read_passages_file(path: Path) -> tuple[str, ...]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return tuple(line.strip() for line in lines if line.strip())


if __name__ == "__main__":  # pragma: no cover - délégation CLI.
    raise SystemExit(main())
