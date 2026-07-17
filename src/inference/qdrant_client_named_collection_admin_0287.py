"""Controlled qdrant-client admin membrane for one named hybrid collection.

This I/O adapter exists because the projection/query executor deliberately does
not own collection lifecycle. It reuses the same connection/gate shape and may
share the same injected SDK client with the future tool-bounded composer.

The adapter can read, create and add payload indexes. It never deletes a
collection, vector, payload index or alias, and it never mutates aliases.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from importlib import import_module
import math
from types import MappingProxyType
from typing import Any, Callable, Mapping


QDRANT_NAMED_COLLECTION_SHAPE_SCHEMA = (
    "missipy.qdrant.named_collection_shape.v1"
)


class QdrantNamedCollectionAdminError(RuntimeError):
    """Fail-closed collection lifecycle error."""


@dataclass(frozen=True, slots=True)
class QdrantNamedCollectionShape:
    """Normalized collection readback without vectors or point payloads."""

    schema: str
    collection_name: str
    exists: bool
    status: str
    points_count: int
    dense_vectors: Mapping[str, Mapping[str, object]]
    sparse_vectors: tuple[str, ...]
    payload_indexes: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.schema != QDRANT_NAMED_COLLECTION_SHAPE_SCHEMA:
            raise QdrantNamedCollectionAdminError(
                "unsupported named collection shape schema"
            )
        if not self.collection_name.strip():
            raise QdrantNamedCollectionAdminError(
                "collection_name must be non-empty"
            )
        if self.points_count < 0:
            raise QdrantNamedCollectionAdminError(
                "points_count must be >= 0"
            )
        dense = {
            str(name): MappingProxyType(dict(config))
            for name, config in self.dense_vectors.items()
        }
        object.__setattr__(self, "dense_vectors", MappingProxyType(dense))
        object.__setattr__(
            self,
            "sparse_vectors",
            tuple(sorted(str(name) for name in self.sparse_vectors)),
        )
        object.__setattr__(
            self,
            "payload_indexes",
            MappingProxyType(
                {
                    str(name): str(kind)
                    for name, kind in self.payload_indexes.items()
                }
            ),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "collection_name": self.collection_name,
            "exists": self.exists,
            "status": self.status,
            "points_count": self.points_count,
            "dense_vectors": {
                name: dict(config)
                for name, config in self.dense_vectors.items()
            },
            "sparse_vectors": list(self.sparse_vectors),
            "payload_indexes": dict(self.payload_indexes),
            "boundaries": {
                "vectors_serialized": False,
                "point_payloads_serialized": False,
                "delete_performed": False,
                "alias_mutated": False,
            },
        }


class QdrantClientNamedCollectionAdmin:
    """Bounded admin surface around an injected qdrant-client instance."""

    def __init__(
        self,
        *,
        client: Any,
        models_module: Any,
        config: Any,
        gate: Any,
    ) -> None:
        self._client = client
        self._models = models_module
        self._config = config
        self._gate = gate

    def read_collection(self, collection_name: str) -> QdrantNamedCollectionShape:
        """Read and normalize collection configuration only."""

        _require_name("collection_name", collection_name)
        try:
            response = self._client.get_collection(collection_name)
        except Exception as exc:
            if _is_not_found(exc):
                return QdrantNamedCollectionShape(
                    schema=QDRANT_NAMED_COLLECTION_SHAPE_SCHEMA,
                    collection_name=collection_name,
                    exists=False,
                    status="missing",
                    points_count=0,
                    dense_vectors={},
                    sparse_vectors=(),
                    payload_indexes={},
                )
            raise QdrantNamedCollectionAdminError(
                f"read_collection failed: {_safe_error(exc)}"
            ) from exc
        payload = _plain(response)
        config = _mapping(payload.get("config"))
        params = _mapping(config.get("params"))
        dense_vectors = _dense_vector_shapes(params.get("vectors"))
        sparse_vectors = _named_keys(params.get("sparse_vectors"))
        payload_schema = _payload_schema(payload.get("payload_schema"))
        status = _enum_text(payload.get("status"))
        points_count = int(payload.get("points_count") or 0)
        return QdrantNamedCollectionShape(
            schema=QDRANT_NAMED_COLLECTION_SHAPE_SCHEMA,
            collection_name=collection_name,
            exists=True,
            status=status,
            points_count=points_count,
            dense_vectors=dense_vectors,
            sparse_vectors=sparse_vectors,
            payload_indexes=payload_schema,
        )

    def create_named_collection(
        self,
        *,
        collection_name: str,
        dense_vector_name: str,
        dense_dimension: int,
        dense_distance: str,
        sparse_vector_name: str,
    ) -> None:
        """Create one physical dense+sparse collection; never overwrite."""

        self._require_write("create_collection")
        for name, value in (
            ("collection_name", collection_name),
            ("dense_vector_name", dense_vector_name),
            ("sparse_vector_name", sparse_vector_name),
        ):
            _require_name(name, value)
        if dense_dimension != 384:
            raise QdrantNamedCollectionAdminError(
                "dense_dimension must be exactly 384"
            )
        distance = _distance_model(self._models, dense_distance)
        try:
            response = self._client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    dense_vector_name: self._models.VectorParams(
                        size=dense_dimension,
                        distance=distance,
                    )
                },
                sparse_vectors_config={
                    sparse_vector_name: self._models.SparseVectorParams()
                },
            )
        except Exception as exc:
            raise QdrantNamedCollectionAdminError(
                f"create_collection failed: {_safe_error(exc)}"
            ) from exc
        if response is False:
            raise QdrantNamedCollectionAdminError(
                "Qdrant did not acknowledge collection creation"
            )

    def create_payload_index(
        self,
        *,
        collection_name: str,
        field_name: str,
        index_kind: str,
    ) -> None:
        """Create one missing canonical payload index."""

        self._require_write("create_payload_index")
        _require_name("collection_name", collection_name)
        _require_name("field_name", field_name)
        schema = _payload_schema_model(self._models, index_kind)
        try:
            response = self._client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=schema,
                wait=bool(getattr(self._config, "wait_for_write", True)),
            )
        except Exception as exc:
            raise QdrantNamedCollectionAdminError(
                f"create_payload_index failed: {_safe_error(exc)}"
            ) from exc
        if response is False:
            raise QdrantNamedCollectionAdminError(
                f"Qdrant did not acknowledge payload index {field_name}"
            )

    def close(self) -> None:
        close = getattr(self._client, "close", None)
        if callable(close):
            close()

    def _require_write(self, operation: str) -> None:
        if not bool(getattr(self._gate, "allow_write", False)):
            raise QdrantNamedCollectionAdminError(
                f"{operation}: effect gate does not allow writes"
            )


def build_qdrant_client_named_collection_admin(
    config: Any,
    gate: Any,
    *,
    api_key: str | None = None,
    client_factory: Callable[..., Any] | None = None,
    models_module: Any | None = None,
) -> QdrantClientNamedCollectionAdmin:
    """Build the admin at the qdrant-client I/O boundary."""

    factory = client_factory
    models = models_module
    if factory is None:
        package = import_module("qdrant_client")
        factory = getattr(package, "QdrantClient")
    if models is None:
        models = import_module("qdrant_client.models")
    kwargs: dict[str, object] = {
        "url": getattr(config, "url"),
        "timeout": getattr(config, "timeout_seconds"),
        "prefer_grpc": bool(getattr(config, "prefer_grpc", False)),
        "check_compatibility": bool(
            getattr(config, "check_compatibility", True)
        ),
    }
    if kwargs["prefer_grpc"]:
        kwargs["grpc_port"] = int(getattr(config, "grpc_port"))
    if api_key:
        kwargs["api_key"] = api_key
    client = factory(**kwargs)
    return QdrantClientNamedCollectionAdmin(
        client=client,
        models_module=models,
        config=config,
        gate=gate,
    )


def _dense_vector_shapes(value: object) -> dict[str, dict[str, object]]:
    mapping = _mapping(value)
    result: dict[str, dict[str, object]] = {}
    for name, raw in mapping.items():
        config = _mapping(raw)
        if "size" not in config:
            continue
        result[str(name)] = {
            "size": int(config.get("size") or 0),
            "distance": _enum_text(config.get("distance")),
        }
    return result


def _named_keys(value: object) -> tuple[str, ...]:
    return tuple(sorted(str(name) for name in _mapping(value)))


def _payload_schema(value: object) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, raw in _mapping(value).items():
        config = _mapping(raw)
        kind = config.get("data_type", raw)
        result[str(name)] = _enum_text(kind)
    return result


def _mapping(value: object) -> Mapping[str, Any]:
    plain = _plain(value)
    return plain if isinstance(plain, Mapping) else {}


def _plain(value: object) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _plain(model_dump())
    dict_method = getattr(value, "dict", None)
    if callable(dict_method):
        return _plain(dict_method())
    if hasattr(value, "__dict__"):
        return {
            str(key): _plain(item)
            for key, item in vars(value).items()
            if not str(key).startswith("_")
        }
    return value


def _enum_text(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw or "")


def _distance_model(models: Any, distance: str) -> object:
    name = distance.strip().upper()
    member = getattr(getattr(models, "Distance"), name, None)
    if member is None:
        raise QdrantNamedCollectionAdminError(
            f"unsupported Qdrant distance: {distance}"
        )
    return member


def _payload_schema_model(models: Any, index_kind: str) -> object:
    name = index_kind.strip().upper()
    member = getattr(getattr(models, "PayloadSchemaType"), name, None)
    if member is None:
        raise QdrantNamedCollectionAdminError(
            f"unsupported payload index kind: {index_kind}"
        )
    return member


def _is_not_found(exc: BaseException) -> bool:
    code = getattr(exc, "status_code", None)
    if code == 404:
        return True
    return "not found" in str(exc).casefold()


def _safe_error(exc: BaseException) -> str:
    return (str(exc).strip() or type(exc).__name__).replace("\n", " ")[:300]


def _require_name(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise QdrantNamedCollectionAdminError(f"{name} must be non-empty")


__all__ = (
    "QDRANT_NAMED_COLLECTION_SHAPE_SCHEMA",
    "QdrantClientNamedCollectionAdmin",
    "QdrantNamedCollectionAdminError",
    "QdrantNamedCollectionShape",
    "build_qdrant_client_named_collection_admin",
)
# r10-r1 does not change collection-admin effects.
