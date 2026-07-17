from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/love_postgresql_authority_binding_0287.py"
REPORT = ROOT / "PHASE0287_R7_R15_R3_R6_POSTGRESQL_AUTHORITY_LIVE_BINDING_REPORT.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0287_R7_R15_R3_R6_POSTGRESQL_AUTHORITY_LIVE_BINDING.md"
ARCH = ROOT / "doc/architecture/POSTGRESQL_AUTHORITY_LIVE_BINDING_0287_R7_R15_R3_R6.md"
DOT = ROOT / "doc/architecture/POSTGRESQL_AUTHORITY_LIVE_BINDING_0287_R7_R15_R3_R6.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_R15_R3_R6_POSTGRESQL_AUTHORITY_LIVE_BINDING.md"


def test_binding_reuses_existing_authority_and_keeps_other_backends_out() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for required in (
        "DbApiContextRevisionAuthorityStore",
        'SqlContextStorePolicy(paramstyle="format", auto_commit=True)',
        "ContextRevision(",
        "initialize_schema()",
        "put_revision(revision)",
        "importlib.import_module(\"psycopg\")",
        "secret_value_serialized",
        "qdrant_write_performed",
        "openvino_inference_performed",
        "scheduler_constructed",
    ):
        assert required in text
    for forbidden in (
        "Scheduler(",
        "Dispatcher(",
        "QdrantClient(",
        "openvino.runtime",
        "SQLiteContextRevisionAuthorityStore(",
        "password = '...",
    ):
        assert forbidden not in text


def test_binding_is_documented_as_one_io_boundary() -> None:
    for path in (REPORT, CHANGELOG, ARCH, DOT, MANIFEST):
        assert path.is_file(), path
    report = REPORT.read_text(encoding="utf-8")
    assert "no new authority store" in report
    assert "context-revision:love-base" in report
    assert "E5/Qdrant remain deferred" in report
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "src/context/love_postgresql_authority_binding_0287.py" in manifest
    assert "tests/context/test_love_postgresql_authority_binding_0287_r7_r15_r3_r6.py" in manifest
