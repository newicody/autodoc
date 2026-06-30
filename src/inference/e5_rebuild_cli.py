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

from .e5_corpus import E5CorpusBuilder, E5CorpusIndex, E5CorpusJsonStore
from .e5_corpus_lock import E5CorpusBuildLock
from .e5_incremental import E5IncrementalBuildStats, E5IncrementalCorpusBuilder
from .e5_corpus_inspect import (
    E5CorpusDiagnosticGateConfig,
    E5CorpusDiagnosticGateResult,
    evaluate_e5_corpus_diagnostic_gate,
    inspect_e5_corpus,
)
from .e5_pipeline import (
    MultilingualE5SmallPipelineBundle,
    MultilingualE5SmallPipelineConfig,
    build_multilingual_e5_small_pipeline,
)
from .e5_profile import MULTILINGUAL_E5_SMALL_ENV, MultilingualE5SmallLocalConfig
from .e5_search_validation import E5SearchValidationQueryResult, validate_e5_search_queries
from .e5_sources import (
    DEFAULT_E5_EXCLUDED_DIR_NAMES,
    DEFAULT_E5_EXCLUDED_FILE_SUFFIXES,
    SUPPORTED_E5_SOURCE_EXTENSIONS,
    load_e5_corpus_documents_from_sources,
)


class E5CorpusRebuildDiagnosticGateError(ValueError):
    """Erreur contrôlée quand un candidat échoue au diagnostic gate."""


class E5CorpusRebuildSearchValidationError(ValueError):
    """Erreur contrôlée quand le jeu de validation recherche échoue."""


class E5RebuildPipelineBuilder(Protocol):
    """Factory injectable du bundle E5 local pour rebuild sûr."""

    def __call__(self, config: MultilingualE5SmallPipelineConfig) -> MultilingualE5SmallPipelineBundle:
        """Construit un bundle E5 depuis une configuration explicite."""


@dataclass(frozen=True, slots=True)
class E5CorpusRebuildValidation:
    """Résultat stable de validation recherche avant promotion."""

    query: str | None = None
    hit_count: int | None = None
    best_score: float | None = None
    query_results: tuple[E5SearchValidationQueryResult, ...] = ()
    min_score: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "query_results", tuple(self.query_results))

    @property
    def search_enabled(self) -> bool:
        return self.query is not None or bool(self.query_results)

    @property
    def query_count(self) -> int:
        if self.query_results:
            return len(self.query_results)
        return 1 if self.query is not None else 0

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.query_results)

    @property
    def total_hit_count(self) -> int | None:
        if self.query_results:
            return sum(item.hit_count for item in self.query_results)
        return self.hit_count

    @property
    def effective_best_score(self) -> float | None:
        if self.query_results:
            scores = [item.best_score for item in self.query_results if item.best_score is not None]
            return max(scores) if scores else None
        return self.best_score

    @classmethod
    def from_query_results(
        cls,
        query_results: tuple[E5SearchValidationQueryResult, ...],
        *,
        min_score: float | None = None,
    ) -> E5CorpusRebuildValidation:
        """Construit le résumé rebuild depuis un jeu de requêtes validées."""
        first = query_results[0] if len(query_results) == 1 else None
        return cls(
            query=first.query if first is not None else None,
            hit_count=sum(item.hit_count for item in query_results),
            best_score=max(
                (item.best_score for item in query_results if item.best_score is not None),
                default=None,
            ),
            query_results=query_results,
            min_score=min_score,
        )

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "search_enabled": self.search_enabled,
            "query": self.query,
            "hit_count": self.total_hit_count,
            "best_score": self.effective_best_score,
            "query_count": self.query_count,
            "min_score": self.min_score,
            "passed": self.passed,
            "queries": [item.to_json_dict() for item in self.query_results],
        }

    def to_text_lines(self) -> tuple[str, ...]:
        if not self.search_enabled:
            return ("validation_search: False",)
        lines = ["validation_search: True", f"validation_query_count: {self.query_count}"]
        if self.query is not None:
            lines.append(f"validation_query: {self.query}")
        if self.min_score is not None:
            lines.append(f"validation_min_score: {self.min_score:.8f}")
        total_hit_count = self.total_hit_count
        if total_hit_count is not None:
            lines.append(f"validation_hit_count: {total_hit_count}")
        best_score = self.effective_best_score
        if best_score is not None:
            lines.append(f"validation_best_score: {best_score:.8f}")
        lines.append(f"validation_passed: {str(self.passed)}")
        if len(self.query_results) > 1:
            lines.append("validation_queries:")
            for result in self.query_results:
                lines.append(f"  - query: {result.query}")
                lines.append(f"    hit_count: {result.hit_count}")
                lines.append(f"    passed: {str(result.passed)}")
                if result.best_score is not None:
                    lines.append(f"    best_score: {result.best_score:.8f}")
        return tuple(lines)


@dataclass(frozen=True, slots=True)
class E5CorpusRebuildCliOutput:
    """Résumé stable d'un rebuild sûr de corpus E5."""

    index: str
    staging: str
    promoted: bool
    model: str
    backend: str
    tokenizer: str
    dimension: int
    size: int
    reused_count: int | None
    embedded_count: int | None
    removed_count: int | None
    validation: E5CorpusRebuildValidation
    diagnostic_gate: E5CorpusDiagnosticGateResult | None = None
    atomic_write: bool = True
    lock_enabled: bool = True
    lock_path: str | None = None

    def to_json_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "index": self.index,
            "staging": self.staging,
            "promoted": self.promoted,
            "model": self.model,
            "backend": self.backend,
            "tokenizer": self.tokenizer,
            "dimension": self.dimension,
            "size": self.size,
            "atomic_write": self.atomic_write,
            "lock_enabled": self.lock_enabled,
            "validation": self.validation.to_json_dict(),
        }
        if self.diagnostic_gate is not None:
            data["diagnostic_gate"] = self.diagnostic_gate.to_json_dict()
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
            f"index: {self.index}",
            f"staging: {self.staging}",
            f"promoted: {self.promoted}",
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
        lines.extend(self.validation.to_text_lines())
        if self.diagnostic_gate is not None:
            lines.extend(_diagnostic_gate_text_lines(self.diagnostic_gate))
        return "\n".join(lines)


def build_rebuild_parser() -> argparse.ArgumentParser:
    """Parser pour le rebuild sûr d'un corpus local."""
    parser = argparse.ArgumentParser(
        prog="missipy-rebuild-e5-corpus",
        description="Reconstruit un corpus E5 via staging, validation puis promotion atomique.",
    )
    _add_common_model_args(parser)
    parser.add_argument("--index", required=True, help="Fichier JSON final du corpus local à reconstruire/promouvoir.")
    parser.add_argument("--staging", default=None, help="Fichier candidat temporaire. Par défaut: voisin caché de --index.")
    parser.add_argument("--passage", action="append", default=[], help="Passage à indexer. Peut être répété.")
    parser.add_argument("--passages-file", default=None, help="Fichier texte contenant un passage par ligne.")
    parser.add_argument(
        "--source-file",
        action="append",
        default=[],
        help="Fichier .md/.markdown/.txt à découper en passages. Peut être répété.",
    )
    parser.add_argument(
        "--source-dir",
        action="append",
        default=[],
        help="Dossier contenant des sources .md/.markdown/.txt à indexer. Peut être répété.",
    )
    parser.add_argument(
        "--source-extensions",
        default=",".join(SUPPORTED_E5_SOURCE_EXTENSIONS),
        help="Extensions source séparées par des virgules.",
    )
    parser.add_argument("--no-recursive", action="store_true", help="Ne parcourt pas récursivement les --source-dir.")
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Nom de répertoire supplémentaire à ignorer pendant l'ingestion source. Peut être répété.",
    )
    parser.add_argument(
        "--exclude-file-suffix",
        action="append",
        default=[],
        help="Suffixe de fichier supplémentaire à ignorer pendant l'ingestion source. Peut être répété.",
    )
    parser.add_argument("--chunk-chars", type=int, default=1200, help="Taille cible maximale des chunks source en caractères.")
    parser.add_argument("--overlap-paragraphs", type=int, default=0, help="Nombre de paragraphes repris entre deux chunks.")
    parser.add_argument(
        "--validation-query",
        action="append",
        default=[],
        help="Requête rapide exécutée sur le corpus candidat avant promotion. Peut être répétée.",
    )
    parser.add_argument(
        "--validation-queries-file",
        action="append",
        default=[],
        help="Fichier texte contenant une requête de validation par ligne. Peut être répété.",
    )
    parser.add_argument(
        "--validation-min-score",
        type=float,
        default=None,
        help="Score minimal inclusif requis pour chaque requête de validation.",
    )
    parser.add_argument("--validation-limit", type=int, default=1, help="Nombre de hits demandés pendant la validation recherche.")
    parser.add_argument("--min-chunks", type=int, default=None, help="Nombre minimal de chunks requis avant promotion.")
    parser.add_argument(
        "--max-missing-source-metadata",
        type=int,
        default=None,
        help="Nombre maximal de chunks sans métadonnée source_path avant promotion.",
    )
    parser.add_argument("--max-empty-texts", type=int, default=None, help="Nombre maximal de chunks à texte vide tolérés.")
    parser.add_argument(
        "--max-dimension-mismatches",
        type=int,
        default=None,
        help="Nombre maximal de vecteurs dont la dimension diffère de l'index.",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Échoue avant promotion si le diagnostic candidat contient des avertissements.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Construit et valide le staging sans le promouvoir vers --index.")
    parser.add_argument("--keep-staging", action="store_true", help="Conserve le staging après échec ou dry-run.")
    parser.add_argument("--no-lock", action="store_true", help="Désactive le verrou fichier du corpus final.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Format de sortie CLI.")
    return parser


async def run_rebuild_async(
    argv: Sequence[str],
    *,
    stdout: TextIOBase,
    stderr: TextIOBase,
    builder: E5RebuildPipelineBuilder = build_multilingual_e5_small_pipeline,
    store: E5CorpusJsonStore | None = None,
) -> int:
    """Reconstruit un corpus local en staging puis promotion contrôlée."""
    args = build_rebuild_parser().parse_args(list(argv))
    validation_error = _validate_args(args)
    if validation_error is not None:
        stderr.write(validation_error)
        stderr.write("\n")
        return 2

    target = Path(args.index)
    staging = Path(args.staging) if args.staging is not None else rebuild_staging_path(target)
    if target.resolve() == staging.resolve():
        stderr.write("--staging must be different from --index\n")
        return 2

    try:
        passages = _collect_passages(args)
    except OSError as exc:
        stderr.write(f"missipy-rebuild-e5-corpus failed to read passages: {exc}\n")
        return 1

    if not passages:
        stderr.write("at least one --passage, --passages-file, --source-file or --source-dir entry is required\n")
        return 2

    lock_enabled = not args.no_lock
    lock_path: str | None = None
    try:
        json_store = store or E5CorpusJsonStore()
        build_lock = E5CorpusBuildLock(target) if lock_enabled else None
        if build_lock is None:
            output = await _rebuild_candidate(args, passages, target, staging, json_store, builder)
        else:
            with build_lock:
                lock_path = str(build_lock.path)
                output = await _rebuild_candidate(args, passages, target, staging, json_store, builder, lock_path=lock_path)
    except E5CorpusRebuildDiagnosticGateError as exc:
        if not args.keep_staging:
            _cleanup_staging(staging)
        stderr.write(f"candidate diagnostic gate failed: {exc}\n")
        return 2
    except E5CorpusRebuildSearchValidationError as exc:
        if not args.keep_staging:
            _cleanup_staging(staging)
        stderr.write(f"candidate search validation failed: {exc}\n")
        return 2
    except Exception as exc:  # pragma: no cover - dépend des dépendances locales.
        if not args.keep_staging:
            _cleanup_staging(staging)
        stderr.write(f"missipy-rebuild-e5-corpus failed: {exc}\n")
        return 1

    _write_output(stdout, args.format, output.to_json_dict(), output.to_text())
    return 0


async def _rebuild_candidate(
    args: argparse.Namespace,
    passages: Sequence[object],
    target: Path,
    staging: Path,
    json_store: E5CorpusJsonStore,
    builder: E5RebuildPipelineBuilder,
    *,
    lock_path: str | None = None,
) -> E5CorpusRebuildCliOutput:
    bundle = builder(_pipeline_config(args, cli_name="missipy-rebuild-e5-corpus"))
    previous_index = json_store.read(target) if target.exists() else None
    index, stats = await _build_index(bundle, passages, previous_index)
    json_store.write_atomic(index, staging, overwrite=True)
    candidate = json_store.read(staging)
    diagnostic_gate = _evaluate_candidate_diagnostic_gate(candidate, args)
    validation_queries = _collect_validation_queries(args)
    validation = await _validate_candidate(
        bundle,
        candidate,
        validation_queries,
        args.validation_limit,
        args.validation_min_score,
    )
    promoted = False
    if not args.dry_run:
        staging.replace(target)
        promoted = True
    elif not args.keep_staging:
        _cleanup_staging(staging)
    return E5CorpusRebuildCliOutput(
        index=str(target),
        staging=str(staging),
        promoted=promoted,
        model=candidate.model,
        backend=candidate.backend,
        tokenizer=candidate.tokenizer,
        dimension=candidate.dimension,
        size=candidate.size,
        reused_count=stats.reused_count if stats is not None else None,
        embedded_count=stats.embedded_count if stats is not None else None,
        removed_count=stats.removed_count if stats is not None else None,
        validation=validation,
        diagnostic_gate=diagnostic_gate,
        atomic_write=True,
        lock_enabled=not args.no_lock,
        lock_path=lock_path,
    )


async def _build_index(
    bundle: MultilingualE5SmallPipelineBundle,
    passages: Sequence[object],
    previous_index: E5CorpusIndex | None,
) -> tuple[E5CorpusIndex, E5IncrementalBuildStats | None]:
    if previous_index is None:
        return await E5CorpusBuilder(bundle.pipeline).build(passages, metadata={"builder": "missipy-rebuild-e5-corpus"}), None
    result = await E5IncrementalCorpusBuilder(bundle.pipeline).build(
        passages,
        previous_index=previous_index,
        metadata={"builder": "missipy-rebuild-e5-corpus"},
    )
    return result.index, result.stats


async def _validate_candidate(
    bundle: MultilingualE5SmallPipelineBundle,
    index: E5CorpusIndex,
    queries: Sequence[str],
    limit: int,
    min_score: float | None,
) -> E5CorpusRebuildValidation:
    if not queries:
        return E5CorpusRebuildValidation()
    results = await validate_e5_search_queries(
        bundle.pipeline,
        index,
        queries,
        limit=limit,
        min_score=min_score,
    )
    failed = tuple(item for item in results if not item.passed)
    if failed:
        failed_queries = ", ".join(item.query for item in failed)
        raise E5CorpusRebuildSearchValidationError(f"queries returned no hits: {failed_queries}")
    return E5CorpusRebuildValidation.from_query_results(results, min_score=min_score)


def _evaluate_candidate_diagnostic_gate(
    candidate: E5CorpusIndex,
    args: argparse.Namespace,
) -> E5CorpusDiagnosticGateResult | None:
    """Inspecte le candidat et bloque la promotion si les seuils échouent."""
    config = _diagnostic_gate_config(args)
    if not config.enabled:
        return None
    diagnostics = inspect_e5_corpus(candidate)
    gate = evaluate_e5_corpus_diagnostic_gate(diagnostics, config)
    if not gate.passed:
        raise E5CorpusRebuildDiagnosticGateError("; ".join(gate.violations))
    return gate


def _diagnostic_gate_config(args: argparse.Namespace) -> E5CorpusDiagnosticGateConfig:
    return E5CorpusDiagnosticGateConfig(
        min_chunks=args.min_chunks,
        max_missing_source_metadata=args.max_missing_source_metadata,
        max_empty_texts=args.max_empty_texts,
        max_dimension_mismatches=args.max_dimension_mismatches,
        fail_on_warning=args.fail_on_warning,
    )


def _diagnostic_gate_text_lines(gate: E5CorpusDiagnosticGateResult) -> tuple[str, ...]:
    lines = [
        "diagnostic_gate:",
        f"  enabled: {str(gate.enabled)}",
        f"  passed: {str(gate.passed)}",
    ]
    if gate.violations:
        lines.append("  violations:")
        lines.extend(f"    - {item}" for item in gate.violations)
    else:
        lines.append("  violations: none")
    return tuple(lines)


def run_rebuild(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIOBase | None = None,
    stderr: TextIOBase | None = None,
    builder: E5RebuildPipelineBuilder = build_multilingual_e5_small_pipeline,
    store: E5CorpusJsonStore | None = None,
) -> int:
    return asyncio.run(
        run_rebuild_async(
            tuple(argv if argv is not None else sys.argv[1:]),
            stdout=stdout or sys.stdout,
            stderr=stderr or sys.stderr,
            builder=builder,
            store=store,
        )
    )


def rebuild_main(argv: Sequence[str] | None = None) -> int:
    return run_rebuild(argv)


def rebuild_staging_path(index_path: str | Path) -> Path:
    """Chemin de staging voisin utilisé par rebuild sûr."""
    target = Path(index_path)
    if not target.name:
        raise ValueError("E5 rebuild target must have a filename")
    return target.with_name(f".{target.name}.rebuild.json")


def _validate_args(args: argparse.Namespace) -> str | None:
    if args.max_length <= 0:
        return "--max-length must be positive"
    if args.chunk_chars <= 0:
        return "--chunk-chars must be positive"
    if args.overlap_paragraphs < 0:
        return "--overlap-paragraphs must be zero or positive"
    if args.validation_limit <= 0:
        return "--validation-limit must be positive"
    if args.validation_min_score is not None and not -1.0 <= args.validation_min_score <= 1.0:
        return "--validation-min-score must be between -1.0 and 1.0"
    for option_name in (
        "min_chunks",
        "max_missing_source_metadata",
        "max_empty_texts",
        "max_dimension_mismatches",
    ):
        value = getattr(args, option_name)
        if value is not None and value < 0:
            return f"--{option_name.replace('_', '-')} must not be negative"
    return None


def _collect_validation_queries(args: argparse.Namespace) -> tuple[str, ...]:
    """Collecte les requêtes de validation CLI en ordre stable."""
    queries: list[str] = [item.strip() for item in args.validation_query if item.strip()]
    for file_path in args.validation_queries_file:
        queries.extend(_read_passages_file(Path(file_path)))
    return tuple(queries)


def _collect_passages(args: argparse.Namespace) -> tuple[object, ...]:
    passages: list[object] = [item for item in args.passage if item.strip()]
    if args.passages_file is not None:
        passages.extend(_read_passages_file(Path(args.passages_file)))
    source_paths = [*args.source_file, *args.source_dir]
    if source_paths:
        extensions = tuple(item.strip() for item in args.source_extensions.split(",") if item.strip())
        passages.extend(
            load_e5_corpus_documents_from_sources(
                tuple(source_paths),
                extensions=extensions,
                recursive=not args.no_recursive,
                max_chars=args.chunk_chars,
                overlap_paragraphs=args.overlap_paragraphs,
                excluded_dir_names=_merge_cli_values(DEFAULT_E5_EXCLUDED_DIR_NAMES, args.exclude_dir),
                excluded_file_suffixes=_merge_cli_values(DEFAULT_E5_EXCLUDED_FILE_SUFFIXES, args.exclude_file_suffix),
            )
        )
    return tuple(passages)


def _read_passages_file(path: Path) -> tuple[str, ...]:
    return tuple(line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _merge_cli_values(defaults: Sequence[str], extras: Sequence[str]) -> tuple[str, ...]:
    """Fusionne les garde-fous par défaut et les ajouts CLI en ordre stable."""
    values: list[str] = []
    for item in (*defaults, *extras):
        value = item.strip()
        if value and value not in values:
            values.append(value)
    return tuple(values)


def _pipeline_config(args: argparse.Namespace, *, cli_name: str) -> MultilingualE5SmallPipelineConfig:
    return MultilingualE5SmallPipelineConfig(
        local=MultilingualE5SmallLocalConfig(
            model_dir=args.model_dir,
            device=args.device,
            max_length=args.max_length,
        ),
        require_model_exists=True,
        metadata={"cli": cli_name},
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


def _cleanup_staging(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
