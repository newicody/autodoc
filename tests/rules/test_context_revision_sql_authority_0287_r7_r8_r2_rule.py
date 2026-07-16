from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/context_revision_sql_authority_0287.py"
CURRENT = ROOT / "doc/README_CURRENT.md"
REPORT = ROOT / "PHASE0287_R7_R8_R2_CONTEXT_REVISION_SQL_AUTHORITY_REPORT.md"
ARCHITECTURE = (
    ROOT
    / "doc/architecture/CONTEXT_REVISION_SQL_AUTHORITY_0287_R7_R8_R2.md"
)
DOT = ROOT / "doc/architecture/CONTEXT_REVISION_SQL_AUTHORITY_0287_R7_R8_R2.dot"
CHANGELOG = (
    ROOT / "doc/CHANGELOG_0287_R7_R8_R2_CONTEXT_REVISION_SQL_AUTHORITY.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/MANIFEST_0287_R7_R8_R2_CONTEXT_REVISION_SQL_AUTHORITY.md"
)


def test_r8_r2_deliverables_exist_and_are_non_empty() -> None:
    for path in (
        SOURCE,
        CURRENT,
        REPORT,
        ARCHITECTURE,
        DOT,
        CHANGELOG,
        MANIFEST,
    ):
        assert path.is_file(), path
        assert path.read_text(encoding="utf-8").strip(), path


def test_public_schemas_and_legacy_bridge_are_locked() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for token in (
        "missipy.context.authority_object.v1",
        "missipy.context.artifact_descriptor.v1",
        "missipy.context.relation.v1",
        "missipy.context.revision_membership.v1",
        "missipy.context.revision.v1",
        "missipy.context.vector_projection_metadata.v1",
        "DbApiContextRevisionAuthorityStore",
        "SQLiteContextRevisionAuthorityStore",
        "build_authority_object_from_sql_context_record",
        "SqlContextRecord",
        "SqlContextStorePolicy",
    ):
        assert token in text


def test_sql_authority_has_dag_membership_artifact_and_projection_tables() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for table in (
        "context_authority_objects",
        "context_artifact_descriptors",
        "context_revisions",
        "context_revision_parents",
        "context_revision_memberships",
        "context_relations",
        "context_vector_projections",
    ):
        assert table in text
    for marker in (
        "parent_revision_refs",
        "replacement_ref",
        "storage_ref",
        "source_content_digest",
        "embedding_profile_ref",
        "vector_name",
        "collection_name",
        "point_id",
    ):
        assert marker in text


def test_module_does_not_import_runtime_or_projection_backends() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = {
        "qdrant_client",
        "openvino",
        "openvino_genai",
        "torch",
        "transformers",
        "context.control_proxy",
        "context.scheduler",
    }
    assert not forbidden.intersection(imported)


def test_roadmap_preserves_role_separation_and_next_step() -> None:
    text = CURRENT.read_text(encoding="utf-8")
    for token in (
        "0287-r7-r8-r2 — context revision SQL authority",
        "missipy.sql_context_store.v1",
        "multi-parent revisions",
        "never raw vector values",
        "ControlProxy route generations remain transport state",
        "only. This phase does not call OpenVINO",
        "canonical Qdrant payload",
        "SQL remains authority and Qdrant remains projection/recall only",
        "Scheduler = the only orchestration authority",
    ):
        assert token in text


def test_report_and_manifest_keep_effects_closed() -> None:
    report = REPORT.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in (
        "Qdrant collection or point creation: not performed",
        "OpenVINO call: not performed",
        "Scheduler change: not performed",
        "ControlProxy change: not performed",
        "GitHub mutation: not performed",
    ):
        assert token in report
    for token in (
        "raw vectors stored in SQL: no",
        "Qdrant write performed: no",
        "Scheduler changed: no",
        "ControlProxy changed: no",
        "`INSTALLATION.md` changed: no",
    ):
        assert token in manifest
