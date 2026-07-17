from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
BUNDLE = ROOT / "templates/github/projects-repository"
MANIFEST = BUNDLE / "projects_bundle_manifest.json"
CONTRACT = BUNDLE / "scripts/projects_bundle_manifest_contract.py"
CLI = BUNDLE / "scripts/audit_projects_bundle_drift.py"


def test_manifest_active_sources_exist_and_destinations_are_unique() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert payload["schema"] == "missipy.projects_bundle_manifest.v1"
    assert payload["ownership_policy"]["safe_delete_scope"] == (
        "retired_entries-only"
    )
    assert payload["ownership_policy"]["rsync_delete_allowed"] is False

    entries = payload["entries"]
    sources = [item["source_path"] for item in entries]
    destinations = [item["destination_path"] for item in entries]
    retired = [
        item["destination_path"]
        for item in payload["retired_entries"]
    ]

    assert len(sources) == len(set(sources))
    assert len(destinations) == len(set(destinations))
    assert not set(destinations).intersection(retired)
    for relative in sources:
        assert (BUNDLE / relative).is_file(), relative


def test_drift_audit_remains_stdlib_local_and_read_only() -> None:
    combined = (
        CONTRACT.read_text(encoding="utf-8")
        + "\n"
        + CLI.read_text(encoding="utf-8")
    )
    for required in (
        "@dataclass(frozen=True, slots=True)",
        "ProjectsBundleDriftAuditCommand",
        "ProjectsBundleDriftAuditPolicy",
        "ProjectsBundleDriftAuditResult",
        "max_manifest_entries",
        "max_unknown_files",
        "mutation_performed: bool = False",
        "remote_access_performed: bool = False",
        "safe_delete_scope",
        "retired_entries-only",
        "rsync_delete_allowed",
    ):
        assert required in combined

    for forbidden in (
        ".unlink(",
        "os.remove(",
        "shutil.rmtree(",
        "subprocess.",
        "requests.",
        "urllib.",
        "httpx.",
        "gh api",
    ):
        assert forbidden not in combined


def test_bundle_documentation_names_manifest_and_audit() -> None:
    readme = (BUNDLE / "README.md").read_text(encoding="utf-8")
    installation = (BUNDLE / "INSTALLATION.md").read_text(encoding="utf-8")
    runbook = (BUNDLE / "PROJECTS_BUNDLE_DRIFT_AUDIT.md").read_text(encoding="utf-8")

    assert len(installation.splitlines()) < 380
    for marker in (
        "Ne pas utiliser `--delete`",
        "PROJECTS_BUNDLE_DRIFT_AUDIT.md",
        "projects_bundle_manifest.json",
        "audit_projects_bundle_drift.py",
        "safe_delete_candidates",
    ):
        assert marker in installation
    for marker in (
        "projects_bundle_manifest.json",
        "audit_projects_bundle_drift.py",
        "PROJECTS_BUNDLE_DRIFT_AUDIT.md",
    ):
        assert marker in readme
    for marker in (
        "safe_delete_candidates",
        "unknown_extra_files",
        "rsync_delete_allowed = false",
    ):
        assert marker in runbook
