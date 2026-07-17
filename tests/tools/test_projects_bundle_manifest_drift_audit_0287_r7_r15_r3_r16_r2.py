from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).parents[2]
CONTRACT = (
    ROOT
    / "templates"
    / "github"
    / "projects-repository"
    / "scripts"
    / "projects_bundle_manifest_contract.py"
)


def _load_contract():
    spec = importlib.util.spec_from_file_location(
        "projects_bundle_manifest_contract_test",
        CONTRACT,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


contract = _load_contract()


def _write_manifest(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "missipy.projects_bundle_manifest.v1",
                "bundle_ref": "projects-bundle:test",
                "bundle_version": "test-v1",
                "source_repository": "newicody/autodoc",
                "destination_repository": "newicody/projects",
                "digest_policy": {
                    "algorithm": "sha256",
                    "mode": "compute-from-source-at-audit-time",
                },
                "managed_roots": ["scripts"],
                "entries": [
                    {
                        "source_path": "scripts/managed.py",
                        "destination_path": "scripts/managed.py",
                        "role": "operator-script",
                        "state": "active",
                        "managed_by": "newicody/autodoc",
                    }
                ],
                "retired_entries": [
                    {
                        "destination_path": "scripts/retired.py",
                        "role": "retired-script",
                        "state": "retired",
                        "managed_by": "newicody/autodoc",
                        "reason": "replaced",
                    }
                ],
                "ownership_policy": {
                    "unknown_extra_files": "review-only",
                    "safe_delete_scope": "retired_entries-only",
                    "overwrite_modified_files": (
                        "operator-review-required"
                    ),
                    "rsync_delete_allowed": False,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_audit_distinguishes_copy_delete_and_review_candidates(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "scripts").mkdir(parents=True)
    (destination / "scripts").mkdir(parents=True)
    (source / "scripts/managed.py").write_text(
        "source\n", encoding="utf-8"
    )
    (destination / "scripts/managed.py").write_text(
        "different\n", encoding="utf-8"
    )
    (destination / "scripts/retired.py").write_text(
        "retired\n", encoding="utf-8"
    )
    (destination / "scripts/project_owned.py").write_text(
        "project\n", encoding="utf-8"
    )
    manifest = source / "projects_bundle_manifest.json"
    _write_manifest(manifest)

    result = contract.audit_projects_bundle_drift(
        contract.ProjectsBundleDriftAuditCommand(
            source_root=source,
            destination_root=destination,
            manifest_path=manifest,
        )
    )

    assert result.managed_exact is False
    assert result.review_required is True
    assert result.copy_candidates == ("scripts/managed.py",)
    assert result.safe_delete_candidates == ("scripts/retired.py",)
    assert result.unknown_extra_files == (
        "scripts/project_owned.py",
    )
    assert result.mutation_performed is False
    assert result.remote_access_performed is False
    assert result.to_mapping()["boundaries"][
        "unknown_extra_files_are_delete_candidates"
    ] is False


def test_audit_is_exact_after_copy_and_retired_cleanup(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "scripts").mkdir(parents=True)
    (destination / "scripts").mkdir(parents=True)
    for root in (source, destination):
        (root / "scripts/managed.py").write_text(
            "same\n", encoding="utf-8"
        )
    manifest = source / "projects_bundle_manifest.json"
    _write_manifest(manifest)

    result = contract.audit_projects_bundle_drift(
        contract.ProjectsBundleDriftAuditCommand(
            source_root=source,
            destination_root=destination,
            manifest_path=manifest,
        )
    )

    assert result.managed_exact is True
    assert result.review_required is False
    assert result.copy_candidates == ()
    assert result.safe_delete_candidates == ()
    assert result.unknown_extra_files == ()


def test_manifest_rejects_path_traversal(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["entries"][0]["destination_path"] = "../outside"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        contract.ProjectsBundleManifestError,
        match="normalized relative path",
    ):
        contract.load_projects_bundle_manifest(manifest)


def test_python_transients_are_reported_but_do_not_require_review(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "scripts").mkdir(parents=True)
    (destination / "scripts/__pycache__").mkdir(parents=True)
    for root in (source, destination):
        (root / "scripts/managed.py").write_text(
            "same\n", encoding="utf-8"
        )
    (destination / "scripts/__pycache__/managed.cpython-314.pyc").write_bytes(
        b"cache"
    )
    (destination / "scripts/helper.pyc").write_bytes(b"cache")
    (destination / "scripts/helper.pyo").write_bytes(b"cache")
    manifest = source / "projects_bundle_manifest.json"
    _write_manifest(manifest)

    result = contract.audit_projects_bundle_drift(
        contract.ProjectsBundleDriftAuditCommand(
            source_root=source,
            destination_root=destination,
            manifest_path=manifest,
        )
    )

    assert result.managed_exact is True
    assert result.review_required is False
    assert result.unknown_extra_files == ()
    assert result.ignored_transient_files == (
        "scripts/__pycache__/managed.cpython-314.pyc",
        "scripts/helper.pyc",
        "scripts/helper.pyo",
    )
    mapping = result.to_mapping()
    assert mapping["ignored_transient_files"] == [
        "scripts/__pycache__/managed.cpython-314.pyc",
        "scripts/helper.pyc",
        "scripts/helper.pyo",
    ]
    assert mapping["boundaries"][
        "transient_python_artifacts_ignored"
    ] is True


def test_non_transient_file_inside_scripts_still_requires_review(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "scripts").mkdir(parents=True)
    (destination / "scripts/__pycache__").mkdir(parents=True)
    for root in (source, destination):
        (root / "scripts/managed.py").write_text(
            "same\n", encoding="utf-8"
        )
    (destination / "scripts/__pycache__/cache.pyc").write_bytes(
        b"cache"
    )
    (destination / "scripts/manual-note.txt").write_text(
        "review\n", encoding="utf-8"
    )
    manifest = source / "projects_bundle_manifest.json"
    _write_manifest(manifest)

    result = contract.audit_projects_bundle_drift(
        contract.ProjectsBundleDriftAuditCommand(
            source_root=source,
            destination_root=destination,
            manifest_path=manifest,
        )
    )

    assert result.managed_exact is True
    assert result.review_required is True
    assert result.unknown_extra_files == (
        "scripts/manual-note.txt",
    )
    assert result.ignored_transient_files == (
        "scripts/__pycache__/cache.pyc",
    )
