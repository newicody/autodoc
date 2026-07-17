from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from inference.qdrant_client_named_collection_admin_0287 import (
    QdrantClientNamedCollectionAdmin,
)


class _Distance:
    COSINE = "Cosine"


class _PayloadSchemaType:
    KEYWORD = "keyword"
    BOOL = "bool"


@dataclass
class _VectorParams:
    size: int
    distance: object


class _SparseVectorParams:
    pass


class _Models:
    Distance = _Distance
    PayloadSchemaType = _PayloadSchemaType
    VectorParams = _VectorParams
    SparseVectorParams = _SparseVectorParams


@dataclass
class _Config:
    wait_for_write: bool = True


@dataclass
class _Gate:
    allow_write: bool = True


class _NotFound(Exception):
    status_code = 404


class _Client:
    def __init__(self) -> None:
        self.created = None
        self.indexes = []

    def get_collection(self, collection_name):
        if self.created is None:
            raise _NotFound("not found")
        return {
            "status": "green",
            "points_count": 0,
            "config": {
                "params": {
                    "vectors": {
                        "dense_e5_v1": {
                            "size": 384,
                            "distance": "Cosine",
                        }
                    },
                    "sparse_vectors": {
                        "sparse_lexical_v1": {},
                    },
                }
            },
            "payload_schema": {
                name: {"data_type": kind}
                for name, kind in self.indexes
            },
        }

    def create_collection(self, **kwargs):
        self.created = kwargs
        return True

    def create_payload_index(self, **kwargs):
        self.indexes.append(
            (kwargs["field_name"], kwargs["field_schema"])
        )
        return True


def test_sdk_admin_creates_and_reads_named_collection() -> None:
    client = _Client()
    admin = QdrantClientNamedCollectionAdmin(
        client=client,
        models_module=_Models,
        config=_Config(),
        gate=_Gate(),
    )
    missing = admin.read_collection("autodoc_context_e5_384_hybrid_v1")
    assert missing.exists is False
    admin.create_named_collection(
        collection_name="autodoc_context_e5_384_hybrid_v1",
        dense_vector_name="dense_e5_v1",
        dense_dimension=384,
        dense_distance="Cosine",
        sparse_vector_name="sparse_lexical_v1",
    )
    admin.create_payload_index(
        collection_name="autodoc_context_e5_384_hybrid_v1",
        field_name="sql_ref",
        index_kind="keyword",
    )
    shape = admin.read_collection("autodoc_context_e5_384_hybrid_v1")
    assert shape.exists is True
    assert shape.dense_vectors["dense_e5_v1"]["size"] == 384
    assert shape.sparse_vectors == ("sparse_lexical_v1",)
    assert shape.payload_indexes["sql_ref"] == "keyword"
    assert "vectors" not in shape.to_mapping()
# r10-r1 leaves the admin membrane behavior unchanged.

class _SdkDistance(str, Enum):
    COSINE = "Cosine"


class _SdkPayloadSchemaType(str, Enum):
    KEYWORD = "keyword"
    BOOL = "bool"


class _SdkCollectionStatus(str, Enum):
    GREEN = "green"


class _SdkResponse:
    def model_dump(self):
        return {
            "status": _SdkCollectionStatus.GREEN,
            "points_count": 0,
            "config": {
                "params": {
                    "vectors": {
                        "dense_e5_v1": {
                            "size": 384,
                            "distance": _SdkDistance.COSINE,
                        }
                    },
                    "sparse_vectors": {
                        "sparse_lexical_v1": {},
                    },
                }
            },
            "payload_schema": {
                "sql_ref": {
                    "data_type": _SdkPayloadSchemaType.KEYWORD,
                    "points": 0,
                },
                "valid": {
                    "data_type": _SdkPayloadSchemaType.BOOL,
                    "points": 0,
                },
            },
        }


class _SdkReadClient:
    def get_collection(self, collection_name):
        return _SdkResponse()


def test_sdk_enum_values_are_normalized_during_readback() -> None:
    admin = QdrantClientNamedCollectionAdmin(
        client=_SdkReadClient(),
        models_module=_Models,
        config=_Config(),
        gate=_Gate(allow_write=False),
    )

    shape = admin.read_collection("autodoc_context_e5_384_hybrid_v1")

    assert shape.status == "green"
    assert shape.dense_vectors["dense_e5_v1"] == {
        "size": 384,
        "distance": "Cosine",
    }
    assert shape.sparse_vectors == ("sparse_lexical_v1",)
    assert shape.payload_indexes == {
        "sql_ref": "keyword",
        "valid": "bool",
    }
