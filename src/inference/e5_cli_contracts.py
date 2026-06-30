from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .e5_corpus_inspect import E5CorpusDiagnosticGateConfig
from .e5_pipeline import MultilingualE5SmallPipelineConfig
from .e5_profile import MultilingualE5SmallLocalConfig
from .e5_sources import (
    DEFAULT_E5_EXCLUDED_DIR_NAMES,
    DEFAULT_E5_EXCLUDED_FILE_SUFFIXES,
    SUPPORTED_E5_SOURCE_EXTENSIONS,
    load_e5_corpus_documents_from_sources,
)
from .report_io import JsonReportWritePolicy


E5CliOutputFormat = Literal["text", "json"]


@dataclass(frozen=True, slots=True)
class E5CliModelPolicy:
    """Politique de sélection explicite du modèle E5 local pour un outil CLI."""

    cli_name: str
    model_dir: str | None = None
    device: str = "CPU"
    max_length: int = 128

    def __post_init__(self) -> None:
        if not self.cli_name.strip():
            raise ValueError("cli_name must not be empty")
        if not self.device.strip():
            raise ValueError("--device must not be empty")
        if self.max_length <= 0:
            raise ValueError("--max-length must be positive")

    def to_pipeline_config(self) -> MultilingualE5SmallPipelineConfig:
        """Convertit la politique CLI vers la configuration pipeline déclarative."""
        return MultilingualE5SmallPipelineConfig(
            local=MultilingualE5SmallLocalConfig(
                model_dir=self.model_dir,
                device=self.device,
                max_length=self.max_length,
            ),
            require_model_exists=True,
            metadata={"cli": self.cli_name},
        )


@dataclass(frozen=True, slots=True)
class E5SourceSelectionPolicy:
    """Politique d'ingestion source pour build/rebuild E5 local."""

    passages: tuple[str, ...] = ()
    passages_file: Path | None = None
    source_files: tuple[Path, ...] = ()
    source_dirs: tuple[Path, ...] = ()
    source_extensions: tuple[str, ...] = SUPPORTED_E5_SOURCE_EXTENSIONS
    recursive: bool = True
    chunk_chars: int = 1200
    overlap_paragraphs: int = 0
    excluded_dir_names: tuple[str, ...] = DEFAULT_E5_EXCLUDED_DIR_NAMES
    excluded_file_suffixes: tuple[str, ...] = DEFAULT_E5_EXCLUDED_FILE_SUFFIXES

    def __post_init__(self) -> None:
        object.__setattr__(self, "passages", tuple(item.strip() for item in self.passages if item.strip()))
        object.__setattr__(self, "source_files", tuple(Path(item) for item in self.source_files))
        object.__setattr__(self, "source_dirs", tuple(Path(item) for item in self.source_dirs))
        object.__setattr__(self, "source_extensions", _normalize_strings(self.source_extensions, "source_extensions"))
        object.__setattr__(self, "excluded_dir_names", _normalize_strings(self.excluded_dir_names, "excluded_dir_names"))
        object.__setattr__(self, "excluded_file_suffixes", _normalize_strings(self.excluded_file_suffixes, "excluded_file_suffixes"))
        if self.chunk_chars <= 0:
            raise ValueError("--chunk-chars must be positive")
        if self.overlap_paragraphs < 0:
            raise ValueError("--overlap-paragraphs must be zero or positive")

    @property
    def has_sources(self) -> bool:
        return bool(self.source_files or self.source_dirs)

    def collect_passages(self) -> tuple[object, ...]:
        """Collecte les passages explicites et les sources fichiers selon la politique."""
        passages: list[object] = list(self.passages)
        if self.passages_file is not None:
            passages.extend(read_nonempty_lines(self.passages_file))
        source_paths = (*self.source_files, *self.source_dirs)
        if source_paths:
            passages.extend(
                load_e5_corpus_documents_from_sources(
                    tuple(str(item) for item in source_paths),
                    extensions=self.source_extensions,
                    recursive=self.recursive,
                    max_chars=self.chunk_chars,
                    overlap_paragraphs=self.overlap_paragraphs,
                    excluded_dir_names=self.excluded_dir_names,
                    excluded_file_suffixes=self.excluded_file_suffixes,
                )
            )
        return tuple(passages)


@dataclass(frozen=True, slots=True)
class E5BuildCommand:
    """Commande typée de build de corpus E5 local."""

    model: E5CliModelPolicy
    sources: E5SourceSelectionPolicy
    output: Path
    reuse_index: Path | None = None
    overwrite: bool = False
    lock_enabled: bool = True
    output_format: E5CliOutputFormat = "text"

    def __post_init__(self) -> None:
        if not self.output.name:
            raise ValueError("--output must target a filename")
        if self.output_format not in ("text", "json"):
            raise ValueError("--format must be text or json")


@dataclass(frozen=True, slots=True)
class E5SearchPolicy:
    """Politique de recherche E5 locale."""

    limit: int | None = None
    min_score: float | None = None

    def __post_init__(self) -> None:
        if self.limit is not None and self.limit <= 0:
            raise ValueError("--limit must be positive")
        if self.min_score is not None and not -1.0 <= self.min_score <= 1.0:
            raise ValueError("--min-score must be between -1.0 and 1.0")


@dataclass(frozen=True, slots=True)
class E5SearchRenderPolicy:
    """Politique de rendu d'un rapport de recherche E5."""

    output_format: E5CliOutputFormat = "text"
    excerpt_chars: int = 280
    include_full_text: bool = False

    def __post_init__(self) -> None:
        if self.output_format not in ("text", "json"):
            raise ValueError("--format must be text or json")
        if self.excerpt_chars <= 0:
            raise ValueError("--excerpt-chars must be positive")


@dataclass(frozen=True, slots=True)
class E5SearchCommand:
    """Commande typée de recherche dans un corpus E5 local."""

    model: E5CliModelPolicy
    index: Path
    query: str
    search: E5SearchPolicy = E5SearchPolicy()
    render: E5SearchRenderPolicy = E5SearchRenderPolicy()
    report: JsonReportWritePolicy = JsonReportWritePolicy(path=None)
    context: JsonReportWritePolicy = JsonReportWritePolicy(path=None)

    def __post_init__(self) -> None:
        if not self.index.name:
            raise ValueError("--index must target a filename")
        if not self.query.strip():
            raise ValueError("query must not be empty")


@dataclass(frozen=True, slots=True)
class E5DiagnosticGatePolicy:
    """Politique explicite de gate diagnostic de corpus E5."""

    min_chunks: int | None = None
    max_missing_source_metadata: int | None = None
    max_empty_texts: int | None = None
    max_dimension_mismatches: int | None = None
    fail_on_warning: bool = False

    def __post_init__(self) -> None:
        for name in (
            "min_chunks",
            "max_missing_source_metadata",
            "max_empty_texts",
            "max_dimension_mismatches",
        ):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must not be negative")

    @property
    def enabled(self) -> bool:
        return self.to_config().enabled

    def to_config(self) -> E5CorpusDiagnosticGateConfig:
        return E5CorpusDiagnosticGateConfig(
            min_chunks=self.min_chunks,
            max_missing_source_metadata=self.max_missing_source_metadata,
            max_empty_texts=self.max_empty_texts,
            max_dimension_mismatches=self.max_dimension_mismatches,
            fail_on_warning=self.fail_on_warning,
        )


@dataclass(frozen=True, slots=True)
class E5SearchValidationPolicy:
    """Politique de validation recherche appliquée à un corpus candidat."""

    queries: tuple[str, ...] = ()
    query_files: tuple[Path, ...] = ()
    limit: int = 1
    min_score: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "queries", tuple(item.strip() for item in self.queries if item.strip()))
        object.__setattr__(self, "query_files", tuple(Path(item) for item in self.query_files))
        if self.limit <= 0:
            raise ValueError("--validation-limit must be positive")
        if self.min_score is not None and not -1.0 <= self.min_score <= 1.0:
            raise ValueError("--validation-min-score must be between -1.0 and 1.0")

    def collect_queries(self) -> tuple[str, ...]:
        queries: list[str] = list(self.queries)
        for path in self.query_files:
            queries.extend(read_nonempty_lines(path))
        return tuple(queries)


@dataclass(frozen=True, slots=True)
class E5RebuildCommand:
    """Commande typée de rebuild sûr d'un corpus E5 local."""

    model: E5CliModelPolicy
    sources: E5SourceSelectionPolicy
    index: Path
    staging: Path | None = None
    dry_run: bool = False
    keep_staging: bool = False
    lock_enabled: bool = True
    output_format: E5CliOutputFormat = "text"
    diagnostic_gate: E5DiagnosticGatePolicy = E5DiagnosticGatePolicy()
    validation: E5SearchValidationPolicy = E5SearchValidationPolicy()
    report: JsonReportWritePolicy = JsonReportWritePolicy(path=None)

    def __post_init__(self) -> None:
        if not self.index.name:
            raise ValueError("--index must target a filename")
        if self.staging is not None and not self.staging.name:
            raise ValueError("--staging must target a filename")
        if self.output_format not in ("text", "json"):
            raise ValueError("--format must be text or json")


@dataclass(frozen=True, slots=True)
class E5InspectCommand:
    """Commande typée d'inspection d'un corpus E5 local."""

    index: Path
    top_sources_limit: int
    output_format: E5CliOutputFormat = "text"
    diagnostic_gate: E5DiagnosticGatePolicy = E5DiagnosticGatePolicy()

    def __post_init__(self) -> None:
        if not self.index.name:
            raise ValueError("--index must target a filename")
        if self.top_sources_limit <= 0:
            raise ValueError("--top-sources-limit must be positive")
        if self.output_format not in ("text", "json"):
            raise ValueError("--format must be text or json")


def source_selection_policy_from_cli(
    *,
    passages: Sequence[str],
    passages_file: str | None,
    source_files: Sequence[str],
    source_dirs: Sequence[str],
    source_extensions: str,
    recursive: bool,
    chunk_chars: int,
    overlap_paragraphs: int,
    excluded_dir_names: Sequence[str],
    excluded_file_suffixes: Sequence[str],
) -> E5SourceSelectionPolicy:
    """Construit la politique source depuis les valeurs brutes de CLI."""
    return E5SourceSelectionPolicy(
        passages=tuple(passages),
        passages_file=Path(passages_file) if passages_file is not None else None,
        source_files=tuple(Path(item) for item in source_files),
        source_dirs=tuple(Path(item) for item in source_dirs),
        source_extensions=tuple(item.strip() for item in source_extensions.split(",") if item.strip()),
        recursive=recursive,
        chunk_chars=chunk_chars,
        overlap_paragraphs=overlap_paragraphs,
        excluded_dir_names=merge_cli_values(DEFAULT_E5_EXCLUDED_DIR_NAMES, excluded_dir_names),
        excluded_file_suffixes=merge_cli_values(DEFAULT_E5_EXCLUDED_FILE_SUFFIXES, excluded_file_suffixes),
    )


def read_nonempty_lines(path: Path) -> tuple[str, ...]:
    """Lit un fichier texte comme une liste stable de lignes non vides."""
    return tuple(line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def merge_cli_values(defaults: Sequence[str], extras: Sequence[str]) -> tuple[str, ...]:
    """Fusionne valeurs par défaut et ajouts CLI sans doublons, en ordre stable."""
    values: list[str] = []
    for item in (*defaults, *extras):
        value = item.strip()
        if value and value not in values:
            values.append(value)
    return tuple(values)


def _normalize_strings(values: Sequence[str], field_name: str) -> tuple[str, ...]:
    normalized = tuple(item.strip() for item in values if item.strip())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized
