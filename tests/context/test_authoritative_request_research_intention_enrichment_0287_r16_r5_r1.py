from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "templates/github/projects-repository/scripts/"
    / "enrich_authoritative_request_research_intention.py"
)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "enrich_authoritative_request_research_intention_r16_r5_r1",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _request() -> dict[str, object]:
    return {
        "schema": "missipy.github.authoritative_request.v1",
        "repository": "newicody/projects",
        "issue_number": 42,
        "metadata": {"github_sha": "abc123"},
        "authoritative": True,
        "advisory_content_embedded": False,
        "remote_mutation_requested": False,
    }


def _event() -> dict[str, object]:
    return {
        "repository": {"full_name": "newicody/projects"},
        "autodoc_dispatch": {
            "issue_number": 42,
            "requested_status": "Recherche",
            "request_mode": "initial",
            "parent_event_ref": "",
        },
    }


def test_enrichment_preserves_authority_and_existing_metadata() -> None:
    module = _load()
    enriched = module.enrich_authoritative_request(_request(), _event())

    assert enriched["schema"] == "missipy.github.authoritative_request.v1"
    assert enriched["authoritative"] is True
    assert enriched["metadata"] == {
        "github_sha": "abc123",
        "requested_status": "Recherche",
        "request_mode": "initial",
        "parent_event_ref": "",
    }


def test_main_rewrites_the_request_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load()
    request_path = tmp_path / "authoritative_request.json"
    event_path = tmp_path / "controlled_event.json"
    request_path.write_text(json.dumps(_request()), encoding="utf-8")
    event_path.write_text(json.dumps(_event()), encoding="utf-8")

    monkeypatch.setenv("AUTODOC_REQUEST", str(request_path))
    monkeypatch.setenv("AUTODOC_EVENT_PATH", str(event_path))
    monkeypatch.setenv("AUTODOC_OUTPUT", str(request_path))

    assert module.main() == 0
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["requested_status"] == "Recherche"
    assert not (tmp_path / ".authoritative_request.json.tmp").exists()


@pytest.mark.parametrize(
    ("target", "field", "value", "message"),
    (
        ("event", "repository", {"full_name": "other/repository"}, "repository"),
        ("dispatch", "issue_number", 43, "issue_number"),
        ("dispatch", "requested_status", "Drop", "requested_status"),
        ("dispatch", "request_mode", "implicit", "request_mode"),
    ),
)
def test_invalid_or_mismatched_provenance_fails_closed(
    target: str,
    field: str,
    value: object,
    message: str,
) -> None:
    module = _load()
    event = _event()
    if target == "event":
        event[field] = value
    else:
        dispatch = event["autodoc_dispatch"]
        assert isinstance(dispatch, dict)
        dispatch[field] = value

    with pytest.raises(ValueError, match=message):
        module.enrich_authoritative_request(_request(), event)


def test_existing_conflicting_metadata_is_rejected() -> None:
    module = _load()
    request = _request()
    metadata = request["metadata"]
    assert isinstance(metadata, dict)
    metadata["requested_status"] = "Production"

    with pytest.raises(ValueError, match="collision"):
        module.enrich_authoritative_request(request, _event())
