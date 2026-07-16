from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/qdrant_canonical_profile_0287.py"
REPORT = ROOT / "doc/architecture/PHASE0287_R7_R8_R3_QDRANT_CANONICAL_PROFILE_REPORT.md"
ARCH = ROOT / "doc/architecture/QDRANT_CANONICAL_PROFILE_0287_R7_R8_R3.md"
DOT = ROOT / "doc/architecture/QDRANT_CANONICAL_PROFILE_0287_R7_R8_R3.dot"
CHANGELOG = ROOT / "doc/changelog/0287-r7-r8-r3-qdrant-canonical-profile.md"


def test_r8_r3_files_and_contract_markers_are_present() -> None:
    for path in (MODULE, REPORT, ARCH, DOT, CHANGELOG):
        assert path.is_file(), path
    source = MODULE.read_text(encoding="utf-8")
    for marker in (
        "missipy.qdrant.named_vector_profile.v1",
        "missipy.qdrant.payload_index_profile.v1",
        "missipy.qdrant.collection_profile.v1",
        "missipy.qdrant.point_projection.v1",
        "missipy.qdrant.model_migration_plan.v1",
        "missipy.context.vector_projection_metadata.v1",
        "missipy.embedding_space_profile.v1",
    ):
        assert marker in source


def test_r8_r3_keeps_qdrant_as_reconstructible_projection() -> None:
    text = (REPORT.read_text(encoding="utf-8") + ARCH.read_text(encoding="utf-8"))
    for marker in (
        "SQL remains the authority",
        "Qdrant is reconstructible",
        "no raw authoritative content",
        "no qdrant-client dependency",
        "no Qdrant write",
        "ControlProxy is unchanged",
        "one collection per task is forbidden",
    ):
        assert marker in text


def test_r8_r3_documents_named_vector_and_alias_migrations() -> None:
    text = ARCH.read_text(encoding="utf-8")
    assert "named-vector backfill" in text
    assert "collection alias swap" in text
    assert "payload indexes before ingestion" in text
    assert "dense E5 + sparse" in text
    assert "r8-r4" in text


def test_r8_r3_has_no_runtime_qdrant_dependency() -> None:
    source = MODULE.read_text(encoding="utf-8")
    assert "import qdrant_client" not in source
    assert "from qdrant_client" not in source
    assert "upsert(" not in source
    assert "create_collection(" not in source
    assert "update_collection_aliases(" not in source
