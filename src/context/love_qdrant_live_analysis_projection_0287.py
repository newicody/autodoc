"""Async live projection of SQL authority analyses to named Qdrant vectors.

The adapter reuses the installed asynchronous OpenVINO E5 pipeline, the exact
sparse lexical builder used by hybrid retrieval and the existing qdrant-client
execution membrane.  SQL remains authoritative: Qdrant receives only stable
references, scope fields, content digest and reconstructible vectors.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import hashlib
import math
from typing import Any, Protocol, runtime_checkable

from context.context_revision_sql_authority_0287 import (
    VECTOR_PROJECTION_METADATA_SCHEMA,
    ContextAuthorityObject,
    ContextRevision,
    VectorProjectionMetadata,
)
from context.hybrid_retrieval_sql_rehydration_0287 import build_sparse_lexical_query
from context.love_openvino_e5_async_query_adapter_0287 import AsyncEmbeddingPipeline

LOVE_QDRANT_LIVE_ANALYSIS_PROJECTION_SCHEMA = (
    "missipy.love.qdrant_live_analysis_projection.v1"
)
LOVE_ANALYSIS_PROJECTION_RECEIPT_SCHEMA = (
    "missipy.love.analysis_projection_receipt.v1"
)


class LoveQdrantLiveAnalysisProjectionError(RuntimeError):
    """Raised when live projection violates SQL, E5 or Qdrant boundaries."""


@runtime_checkable
class NamedHybridProjectionWriter(Protocol):
    """Narrow injected write subset of the existing Qdrant executor."""

    def upsert_named_hybrid_point(
        self,
        *,
        collection_name: str,
        point_id: str,
        dense_vector_name: str,
        dense_values: tuple[float, ...],
        sparse_vector_name: str,
        sparse_indices: tuple[int, ...],
        sparse_values: tuple[float, ...],
        payload: Mapping[str, object],
        dense_dimension: int = 384,
    ) -> Any: ...


@dataclass(frozen=True, slots=True)
class LoveQdrantLiveAnalysisProjectionSettings:
    """Locked identities for one installed E5/Qdrant projection surface."""

    schema: str = LOVE_QDRANT_LIVE_ANALYSIS_PROJECTION_SCHEMA
    collection_name: str = "autodoc_context_e5_384_hybrid_v1"
    dense_vector_name: str = "dense_e5_v1"
    sparse_vector_name: str = "sparse_lexical_v1"
    embedding_profile_ref: str = (
        "embedding-profile:multilingual-e5-small-passage"
    )
    model_ref: str = "model:multilingual-e5-small"
    model_revision: str = "installed"
    backend_ref: str = "openvino:multilingual-e5-small"
    passage_prefix: str = "passage:"
    dimension: int = 384

    def __post_init__(self) -> None:
        if self.schema != LOVE_QDRANT_LIVE_ANALYSIS_PROJECTION_SCHEMA:
            raise LoveQdrantLiveAnalysisProjectionError(
                "unsupported live projection settings schema"
            )
        for name in ("embedding_profile_ref", "model_ref", "backend_ref"):
            _require_typed_ref(name, getattr(self, name))
        for name in ("dense_vector_name", "sparse_vector_name"):
            _require_identifier(name, getattr(self, name))
        if self.dense_vector_name == self.sparse_vector_name:
            raise LoveQdrantLiveAnalysisProjectionError(
                "dense and sparse vector names must differ"
            )
        if not self.collection_name.strip():
            raise LoveQdrantLiveAnalysisProjectionError(
                "collection_name must not be empty"
            )
        if not self.model_revision.strip():
            raise LoveQdrantLiveAnalysisProjectionError(
                "model_revision must not be empty"
            )
        if not self.passage_prefix.strip():
            raise LoveQdrantLiveAnalysisProjectionError(
                "passage_prefix must not be empty"
            )
        if self.dimension != 384:
            raise LoveQdrantLiveAnalysisProjectionError(
                "multilingual-e5-small dimension must be 384"
            )


@dataclass(frozen=True, slots=True)
class LoveQdrantLiveProjectionIdentity:
    """Deterministic SQL/Qdrant identity for one live projection."""

    projection_ref: str
    point_id: str

    def __post_init__(self) -> None:
        _require_typed_ref("projection_ref", self.projection_ref)
        _require_typed_ref("point_id", self.point_id)


def build_love_qdrant_live_projection_identity_from_refs(
    *,
    object_ref: str,
    content_digest: str,
    revision_ref: str,
    collection_name: str,
) -> LoveQdrantLiveProjectionIdentity:
    """Build immutable identities from already-authorized typed references."""

    _require_typed_ref("object_ref", object_ref)
    _require_typed_ref("revision_ref", revision_ref)
    if (
        not isinstance(content_digest, str)
        or not content_digest.startswith("sha256:")
        or len(content_digest) != 71
    ):
        raise LoveQdrantLiveAnalysisProjectionError(
            "content_digest must be a sha256:* digest"
        )
    if not isinstance(collection_name, str) or not collection_name.strip():
        raise LoveQdrantLiveAnalysisProjectionError(
            "collection_name must not be empty"
        )
    collection = collection_name.strip()
    projection_ref = _digest_ref(
        "vector-projection:",
        object_ref,
        content_digest,
        revision_ref,
        collection,
    )
    point_id = _digest_ref("qdrant-point:", projection_ref, collection)
    return LoveQdrantLiveProjectionIdentity(
        projection_ref=projection_ref,
        point_id=point_id,
    )


def build_love_qdrant_live_projection_identity(
    authority_object: ContextAuthorityObject,
    *,
    revision: ContextRevision,
    collection_name: str,
) -> LoveQdrantLiveProjectionIdentity:
    """Build the same immutable identities used by the live writer."""

    if not isinstance(authority_object, ContextAuthorityObject):
        raise LoveQdrantLiveAnalysisProjectionError(
            "authority_object must be a ContextAuthorityObject"
        )
    if not isinstance(revision, ContextRevision):
        raise LoveQdrantLiveAnalysisProjectionError(
            "revision must be a ContextRevision"
        )
    _require_active_membership(authority_object, revision)
    return build_love_qdrant_live_projection_identity_from_refs(
        object_ref=authority_object.object_ref,
        content_digest=authority_object.content_digest,
        revision_ref=revision.revision_ref,
        collection_name=collection_name,
    )


class LoveQdrantLiveAnalysisProjection:
    """Project one already-persisted SQL authority object through real ports."""

    def __init__(
        self,
        *,
        pipeline: AsyncEmbeddingPipeline,
        writer: NamedHybridProjectionWriter,
        settings: LoveQdrantLiveAnalysisProjectionSettings | None = None,
        receipt_factory: Callable[..., Any] | None = None,
    ) -> None:
        if not isinstance(pipeline, AsyncEmbeddingPipeline):
            raise LoveQdrantLiveAnalysisProjectionError(
                "pipeline must expose async embed_text()"
            )
        if not isinstance(writer, NamedHybridProjectionWriter):
            raise LoveQdrantLiveAnalysisProjectionError(
                "writer must expose upsert_named_hybrid_point()"
            )
        self._pipeline = pipeline
        self._writer = writer
        self._settings = settings or LoveQdrantLiveAnalysisProjectionSettings()
        self._receipt_factory = receipt_factory or _default_receipt_factory

    @property
    def settings(self) -> LoveQdrantLiveAnalysisProjectionSettings:
        return self._settings

    def read_named_reference_point(
        self,
        *,
        collection_name: str,
        point_id: str,
    ) -> object | None:
        """Delegate exact reference-only readback to the existing writer."""

        reader = getattr(self._writer, "read_named_reference_point", None)
        if not callable(reader):
            raise LoveQdrantLiveAnalysisProjectionError(
                "writer does not expose reference-only point readback"
            )
        return reader(
            collection_name=collection_name,
            point_id=point_id,
        )

    async def project(
        self,
        authority_object: ContextAuthorityObject,
        *,
        revision: ContextRevision,
        branch_ref: str,
        project_ref: str,
        conversation_ref: str,
        specialist_ref: str,
        laboratory_ref: str,
        security_scope: str,
        projected_at: str | None = None,
    ) -> Any:
        """Embed one SQL object and upsert one named dense+sparse Qdrant point."""

        for name, value in (
            ("branch_ref", branch_ref),
            ("project_ref", project_ref),
            ("conversation_ref", conversation_ref),
            ("specialist_ref", specialist_ref),
            ("laboratory_ref", laboratory_ref),
            ("security_scope", security_scope),
        ):
            _require_typed_ref(name, value)
        _require_active_membership(authority_object, revision)
        if not authority_object.body.strip():
            raise LoveQdrantLiveAnalysisProjectionError(
                "live analysis projection requires SQL-authoritative text body"
            )

        identity = build_love_qdrant_live_projection_identity(
            authority_object,
            revision=revision,
            collection_name=self._settings.collection_name,
        )
        projection_ref = identity.projection_ref
        point_id = identity.point_id
        plain_text = f"{authority_object.title.strip()}\n\n{authority_object.body.strip()}"
        passage_text = _prefixed_passage(
            plain_text, self._settings.passage_prefix
        )
        result = await self._pipeline.embed_text(passage_text)
        dense_values = _validated_dense_values(
            result, expected_dimension=self._settings.dimension
        )
        sparse = build_sparse_lexical_query(
            plain_text,
            query_ref=projection_ref,
            vector_name=self._settings.sparse_vector_name,
        )
        contribution_kind = str(
            authority_object.metadata.get(
                "contribution_kind", authority_object.object_kind
            )
        )
        _require_identifier("contribution_kind", contribution_kind)
        payload: dict[str, object] = {
            "point_id": point_id,
            "sql_ref": authority_object.object_ref,
            "source_ref": authority_object.object_ref,
            "source_content_digest": authority_object.content_digest,
            "context_revision_ref": revision.revision_ref,
            "branch_ref": branch_ref,
            "project_ref": project_ref,
            "conversation_ref": conversation_ref,
            "artifact_kind": authority_object.object_kind,
            "contribution_kind": contribution_kind,
            "specialist_ref": specialist_ref,
            "laboratory_ref": laboratory_ref,
            "security_scope": security_scope,
            "valid": True,
            "superseded_by": "",
        }
        write_result = self._writer.upsert_named_hybrid_point(
            collection_name=self._settings.collection_name,
            point_id=point_id,
            dense_vector_name=self._settings.dense_vector_name,
            dense_values=dense_values,
            sparse_vector_name=self._settings.sparse_vector_name,
            sparse_indices=sparse.indices,
            sparse_values=sparse.weights,
            payload=payload,
            dense_dimension=self._settings.dimension,
        )
        if getattr(write_result, "acknowledged", False) is not True:
            raise LoveQdrantLiveAnalysisProjectionError(
                "Qdrant named hybrid write was not acknowledged"
            )
        if getattr(write_result, "point_id", point_id) != point_id:
            raise LoveQdrantLiveAnalysisProjectionError(
                "Qdrant write receipt point_id mismatch"
            )

        projection = VectorProjectionMetadata(
            schema=VECTOR_PROJECTION_METADATA_SCHEMA,
            projection_ref=projection_ref,
            source_ref=authority_object.object_ref,
            source_content_digest=authority_object.content_digest,
            embedding_profile_ref=self._settings.embedding_profile_ref,
            model_ref=self._settings.model_ref,
            model_revision=self._settings.model_revision,
            dimension=self._settings.dimension,
            normalized=True,
            vector_name=self._settings.dense_vector_name,
            collection_name=self._settings.collection_name,
            point_id=point_id,
            projection_state="active",
            projected_at=projected_at,
            metadata={
                "backend_ref": self._settings.backend_ref,
                "sparse_vector_name": self._settings.sparse_vector_name,
                "sparse_term_count": len(sparse.indices),
                "passage_prefix_applied": True,
                "reference_only_payload": True,
                "authoritative_body_in_qdrant": False,
            },
        )
        return self._receipt_factory(
            schema=LOVE_ANALYSIS_PROJECTION_RECEIPT_SCHEMA,
            projection=projection,
            openvino_e5_used=True,
            qdrant_write_performed=True,
            qdrant_returns_references_only=True,
            sql_remains_authority=True,
        )


def _default_receipt_factory(**kwargs: object) -> Any:
    from context.love_memory_evidence_liaison_synthesis_0287 import (
        LoveAnalysisProjectionReceipt,
    )

    return LoveAnalysisProjectionReceipt(**kwargs)


def _require_active_membership(
    authority_object: ContextAuthorityObject,
    revision: ContextRevision,
) -> None:
    membership = next(
        (
            item
            for item in revision.memberships
            if item.object_ref == authority_object.object_ref
        ),
        None,
    )
    if membership is None or membership.state != "active":
        raise LoveQdrantLiveAnalysisProjectionError(
            "authority object must be an active member of the revision"
        )


def _validated_dense_values(
    result: object,
    *,
    expected_dimension: int,
) -> tuple[float, ...]:
    vector = getattr(result, "vector", None)
    if vector is None:
        raise LoveQdrantLiveAnalysisProjectionError(
            "embedding pipeline result must expose vector"
        )
    values = tuple(float(value) for value in getattr(vector, "values", ()))
    dimension = getattr(vector, "dimension", len(values))
    normalized = getattr(vector, "normalized", False)
    if dimension != expected_dimension or len(values) != expected_dimension:
        raise LoveQdrantLiveAnalysisProjectionError(
            "E5 passage vector dimension differs from configured dimension"
        )
    if normalized is not True or any(not math.isfinite(value) for value in values):
        raise LoveQdrantLiveAnalysisProjectionError(
            "E5 passage vector must be finite and normalized"
        )
    norm = math.sqrt(sum(value * value for value in values))
    if not math.isclose(norm, 1.0, rel_tol=1e-4, abs_tol=1e-4):
        raise LoveQdrantLiveAnalysisProjectionError(
            "E5 passage vector must have unit norm"
        )
    return values


def _prefixed_passage(text: str, prefix: str) -> str:
    plain = text.strip()
    marker = prefix.strip()
    if plain == marker or plain.startswith(marker + " "):
        return plain
    return f"{marker} {plain}"


def _digest_ref(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()
    return prefix + digest[:24]


def _require_typed_ref(name: str, value: object) -> None:
    if not isinstance(value, str) or ":" not in value or not value.strip():
        raise LoveQdrantLiveAnalysisProjectionError(
            f"{name} must be a typed reference"
        )


def _require_identifier(name: str, value: object) -> None:
    if (
        not isinstance(value, str)
        or not value
        or not value[0].islower()
        or any(
            not (character.islower() or character.isdigit() or character in "_.-")
            for character in value
        )
    ):
        raise LoveQdrantLiveAnalysisProjectionError(
            f"{name} must be a stable identifier"
        )


__all__ = (
    "LOVE_QDRANT_LIVE_ANALYSIS_PROJECTION_SCHEMA",
    "LoveQdrantLiveAnalysisProjection",
    "LoveQdrantLiveAnalysisProjectionError",
    "LoveQdrantLiveAnalysisProjectionSettings",
    "LoveQdrantLiveProjectionIdentity",
    "NamedHybridProjectionWriter",
    "build_love_qdrant_live_projection_identity",
    "build_love_qdrant_live_projection_identity_from_refs",
)
