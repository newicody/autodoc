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

from .e5_cli_contracts import (
    E5BuildCommand,
    E5CliModelPolicy,
    E5SearchCommand,
    E5SearchPolicy,
    E5SearchRenderPolicy,
    source_selection_policy_from_cli,
)
from .e5_corpus import E5CorpusBuilder, E5CorpusIndex, E5CorpusJsonStore, E5CorpusSearcher
from .e5_corpus_lock import E5CorpusBuildLock
from .e5_incremental import E5IncrementalBuildStats, E5IncrementalCorpusBuilder
from .e5_pipeline import (
    MultilingualE5SmallPipelineBundle,
    MultilingualE5SmallPipelineConfig,
    build_multilingual_e5_small_pipeline,
)
from .e5_profile import MULTILINGUAL_E5_SMALL_ENV
from .e5_search_report import E5SearchReport, E5SearchReportConfig
from .e5_sources import SUPPORTED_E5_SOURCE_EXTENSIONS
from .report_io import JsonReportWritePolicy, write_json_report_atomic


class E5CorpusPipelineBuilder(Protocol):
    """Factory injectable du bundle E5 local."""

    def __call__(self, config: MultilingualE5SmallPipelineConfig) -> MultilingualE5SmallPipelineBundle:
        """Construit un bundle E5 depuis une configuration explicite."""


@dataclass(frozen=True, slots=True)
class E5CorpusBuildCliOutput:
    """Résumé stable de construction d'un corpus local."""

    output: str
    model: str
    backend: str
    tokenizer: str
    dimension: int
    size: int
    reused_count: int | None = None
    embedded_count: int | None = None
    removed_count: int | None = None
    atomic_write: bool = True
    lock_enabled: bool = True
    lock_path: str | None = None

    def to_json_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "output": self.output,
            "model": self.model,
            "backend": self.backend,
            "tokenizer": self.tokenizer,
            "dimension": self.dimension,
            "size": self.size,
            "atomic_write": self.atomic_write,
            "lock_enabled": self.lock_enabled,
        }
        if self.lock_path is not None:
            data["lock_path"] = self.lock_path
        if self.reused_count is not None:
            data["reused_count"] = self.reused_count
        if self.embedded_count is not None:
            data["embedded_count"] = self.embedded_count
        if self.removed_count is not None:
            data["removed_count"] = self.removed_count
        return data

    def to_text(self) -> str:
        lines = [
            f"output: {self.output}",
            f"model: {self.model}",
            f"backend: {self.backend}",
            f"tokenizer: {self.tokenizer}",
            f"dimension: {self.dimension}",
            f"size: {self.size}",
            f"atomic_write: {self.atomic_write}",
            f"lock_enabled: {self.lock_enabled}",
        ]
        if self.lock_path is not None:
            lines.append(f"lock_path: {self.lock_path}")
        if self.reused_count is not None:
            lines.append(f"reused_count: {self.reused_count}")
        if self.embedded_count is not None:
            lines.append(f"embedded_count: {self.embedded_count}")
        if self.removed_count is not None:
            lines.append(f"removed_count: {self.removed_count}")
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class E5CorpusSearchCliOutput:
    """Résumé stable de recherche dans un corpus local."""

    report: E5SearchReport

    @classmethod
    def from_results(
        cls,
        *,
        query: str,
        prefixed_query: str,
        index: str,
        results: object,
        config: E5SearchReportConfig | None = None,
    ) -> E5CorpusSearchCliOutput:
        return cls(
            report=E5SearchReport.from_results(
                query=query,
                prefixed_query=prefixed_query,
                index=index,
                results=results,
                config=config,
            )
        )

    def to_json_dict(self) -> dict[str, object]:
        return self.report.to_json_dict()

    def to_text(self) -> str:
        return self.report.to_text()


def build_build_parser() -> argparse.ArgumentParser:
    """Parser pour la construction d'un corpus local."""
    parser = argparse.ArgumentParser(
        prog="missipy-build-e5-corpus",
        description="Construit un corpus E5 local persistant à partir de passages.",
    )
    _add_common_model_args(parser)
    parser.add_argument("--passage", action="append", default=[], help="Passage à indexer. Peut être répété.")
    parser.add_argument("--passages-file", default=None, help="Fichier texte contenant un passage par ligne.")
    parser.add_argument("--source-file", action="append", default=[], help="Fichier .md/.markdown/.txt à découper en passages. Peut être répété.")
    parser.add_argument("--source-dir", action="append", default=[], help="Dossier contenant des sources .md/.markdown/.txt à indexer. Peut être répété.")
    parser.add_argument("--source-extensions", default=",".join(SUPPORTED_E5_SOURCE_EXTENSIONS), help="Extensions source séparées par des virgules.")
    parser.add_argument("--no-recursive", action="store_true", help="Ne parcourt pas récursivement les --source-dir.")
    parser.add_argument("--exclude-dir", action="append", default=[], help="Nom de répertoire supplémentaire à ignorer pendant l'ingestion source. Peut être répété.")
    parser.add_argument("--exclude-file-suffix", action="append", default=[], help="Suffixe de fichier supplémentaire à ignorer pendant l'ingestion source. Peut être répété.")
    parser.add_argument("--chunk-chars", type=int, default=1200, help="Taille cible maximale des chunks source en caractères.")
    parser.add_argument("--overlap-paragraphs", type=int, default=0, help="Nombre de paragraphes repris entre deux chunks.")
    parser.add_argument("--output", required=True, help="Fichier JSON de sortie du corpus local.")
    parser.add_argument("--reuse-index", default=None, help="Index JSON existant à réutiliser pour un build incrémental.")
    parser.add_argument("--overwrite", action="store_true", help="Autorise l'écrasement du fichier de sortie.")
    parser.add_argument("--no-lock", action="store_true", help="Désactive le verrou fichier de build du corpus.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Format de sortie CLI.")
    return parser


def build_search_parser() -> argparse.ArgumentParser:
    """Parser pour la recherche dans un corpus local."""
    parser = argparse.ArgumentParser(
        prog="missipy-search-e5-corpus",
        description="Recherche dans un corpus E5 local déjà vectorisé.",
    )
    _add_common_model_args(parser)
    parser.add_argument("query", help="Requête utilisateur. Le rôle query est appliqué si absent.")
    parser.add_argument("--index", required=True, help="Fichier JSON du corpus local.")
    parser.add_argument("--limit", type=int, default=None, help="Nombre maximal de résultats.")
    parser.add_argument("--min-score", type=float, default=None, help="Score minimal inclusif requis pour conserver un résultat.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Format de sortie CLI.")
    parser.add_argument("--report-file", default=None, help="Écrit un rapport JSON stable de la recherche vers ce fichier si la recherche réussit.")
    parser.add_argument("--excerpt-chars", type=int, default=280, help="Longueur maximale de l'extrait affiché par résultat.")
    parser.add_argument("--full-text", action="store_true", help="Inclut le texte complet du chunk dans la sortie.")
    return parser


async def run_build_async(
    argv: Sequence[str],
    *,
    stdout: TextIOBase,
    stderr: TextIOBase,
    builder: E5CorpusPipelineBuilder = build_multilingual_e5_small_pipeline,
    store: E5CorpusJsonStore | None = None,
) -> int:
    """Construit un corpus depuis la CLI."""
    raw_args = build_build_parser().parse_args(list(argv))
    try:
        command = _build_command(raw_args)
    except ValueError as exc:
        stderr.write(f"{exc}\n")
        return 2

    try:
        passages = command.sources.collect_passages()
    except OSError as exc:
        stderr.write(f"missipy-build-e5-corpus failed to read passages: {exc}\n")
        return 1

    if not passages:
        stderr.write("at least one --passage, --passages-file, --source-file or --source-dir entry is required\n")
        return 2

    lock_path: str | None = None
    try:
        json_store = store or E5CorpusJsonStore()
        build_lock = E5CorpusBuildLock(command.output) if command.lock_enabled else None
        if build_lock is None:
            path, index, stats = await _build_and_write_corpus(command, passages, json_store, builder)
        else:
            with build_lock:
                lock_path = str(build_lock.path)
                path, index, stats = await _build_and_write_corpus(command, passages, json_store, builder)
    except Exception as exc:  # pragma: no cover - dépend des dépendances locales.
        stderr.write(f"missipy-build-e5-corpus failed: {exc}\n")
        return 1

    output = E5CorpusBuildCliOutput(
        output=str(path),
        model=index.model,
        backend=index.backend,
        tokenizer=index.tokenizer,
        dimension=index.dimension,
        size=index.size,
        reused_count=stats.reused_count if stats is not None else None,
        embedded_count=stats.embedded_count if stats is not None else None,
        removed_count=stats.removed_count if stats is not None else None,
        atomic_write=True,
        lock_enabled=command.lock_enabled,
        lock_path=lock_path,
    )
    _write_output(stdout, command.output_format, output.to_json_dict(), output.to_text())
    return 0


async def _build_and_write_corpus(
    command: E5BuildCommand,
    passages: Sequence[object],
    json_store: E5CorpusJsonStore,
    builder: E5CorpusPipelineBuilder,
) -> tuple[Path, E5CorpusIndex, E5IncrementalBuildStats | None]:
    bundle = builder(command.model.to_pipeline_config())
    stats: E5IncrementalBuildStats | None = None
    if command.reuse_index is not None:
        previous_index = json_store.read(command.reuse_index)
        incremental = await E5IncrementalCorpusBuilder(bundle.pipeline).build(
            passages,
            previous_index=previous_index,
            metadata={"builder": "missipy-build-e5-corpus"},
        )
        index = incremental.index
        stats = incremental.stats
    else:
        index = await E5CorpusBuilder(bundle.pipeline).build(passages, metadata={"builder": "missipy-build-e5-corpus"})
    path = json_store.write_atomic(index, command.output, overwrite=command.overwrite)
    return path, index, stats


async def run_search_async(
    argv: Sequence[str],
    *,
    stdout: TextIOBase,
    stderr: TextIOBase,
    builder: E5CorpusPipelineBuilder = build_multilingual_e5_small_pipeline,
    store: E5CorpusJsonStore | None = None,
) -> int:
    """Recherche dans un corpus depuis la CLI."""
    raw_args = build_search_parser().parse_args(list(argv))
    try:
        command = _search_command(raw_args)
    except ValueError as exc:
        stderr.write(f"{exc}\n")
        return 2

    try:
        index: E5CorpusIndex = (store or E5CorpusJsonStore()).read(command.index)
        bundle = builder(command.model.to_pipeline_config())
        results = await E5CorpusSearcher(bundle.pipeline).search(
            command.query,
            index,
            limit=command.search.limit,
            min_score=command.search.min_score,
        )
    except Exception as exc:  # pragma: no cover - dépend des dépendances locales.
        stderr.write(f"missipy-search-e5-corpus failed: {exc}\n")
        return 1

    output = E5CorpusSearchCliOutput.from_results(
        query=results.query.content,
        prefixed_query=results.query.prefixed,
        index=str(command.index),
        results=results,
        config=E5SearchReportConfig(
            excerpt_chars=command.render.excerpt_chars,
            include_full_text=command.render.include_full_text,
        ),
    )
    json_output = output.to_json_dict()
    try:
        write_json_report_atomic(command.report, json_output)
    except OSError as exc:
        stderr.write(f"missipy-search-e5-corpus failed to write report: {exc}\n")
        return 1

    _write_output(stdout, command.render.output_format, json_output, output.to_text())
    return 0


def run_build(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIOBase | None = None,
    stderr: TextIOBase | None = None,
    builder: E5CorpusPipelineBuilder = build_multilingual_e5_small_pipeline,
    store: E5CorpusJsonStore | None = None,
) -> int:
    return asyncio.run(
        run_build_async(
            tuple(argv if argv is not None else sys.argv[1:]),
            stdout=stdout or sys.stdout,
            stderr=stderr or sys.stderr,
            builder=builder,
            store=store,
        )
    )


def run_search(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIOBase | None = None,
    stderr: TextIOBase | None = None,
    builder: E5CorpusPipelineBuilder = build_multilingual_e5_small_pipeline,
    store: E5CorpusJsonStore | None = None,
) -> int:
    return asyncio.run(
        run_search_async(
            tuple(argv if argv is not None else sys.argv[1:]),
            stdout=stdout or sys.stdout,
            stderr=stderr or sys.stderr,
            builder=builder,
            store=store,
        )
    )


def build_main(argv: Sequence[str] | None = None) -> int:
    return run_build(argv)


def search_main(argv: Sequence[str] | None = None) -> int:
    return run_search(argv)


def _build_command(args: argparse.Namespace) -> E5BuildCommand:
    return E5BuildCommand(
        model=E5CliModelPolicy(
            cli_name="missipy-build-e5-corpus",
            model_dir=args.model_dir,
            device=args.device,
            max_length=args.max_length,
        ),
        sources=source_selection_policy_from_cli(
            passages=args.passage,
            passages_file=args.passages_file,
            source_files=args.source_file,
            source_dirs=args.source_dir,
            source_extensions=args.source_extensions,
            recursive=not args.no_recursive,
            chunk_chars=args.chunk_chars,
            overlap_paragraphs=args.overlap_paragraphs,
            excluded_dir_names=args.exclude_dir,
            excluded_file_suffixes=args.exclude_file_suffix,
        ),
        output=Path(args.output),
        reuse_index=Path(args.reuse_index) if args.reuse_index is not None else None,
        overwrite=args.overwrite,
        lock_enabled=not args.no_lock,
        output_format=args.format,
    )


def _search_command(args: argparse.Namespace) -> E5SearchCommand:
    return E5SearchCommand(
        model=E5CliModelPolicy(
            cli_name="missipy-search-e5-corpus",
            model_dir=args.model_dir,
            device=args.device,
            max_length=args.max_length,
        ),
        index=Path(args.index),
        query=args.query,
        search=E5SearchPolicy(limit=args.limit, min_score=args.min_score),
        render=E5SearchRenderPolicy(
            output_format=args.format,
            excerpt_chars=args.excerpt_chars,
            include_full_text=args.full_text,
        ),
        report=JsonReportWritePolicy(path=Path(args.report_file) if args.report_file is not None else None),
    )


def _add_common_model_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--model-dir",
        default=None,
        help=f"Dossier du modèle OpenVINO. Par défaut: {MULTILINGUAL_E5_SMALL_ENV} ou config locale.",
    )
    parser.add_argument("--device", default="CPU", help="Device OpenVINO, par exemple CPU ou GPU.")
    parser.add_argument("--max-length", type=int, default=128, help="Longueur maximale de tokenization.")


def _write_output(stdout: TextIOBase, fmt: str, json_data: dict[str, object], text: str) -> None:
    if fmt == "json":
        stdout.write(json.dumps(json_data, ensure_ascii=False, sort_keys=True))
        stdout.write("\n")
    else:
        stdout.write(text)
        stdout.write("\n")
