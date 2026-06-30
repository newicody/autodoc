from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .e5_corpus import E5CorpusIndex


DEFAULT_E5_CORPUS_TOP_SOURCES_LIMIT = 10


def _empty_mapping() -> Mapping[str, int]:
    return MappingProxyType({})


def _freeze_int_mapping(value: Mapping[str, int]) -> Mapping[str, int]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class E5CorpusTopSource:
    """Source dominante dans un corpus E5 local."""

    source_path: str
    chunk_count: int
    source_extension: str | None = None

    def __post_init__(self) -> None:
        if not self.source_path:
            raise ValueError("E5CorpusTopSource.source_path must not be empty")
        if self.chunk_count <= 0:
            raise ValueError("E5CorpusTopSource.chunk_count must be positive")
        if self.source_extension is not None and not self.source_extension:
            raise ValueError("E5CorpusTopSource.source_extension must not be empty")

    def to_json_dict(self) -> dict[str, object | None]:
        """Convertit la source dominante vers JSON stable."""
        return {
            "source_path": self.source_path,
            "chunk_count": self.chunk_count,
            "source_extension": self.source_extension,
        }


@dataclass(frozen=True, slots=True)
class E5CorpusDiagnosticGateConfig:
    """Seuils optionnels pour rendre un diagnostic E5 actionnable."""

    min_chunks: int | None = None
    max_missing_source_metadata: int | None = None
    max_empty_texts: int | None = None
    max_dimension_mismatches: int | None = None
    fail_on_warning: bool = False

    def __post_init__(self) -> None:
        if self.min_chunks is not None and self.min_chunks < 0:
            raise ValueError("min_chunks must not be negative")
        for name in (
            "max_missing_source_metadata",
            "max_empty_texts",
            "max_dimension_mismatches",
        ):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must not be negative")

    @property
    def enabled(self) -> bool:
        """Indique si au moins un garde-fou est actif."""
        return any(
            (
                self.min_chunks is not None,
                self.max_missing_source_metadata is not None,
                self.max_empty_texts is not None,
                self.max_dimension_mismatches is not None,
                self.fail_on_warning,
            )
        )

    def to_json_dict(self) -> dict[str, object]:
        """Convertit la configuration gate vers JSON stable."""
        return {
            "min_chunks": self.min_chunks,
            "max_missing_source_metadata": self.max_missing_source_metadata,
            "max_empty_texts": self.max_empty_texts,
            "max_dimension_mismatches": self.max_dimension_mismatches,
            "fail_on_warning": self.fail_on_warning,
            "enabled": self.enabled,
        }


@dataclass(frozen=True, slots=True)
class E5CorpusDiagnosticGateResult:
    """Résultat d'évaluation des seuils sur un diagnostic E5."""

    config: E5CorpusDiagnosticGateConfig
    violations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "violations", tuple(self.violations))
        if any(not item for item in self.violations):
            raise ValueError("E5CorpusDiagnosticGateResult.violations must contain non-empty strings")

    @property
    def enabled(self) -> bool:
        """Indique si le gate a réellement été demandé."""
        return self.config.enabled

    @property
    def passed(self) -> bool:
        """Indique si le corpus respecte les seuils demandés."""
        return not self.violations

    def to_json_dict(self) -> dict[str, object]:
        """Convertit le résultat gate vers JSON stable."""
        return {
            "enabled": self.enabled,
            "passed": self.passed,
            "config": self.config.to_json_dict(),
            "violations": list(self.violations),
        }

    def to_text(self) -> str:
        """Produit une section texte stable pour la CLI."""
        lines = ["gate:", f"  enabled: {str(self.enabled)}", f"  passed: {str(self.passed)}"]
        if self.violations:
            lines.append("  violations:")
            for violation in self.violations:
                lines.append(f"    - {violation}")
        else:
            lines.append("  violations: none")
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class E5CorpusDiagnostics:
    """Diagnostic stable d'un index E5 local déjà chargé."""

    schema: str
    model: str
    backend: str
    tokenizer: str
    dimension: int
    chunk_count: int
    source_count: int
    extension_counts: Mapping[str, int] = field(default_factory=_empty_mapping)
    top_sources: tuple[E5CorpusTopSource, ...] = ()
    embedding_reused_count: int = 0
    embedding_embedded_count: int = 0
    embedding_reuse_unknown_count: int = 0
    missing_source_count: int = 0
    empty_text_count: int = 0
    wrong_dimension_count: int = 0

    def __post_init__(self) -> None:
        if not self.schema:
            raise ValueError("E5CorpusDiagnostics.schema must not be empty")
        if not self.model:
            raise ValueError("E5CorpusDiagnostics.model must not be empty")
        if not self.backend:
            raise ValueError("E5CorpusDiagnostics.backend must not be empty")
        if not self.tokenizer:
            raise ValueError("E5CorpusDiagnostics.tokenizer must not be empty")
        if self.dimension <= 0:
            raise ValueError("E5CorpusDiagnostics.dimension must be positive")
        if self.chunk_count < 0:
            raise ValueError("E5CorpusDiagnostics.chunk_count must not be negative")
        if self.source_count < 0:
            raise ValueError("E5CorpusDiagnostics.source_count must not be negative")
        for name in (
            "embedding_reused_count",
            "embedding_embedded_count",
            "embedding_reuse_unknown_count",
            "missing_source_count",
            "empty_text_count",
            "wrong_dimension_count",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"E5CorpusDiagnostics.{name} must not be negative")
        object.__setattr__(self, "extension_counts", _freeze_int_mapping(self.extension_counts))
        object.__setattr__(self, "top_sources", tuple(self.top_sources))

    @property
    def has_warnings(self) -> bool:
        """Indique si le diagnostic contient des anomalies à vérifier."""
        return any(
            (
                self.missing_source_count,
                self.empty_text_count,
                self.wrong_dimension_count,
            )
        )

    def to_json_dict(self) -> dict[str, object]:
        """Convertit le diagnostic vers JSON stable."""
        return {
            "schema": self.schema,
            "model": self.model,
            "backend": self.backend,
            "tokenizer": self.tokenizer,
            "dimension": self.dimension,
            "chunk_count": self.chunk_count,
            "source_count": self.source_count,
            "extension_counts": dict(self.extension_counts),
            "top_sources": [item.to_json_dict() for item in self.top_sources],
            "embedding_reused_count": self.embedding_reused_count,
            "embedding_embedded_count": self.embedding_embedded_count,
            "embedding_reuse_unknown_count": self.embedding_reuse_unknown_count,
            "missing_source_count": self.missing_source_count,
            "empty_text_count": self.empty_text_count,
            "wrong_dimension_count": self.wrong_dimension_count,
            "has_warnings": self.has_warnings,
        }

    def to_text(self) -> str:
        """Produit un rapport texte compact et stable."""
        lines = [
            f"schema: {self.schema}",
            f"model: {self.model}",
            f"backend: {self.backend}",
            f"tokenizer: {self.tokenizer}",
            f"dimension: {self.dimension}",
            f"chunk_count: {self.chunk_count}",
            f"source_count: {self.source_count}",
            "extensions:",
        ]
        if self.extension_counts:
            for extension, count in self.extension_counts.items():
                lines.append(f"  {extension}: {count}")
        else:
            lines.append("  none: 0")

        lines.append("top_sources:")
        if self.top_sources:
            for source in self.top_sources:
                extension = f" ({source.source_extension})" if source.source_extension else ""
                lines.append(f"  {source.source_path}: {source.chunk_count}{extension}")
        else:
            lines.append("  none: 0")

        lines.extend(
            [
                "embedding_reuse:",
                f"  reused: {self.embedding_reused_count}",
                f"  embedded: {self.embedding_embedded_count}",
                f"  unknown: {self.embedding_reuse_unknown_count}",
                "health:",
                f"  missing_source_path: {self.missing_source_count}",
                f"  empty_text: {self.empty_text_count}",
                f"  wrong_dimension: {self.wrong_dimension_count}",
                f"  warnings: {str(self.has_warnings)}",
            ]
        )
        return "\n".join(lines)


def inspect_e5_corpus(
    index: E5CorpusIndex,
    *,
    top_sources_limit: int | None = DEFAULT_E5_CORPUS_TOP_SOURCES_LIMIT,
) -> E5CorpusDiagnostics:
    """Calcule un diagnostic local sans modifier l'index ni son format."""
    if top_sources_limit is not None and top_sources_limit <= 0:
        raise ValueError("top_sources_limit must be positive or None")

    extension_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    source_extensions: dict[str, str | None] = {}
    embedding_reused_count = 0
    embedding_embedded_count = 0
    embedding_reuse_unknown_count = 0
    missing_source_count = 0
    empty_text_count = 0
    wrong_dimension_count = 0

    for item in index.embeddings:
        if not item.text.strip():
            empty_text_count += 1
        if item.dimension != index.dimension:
            wrong_dimension_count += 1

        metadata = dict(item.metadata)
        source_path = _optional_str(metadata.get("source_path"))
        source_extension = _source_extension(metadata, source_path)
        extension_counts[source_extension or "unknown"] += 1

        if source_path is None:
            missing_source_count += 1
        else:
            source_counts[source_path] += 1
            source_extensions.setdefault(source_path, source_extension)

        reused = metadata.get("embedding_reused")
        if reused is True:
            embedding_reused_count += 1
        elif reused is False:
            embedding_embedded_count += 1
        else:
            embedding_reuse_unknown_count += 1

    top_sources = _top_sources(source_counts, source_extensions, top_sources_limit=top_sources_limit)
    return E5CorpusDiagnostics(
        schema=index.schema,
        model=index.model,
        backend=index.backend,
        tokenizer=index.tokenizer,
        dimension=index.dimension,
        chunk_count=index.size,
        source_count=len(source_counts),
        extension_counts=dict(sorted(extension_counts.items())),
        top_sources=top_sources,
        embedding_reused_count=embedding_reused_count,
        embedding_embedded_count=embedding_embedded_count,
        embedding_reuse_unknown_count=embedding_reuse_unknown_count,
        missing_source_count=missing_source_count,
        empty_text_count=empty_text_count,
        wrong_dimension_count=wrong_dimension_count,
    )


def evaluate_e5_corpus_diagnostic_gate(
    diagnostics: E5CorpusDiagnostics,
    config: E5CorpusDiagnosticGateConfig,
) -> E5CorpusDiagnosticGateResult:
    """Évalue des seuils optionnels sans modifier le corpus inspecté."""
    violations: list[str] = []
    if config.min_chunks is not None and diagnostics.chunk_count < config.min_chunks:
        violations.append(f"chunk_count {diagnostics.chunk_count} < min_chunks {config.min_chunks}")
    if (
        config.max_missing_source_metadata is not None
        and diagnostics.missing_source_count > config.max_missing_source_metadata
    ):
        violations.append(
            "missing_source_count "
            f"{diagnostics.missing_source_count} > "
            f"max_missing_source_metadata {config.max_missing_source_metadata}"
        )
    if config.max_empty_texts is not None and diagnostics.empty_text_count > config.max_empty_texts:
        violations.append(f"empty_text_count {diagnostics.empty_text_count} > max_empty_texts {config.max_empty_texts}")
    if (
        config.max_dimension_mismatches is not None
        and diagnostics.wrong_dimension_count > config.max_dimension_mismatches
    ):
        violations.append(
            "wrong_dimension_count "
            f"{diagnostics.wrong_dimension_count} > "
            f"max_dimension_mismatches {config.max_dimension_mismatches}"
        )
    if config.fail_on_warning and diagnostics.has_warnings:
        violations.append("diagnostics has warnings")
    return E5CorpusDiagnosticGateResult(config=config, violations=tuple(violations))



def _top_sources(
    source_counts: Mapping[str, int],
    source_extensions: Mapping[str, str | None],
    *,
    top_sources_limit: int | None,
) -> tuple[E5CorpusTopSource, ...]:
    ranked = sorted(source_counts.items(), key=lambda item: (-item[1], item[0]))
    if top_sources_limit is not None:
        ranked = ranked[:top_sources_limit]
    return tuple(
        E5CorpusTopSource(
            source_path=source_path,
            chunk_count=count,
            source_extension=source_extensions.get(source_path),
        )
        for source_path, count in ranked
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _source_extension(metadata: Mapping[str, Any], source_path: str | None) -> str | None:
    metadata_extension = _optional_str(metadata.get("source_extension"))
    if metadata_extension is not None:
        return metadata_extension.lower()
    if source_path is None:
        return None
    suffix = Path(source_path).suffix.lower()
    return suffix or None
