"""OpenVINO embedding adapter boundary for hydrated SQL context fragments.

0118 keeps real model execution behind an injected executor.  The adapter builds
bounded embedding texts from SQLContextHydrator fragments, calls the injected
executor, validates vector shape/normalization, and returns immutable embedding
batches suitable for a later Qdrant projection adapter.  It does not import the
OpenVINO package directly; the real import remains isolated in
src/inference/openvino_runtime.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math
from pathlib import Path
import re
from typing import Protocol, Sequence

from context.sql_context_hydrator import HydratedSqlContextFragment, SqlHydratedContextBundle

_TARGET_SCHEMA = "missipy.openvino_embedding.target.v1"
_TEXT_SCHEMA = "missipy.openvino_embedding.text.v1"
_VECTOR_SCHEMA = "missipy.openvino_embedding.vector.v1"
_BATCH_SCHEMA = "missipy.openvino_embedding.batch.v1"
_ALLOWED_ROLES = frozenset({"passage", "query"})
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")


class OpenVINOEmbeddingExecutor(Protocol):
    """Injected execution membrane for a real or test embedding backend."""

    def embed_texts(
        self,
        texts: Sequence[str],
        *,
        target: OpenVINOEmbeddingRuntimeTarget,
        policy: OpenVINOEmbeddingPolicy,
    ) -> Sequence[Sequence[float]]: ...


@dataclass(frozen=True, slots=True)
class OpenVINOEmbeddingRuntimeTarget:
    """Explicit local OpenVINO embedding runtime target.

    The default model path documents the user's local multilingual-e5-small
    OpenVINO export.  The target is data only; it does not load OpenVINO.
    """

    model_dir: str = "/home/eric/model/openvino/multilingual-e5-small"
    device: str = "CPU"
    dimension: int = 384
    normalized: bool = True
    backend_ref: str = "openvino:model:multilingual-e5-small"

    def __post_init__(self) -> None:
        _require_non_empty("model_dir", self.model_dir)
        _require_non_empty("device", self.device)
        _require_typed_ref("backend_ref", self.backend_ref)
        if self.dimension <= 0:
            raise ValueError("dimension must be > 0")

    @property
    def model_xml_path(self) -> str:
        return str(Path(self.model_dir) / "openvino_model.xml")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _TARGET_SCHEMA,
            "model_dir": self.model_dir,
            "model_xml_path": self.model_xml_path,
            "device": self.device,
            "dimension": self.dimension,
            "normalized": self.normalized,
            "backend_ref": self.backend_ref,
            "runtime_import": "src/inference/openvino_runtime.py",
        }


@dataclass(frozen=True, slots=True)
class OpenVINOEmbeddingPolicy:
    """Bounded deterministic embedding policy for hydrated fragments."""

    max_fragments: int = 64
    max_text_chars: int = 8_192
    expected_dimension: int = 384
    require_normalized: bool = True
    passage_prefix: str = "passage: "
    query_prefix: str = "query: "
    normalization_tolerance: float = 1e-4

    def __post_init__(self) -> None:
        if self.max_fragments <= 0:
            raise ValueError("max_fragments must be > 0")
        if self.max_text_chars <= 0:
            raise ValueError("max_text_chars must be > 0")
        if self.expected_dimension <= 0:
            raise ValueError("expected_dimension must be > 0")
        if self.normalization_tolerance <= 0:
            raise ValueError("normalization_tolerance must be > 0")
        _require_non_empty("passage_prefix", self.passage_prefix)
        _require_non_empty("query_prefix", self.query_prefix)


@dataclass(frozen=True, slots=True)
class OpenVINOEmbeddingText:
    """Text item to send through the embedding execution membrane."""

    source_ref: str
    text: str
    role: str = "passage"
    title: str = ""
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    truncated: bool = False

    def __post_init__(self) -> None:
        _require_typed_ref("source_ref", self.source_ref)
        _require_non_empty("text", self.text)
        if self.role not in _ALLOWED_ROLES:
            raise ValueError("role must be passage or query")
        if self.title:
            _require_non_empty("title", self.title)
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def embedding_ref(self) -> str:
        digest = hashlib.sha256()
        digest.update(self.source_ref.encode("utf-8"))
        digest.update(b"\0")
        digest.update(self.role.encode("utf-8"))
        digest.update(b"\0")
        digest.update(self.text.encode("utf-8"))
        return f"embedding:{self.role}:{digest.hexdigest()[:16]}"

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _TEXT_SCHEMA,
            "source_ref": self.source_ref,
            "embedding_ref": self.embedding_ref,
            "role": self.role,
            "title": self.title,
            "text": self.text,
            "metadata": dict(self.metadata),
            "truncated": self.truncated,
        }


@dataclass(frozen=True, slots=True)
class OpenVINOEmbeddingVector:
    """Validated embedding vector tied to a source context ref."""

    embedding_ref: str
    source_ref: str
    vector: tuple[float, ...]
    backend_ref: str
    role: str = "passage"
    normalized: bool = True
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("embedding_ref", self.embedding_ref)
        _require_typed_ref("source_ref", self.source_ref)
        _require_typed_ref("backend_ref", self.backend_ref)
        if self.role not in _ALLOWED_ROLES:
            raise ValueError("role must be passage or query")
        if not self.vector:
            raise ValueError("vector must not be empty")
        object.__setattr__(self, "vector", tuple(float(value) for value in self.vector))
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def dimension(self) -> int:
        return len(self.vector)

    @property
    def l2_norm(self) -> float:
        return _l2_norm(self.vector)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _VECTOR_SCHEMA,
            "embedding_ref": self.embedding_ref,
            "source_ref": self.source_ref,
            "backend_ref": self.backend_ref,
            "role": self.role,
            "dimension": self.dimension,
            "normalized": self.normalized,
            "l2_norm": self.l2_norm,
            "metadata": dict(self.metadata),
            "vector": list(self.vector),
        }


@dataclass(frozen=True, slots=True)
class OpenVINOEmbeddingBatch:
    """Serializable embedding batch for later Qdrant projection."""

    target: OpenVINOEmbeddingRuntimeTarget
    vectors: tuple[OpenVINOEmbeddingVector, ...]
    capped: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "vectors", tuple(self.vectors))

    @property
    def vector_count(self) -> int:
        return len(self.vectors)

    @property
    def embedding_refs(self) -> tuple[str, ...]:
        return tuple(vector.embedding_ref for vector in self.vectors)

    @property
    def source_refs(self) -> tuple[str, ...]:
        return tuple(vector.source_ref for vector in self.vectors)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _BATCH_SCHEMA,
            "target": self.target.to_mapping(),
            "vector_count": self.vector_count,
            "embedding_refs": list(self.embedding_refs),
            "source_refs": list(self.source_refs),
            "capped": self.capped,
            "vectors": [vector.to_mapping() for vector in self.vectors],
        }


class OpenVINOEmbeddingAdapter:
    """Build embedding requests from hydrated SQL fragments using an executor."""

    def __init__(
        self,
        executor: OpenVINOEmbeddingExecutor,
        target: OpenVINOEmbeddingRuntimeTarget | None = None,
        policy: OpenVINOEmbeddingPolicy | None = None,
    ) -> None:
        self._executor = executor
        self._target = target or OpenVINOEmbeddingRuntimeTarget()
        self._policy = policy or OpenVINOEmbeddingPolicy()
        if self._target.dimension != self._policy.expected_dimension:
            raise ValueError("target dimension must match expected_dimension")

    @property
    def target(self) -> OpenVINOEmbeddingRuntimeTarget:
        return self._target

    @property
    def policy(self) -> OpenVINOEmbeddingPolicy:
        return self._policy

    def embed_hydrated_bundle(self, bundle: SqlHydratedContextBundle) -> OpenVINOEmbeddingBatch:
        texts, capped = build_embedding_texts_from_hydrated_bundle(bundle, self._policy)
        raw_vectors = self._executor.embed_texts(
            tuple(text.text for text in texts),
            target=self._target,
            policy=self._policy,
        )
        if len(raw_vectors) != len(texts):
            raise ValueError("executor must return one vector per embedding text")
        vectors = tuple(
            build_embedding_vector(text, raw_vector, self._target, self._policy)
            for text, raw_vector in zip(texts, raw_vectors, strict=True)
        )
        return OpenVINOEmbeddingBatch(target=self._target, vectors=vectors, capped=capped)


def build_embedding_texts_from_hydrated_bundle(
    bundle: SqlHydratedContextBundle,
    policy: OpenVINOEmbeddingPolicy | None = None,
    *,
    role: str = "passage",
) -> tuple[tuple[OpenVINOEmbeddingText, ...], bool]:
    """Build bounded embedding texts from a hydrated SQL context bundle."""

    if role not in _ALLOWED_ROLES:
        raise ValueError("role must be passage or query")
    effective = policy or OpenVINOEmbeddingPolicy()
    texts: list[OpenVINOEmbeddingText] = []
    capped = bundle.capped
    prefix = effective.query_prefix if role == "query" else effective.passage_prefix
    for fragment in bundle.fragments:
        if len(texts) >= effective.max_fragments:
            capped = True
            break
        text, truncated = _bounded_text(prefix, fragment, effective.max_text_chars)
        texts.append(
            OpenVINOEmbeddingText(
                source_ref=fragment.projection_ref,
                text=text,
                role=role,
                title=fragment.title,
                metadata=(
                    ("context_ref", fragment.context_ref),
                    ("kind", fragment.kind),
                    ("relation", fragment.relation),
                ),
                truncated=truncated or fragment.truncated,
            )
        )
    return tuple(texts), capped


def build_embedding_vector(
    text: OpenVINOEmbeddingText,
    raw_vector: Sequence[float],
    target: OpenVINOEmbeddingRuntimeTarget,
    policy: OpenVINOEmbeddingPolicy | None = None,
) -> OpenVINOEmbeddingVector:
    """Validate and wrap a raw vector returned by the injected executor."""

    effective = policy or OpenVINOEmbeddingPolicy(expected_dimension=target.dimension)
    vector = tuple(float(value) for value in raw_vector)
    if len(vector) != effective.expected_dimension:
        raise ValueError("embedding vector dimension does not match expected_dimension")
    norm = _l2_norm(vector)
    normalized = math.isclose(norm, 1.0, rel_tol=effective.normalization_tolerance, abs_tol=effective.normalization_tolerance)
    if effective.require_normalized and not normalized:
        raise ValueError("embedding vector must be normalized")
    return OpenVINOEmbeddingVector(
        embedding_ref=text.embedding_ref,
        source_ref=text.source_ref,
        vector=vector,
        backend_ref=target.backend_ref,
        role=text.role,
        normalized=normalized,
        metadata=text.metadata,
    )


def local_multilingual_e5_openvino_target(*, device: str = "CPU") -> OpenVINOEmbeddingRuntimeTarget:
    """Return the documented local multilingual-e5-small OpenVINO target."""

    return OpenVINOEmbeddingRuntimeTarget(device=device)


def _bounded_text(
    prefix: str,
    fragment: HydratedSqlContextFragment,
    max_chars: int,
) -> tuple[str, bool]:
    body = f"{prefix}{fragment.title}\n{fragment.body}"
    if len(body) <= max_chars:
        return body, False
    return body[:max_chars], True


def _l2_norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _normalize_metadata(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    seen: set[str] = set()
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        if key in seen:
            raise ValueError("metadata keys must be unique")
        seen.add(key)
        normalized.append((key, value))
    return tuple(sorted(normalized))


def _require_typed_ref(name: str, value: str) -> None:
    _require_non_empty(name, value)
    if not _TYPED_REF_RE.match(value):
        raise ValueError(f"{name} must be a typed reference")


def _require_non_empty(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must not be empty")
