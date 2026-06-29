from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .e5_corpus import E5CorpusDocument
from .e5_text import E5Text

SUPPORTED_E5_SOURCE_EXTENSIONS: tuple[str, ...] = (".md", ".markdown", ".txt")


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class E5SourceDocument:
    """Document texte local lu depuis un fichier Markdown/TXT."""

    path: str
    text: str
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("E5SourceDocument.path must not be empty")
        if not self.text.strip():
            raise ValueError("E5SourceDocument.text must not be empty")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    @property
    def source_id(self) -> str:
        """Identifiant stable court du fichier source."""

        digest = sha256(self.path.encode("utf-8")).hexdigest()[:12]
        return f"source-{digest}"


@dataclass(frozen=True, slots=True)
class E5TextChunk:
    """Chunk de texte prêt à devenir un passage E5."""

    id: str
    text: str
    source_path: str
    chunk_index: int
    start_line: int
    end_line: int
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("E5TextChunk.id must not be empty")
        if not self.text.strip():
            raise ValueError("E5TextChunk.text must not be empty")
        if not self.source_path:
            raise ValueError("E5TextChunk.source_path must not be empty")
        if self.chunk_index <= 0:
            raise ValueError("E5TextChunk.chunk_index must be positive")
        if self.start_line <= 0 or self.end_line < self.start_line:
            raise ValueError("E5TextChunk line range is invalid")
        object.__setattr__(self, "text", self.text.strip())
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def to_corpus_document(self) -> E5CorpusDocument:
        """Convertit le chunk en document passage pour E5CorpusBuilder."""

        metadata = {
            "source_path": self.source_path,
            "chunk_index": self.chunk_index,
            "start_line": self.start_line,
            "end_line": self.end_line,
            **dict(self.metadata),
        }
        return E5CorpusDocument(
            id=self.id,
            text=E5Text.passage(self.text),
            metadata=metadata,
        )


def discover_e5_source_files(
    paths: Sequence[str | Path],
    *,
    extensions: Sequence[str] = SUPPORTED_E5_SOURCE_EXTENSIONS,
    recursive: bool = True,
) -> tuple[Path, ...]:
    """Découvre les fichiers texte indexables avec ordre stable."""

    normalized_extensions = _normalize_extensions(extensions)
    files: set[Path] = set()
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file():
            if path.suffix.lower() in normalized_extensions:
                files.add(path.resolve())
            continue
        if path.is_dir():
            pattern = "**/*" if recursive else "*"
            for candidate in path.glob(pattern):
                if candidate.is_file() and candidate.suffix.lower() in normalized_extensions:
                    files.add(candidate.resolve())
            continue
        raise FileNotFoundError(path)
    return tuple(sorted(files, key=lambda item: str(item)))


def load_e5_source_documents(
    paths: Sequence[str | Path],
    *,
    extensions: Sequence[str] = SUPPORTED_E5_SOURCE_EXTENSIONS,
    recursive: bool = True,
    root: str | Path | None = None,
) -> tuple[E5SourceDocument, ...]:
    """Charge des fichiers Markdown/TXT en documents sources."""

    files = discover_e5_source_files(paths, extensions=extensions, recursive=recursive)
    base = Path(root).resolve() if root is not None else None
    documents: list[E5SourceDocument] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            continue
        source_path = _stable_path(path, base=base)
        documents.append(
            E5SourceDocument(
                path=source_path,
                text=text,
                metadata={"source_extension": path.suffix.lower()},
            )
        )
    return tuple(documents)


def chunk_e5_source_document(
    document: E5SourceDocument,
    *,
    max_chars: int = 1200,
    overlap_paragraphs: int = 0,
) -> tuple[E5TextChunk, ...]:
    """Découpe un document source en chunks déterministes par paragraphes."""

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap_paragraphs < 0:
        raise ValueError("overlap_paragraphs must be zero or positive")

    paragraphs = _paragraphs(document.text)
    if not paragraphs:
        return ()

    chunks: list[E5TextChunk] = []
    position = 0
    while position < len(paragraphs):
        paragraph = paragraphs[position]
        if len(paragraph.text) > max_chars:
            for split_text, start_line, end_line in _split_long_paragraph(paragraph, max_chars=max_chars):
                chunks.append(
                    _make_chunk_from_text(
                        document,
                        split_text,
                        chunk_index=len(chunks) + 1,
                        start_line=start_line,
                        end_line=end_line,
                    )
                )
            position += 1
            continue

        window: list[_Paragraph] = [paragraph]
        cursor = position + 1
        while cursor < len(paragraphs):
            candidate = [*window, paragraphs[cursor]]
            if _joined_length(candidate) > max_chars:
                break
            window.append(paragraphs[cursor])
            cursor += 1

        chunks.append(_make_chunk(document, tuple(window), chunk_index=len(chunks) + 1))
        if cursor >= len(paragraphs):
            break
        next_position = cursor - overlap_paragraphs
        if next_position <= position:
            next_position = position + 1
        position = next_position

    return tuple(chunks)

def chunk_e5_sources(
    documents: Sequence[E5SourceDocument],
    *,
    max_chars: int = 1200,
    overlap_paragraphs: int = 0,
) -> tuple[E5TextChunk, ...]:
    """Découpe plusieurs sources en chunks dans un ordre déterministe."""

    chunks: list[E5TextChunk] = []
    for document in documents:
        chunks.extend(chunk_e5_source_document(document, max_chars=max_chars, overlap_paragraphs=overlap_paragraphs))
    return tuple(chunks)


def load_e5_corpus_documents_from_sources(
    paths: Sequence[str | Path],
    *,
    extensions: Sequence[str] = SUPPORTED_E5_SOURCE_EXTENSIONS,
    recursive: bool = True,
    root: str | Path | None = None,
    max_chars: int = 1200,
    overlap_paragraphs: int = 0,
) -> tuple[E5CorpusDocument, ...]:
    """Charge, découpe et convertit des sources locales en passages de corpus."""

    sources = load_e5_source_documents(paths, extensions=extensions, recursive=recursive, root=root)
    return tuple(
        chunk.to_corpus_document()
        for chunk in chunk_e5_sources(sources, max_chars=max_chars, overlap_paragraphs=overlap_paragraphs)
    )


@dataclass(frozen=True, slots=True)
class _Paragraph:
    text: str
    start_line: int
    end_line: int


def _normalize_extensions(extensions: Sequence[str]) -> frozenset[str]:
    normalized = []
    for extension in extensions:
        item = extension.strip().lower()
        if not item:
            continue
        if not item.startswith("."):
            item = f".{item}"
        normalized.append(item)
    if not normalized:
        raise ValueError("at least one extension is required")
    return frozenset(normalized)


def _stable_path(path: Path, *, base: Path | None) -> str:
    if base is None:
        return str(path)
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def _paragraphs(text: str) -> tuple[_Paragraph, ...]:
    paragraphs: list[_Paragraph] = []
    buffer: list[str] = []
    start_line = 0
    last_line = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.strip():
            if not buffer:
                start_line = line_number
            buffer.append(line.rstrip())
            last_line = line_number
            continue
        if buffer:
            paragraphs.append(_Paragraph(text="\n".join(buffer).strip(), start_line=start_line, end_line=last_line))
            buffer = []
    if buffer:
        paragraphs.append(_Paragraph(text="\n".join(buffer).strip(), start_line=start_line, end_line=last_line))
    return tuple(paragraphs)


def _joined_length(paragraphs: Sequence[_Paragraph]) -> int:
    return len("\n\n".join(item.text for item in paragraphs))


def _join_paragraphs(paragraphs: Sequence[_Paragraph]) -> str:
    return "\n\n".join(item.text for item in paragraphs).strip()


def _overlap_tail(paragraphs: Sequence[_Paragraph], overlap_paragraphs: int) -> list[_Paragraph]:
    if overlap_paragraphs <= 0:
        return []
    return list(paragraphs[-overlap_paragraphs:])


def _make_chunk(document: E5SourceDocument, paragraphs: Sequence[_Paragraph], *, chunk_index: int) -> E5TextChunk:
    return _make_chunk_from_text(
        document,
        _join_paragraphs(paragraphs),
        chunk_index=chunk_index,
        start_line=paragraphs[0].start_line,
        end_line=paragraphs[-1].end_line,
    )


def _make_chunk_from_text(
    document: E5SourceDocument,
    text: str,
    *,
    chunk_index: int,
    start_line: int,
    end_line: int,
) -> E5TextChunk:
    digest = sha256(f"{document.path}\n{chunk_index}\n{text}".encode("utf-8")).hexdigest()[:12]
    return E5TextChunk(
        id=f"chunk-{chunk_index:06d}-{digest}",
        text=text,
        source_path=document.path,
        chunk_index=chunk_index,
        start_line=start_line,
        end_line=end_line,
        metadata={"source_id": document.source_id, **dict(document.metadata)},
    )


def _split_long_paragraph(paragraph: _Paragraph, *, max_chars: int) -> Iterable[tuple[str, int, int]]:
    words = paragraph.text.split()
    if not words:
        return ()
    chunks: list[tuple[str, int, int]] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if current and len(candidate) > max_chars:
            chunks.append((" ".join(current), paragraph.start_line, paragraph.end_line))
            current = [word]
        else:
            current.append(word)
    if current:
        chunks.append((" ".join(current), paragraph.start_line, paragraph.end_line))
    return tuple(chunks)
