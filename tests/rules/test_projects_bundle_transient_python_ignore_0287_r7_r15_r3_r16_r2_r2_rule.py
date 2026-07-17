import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
BUNDLE = ROOT / "templates/github/projects-repository"
CONTRACT = BUNDLE / "scripts/projects_bundle_manifest_contract.py"
MANIFEST = BUNDLE / "projects_bundle_manifest.json"
RUNBOOK = BUNDLE / "PROJECTS_BUNDLE_DRIFT_AUDIT.md"


def test_transient_python_ignore_is_explicit_and_narrow() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    for marker in (
        'TRANSIENT_PYTHON_DIRECTORY_NAMES = frozenset({"__pycache__"})',
        'TRANSIENT_PYTHON_FILE_SUFFIXES = frozenset({".pyc", ".pyo"})',
        "ignored_transient_files",
        "_is_transient_python_artifact",
        "transient_python_artifacts_ignored",
    ):
        assert marker in text

    for forbidden in (
        ".gitignore",
        ".pytest_cache",
        ".mypy_cache",
        "*.tmp",
        "*.log",
    ):
        assert forbidden not in text


def test_manifest_and_runbook_expose_transient_policy() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    policy = payload["ownership_policy"]["ignored_transient_files"]
    assert policy == {
        "directory_names": ["__pycache__"],
        "file_suffixes": [".pyc", ".pyo"],
        "report_field": "ignored_transient_files",
        "review_required": False,
    }
    assert payload["bundle_version"] == (
        "0287-r7-r15-r3-r16-r2-r2"
    )

    text = RUNBOOK.read_text(encoding="utf-8")
    assert "ignored_transient_files" in text
    assert "`__pycache__`, `*.pyc` et `*.pyo`" in text
    assert "ils ne déclenchent aucune revue" in text
