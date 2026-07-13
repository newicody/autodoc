from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "templates/github/projects-repository/scripts/"
    "run_workflow_dispatch_authoritative_request.py"
)


def _load():
    spec = spec_from_file_location("dispatch_repair_0281", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_normalize_recovers_missing_issue_from_selected_payload() -> None:
    module = _load()
    selected = {
        "number": 15,
        "title": "Recherche",
        "body": "Analyser",
        "labels": [],
    }
    event = {
        "action": "workflow_dispatch",
        "issue": None,
        "repository": {"full_name": "newicody/projects"},
        "sender": {"login": "newicody"},
        "autodoc_dispatch": {"request_mode": "initial"},
    }

    normalized = module.normalize_dispatch_event(
        event,
        selected,
        repository="newicody/projects",
        actor="newicody",
    )

    assert normalized["issue"] == selected
    assert normalized["issue"]["number"] == 15
    assert normalized["schema"].endswith(".v1")


def test_normalize_decodes_string_issue_object() -> None:
    module = _load()
    selected = {"number": 15, "title": "Recherche", "body": ""}
    event = {"issue": json.dumps(selected)}

    normalized = module.normalize_dispatch_event(
        event,
        selected,
        repository="newicody/projects",
        actor="newicody",
    )

    assert normalized["issue"]["title"] == "Recherche"


def test_normalize_rejects_cross_issue_mismatch() -> None:
    module = _load()
    try:
        module.normalize_dispatch_event(
            {"issue": {"number": 99}},
            {"number": 15},
            repository="newicody/projects",
            actor="newicody",
        )
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("cross-Issue mismatch must be rejected")
