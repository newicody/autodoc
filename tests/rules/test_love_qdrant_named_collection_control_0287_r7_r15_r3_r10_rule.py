from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "src/context/love_qdrant_named_collection_control_0287.py"
ADMIN = ROOT / "src/inference/qdrant_client_named_collection_admin_0287.py"
CONFIG = ROOT / "config/love_installed_runtime.example.ini"
TOOL = ROOT / "tools/control_love_qdrant_named_collection_0287.py"
RUNTIME_CONFIG = ROOT / "src/context/love_manual_runtime_configuration_0287.py"


def test_r10_keeps_collection_creation_additive_and_preview_first() -> None:
    control = CONTROL.read_text(encoding="utf-8")
    admin = ADMIN.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")

    for marker in (
        "physical_collection = autodoc_context_e5_384_hybrid_v1",
        "collection_alias = autodoc_context_hybrid_current",
        "dense_vector_name = dense_e5_v1",
        "sparse_vector_name = sparse_lexical_v1",
    ):
        assert marker in config

    for marker in (
        "confirm-plan-digest mismatch",
        "operator_decision",
        "allow_create",
        "alias_mutated",
        "delete_performed",
        "build_canonical_payload_indexes",
    ):
        assert marker in control

    for marker in (
        "create_collection",
        "create_payload_index",
        "SparseVectorParams",
        "VectorParams",
        "get_collection",
    ):
        assert marker in admin

    for forbidden in (
        "delete_collection",
        "delete_payload_index",
        "update_collection_aliases",
        "delete_alias",
    ):
        assert forbidden not in control
        assert forbidden not in admin
        assert forbidden not in tool

    assert "AUTODOC_QDRANT_COLLECTION_MUTATION_ALLOWED" in tool
    assert "Scheduler(" not in control
    assert "Scheduler(" not in admin


def test_r10_keeps_legacy_qdrant_constructor_compatible() -> None:
    source = RUNTIME_CONFIG.read_text(encoding="utf-8")
    for marker in (
        'physical_collection: str = ""',
        'collection_alias: str = ""',
        'dense_vector_name: str = "dense_e5_v1"',
        'sparse_vector_name: str = "sparse_lexical_v1"',
        'named_vectors_enabled: bool = False',
        'self.physical_collection.strip() or collection',
        'self.collection_alias.strip() or collection',
    ):
        assert marker in source
