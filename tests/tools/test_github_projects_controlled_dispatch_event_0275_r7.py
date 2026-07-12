from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "templates/github/projects-repository/scripts/"
    "build_workflow_dispatch_issue_event.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("dispatch_event_0275_r7", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_controlled_dispatch_event_preserves_hierarchy() -> None:
    module = _load_module()
    event = module.build_event(
        {
            "number": 42,
            "title": "Recherche transversale",
            "body": "Thèmes: #10, #11",
        },
        repository="newicody/projects",
        actor="newicody",
        requested_status="Recherche",
        request_mode="transversal",
        parent_event_ref="event:41",
    )

    assert event["issue"]["number"] == 42
    assert event["repository"]["full_name"] == "newicody/projects"
    assert event["sender"]["login"] == "newicody"
    assert event["autodoc_dispatch"] == {
        "issue_number": 42,
        "requested_status": "Recherche",
        "request_mode": "transversal",
        "parent_event_ref": "event:41",
    }


def test_build_controlled_dispatch_event_rejects_unsupported_status() -> None:
    module = _load_module()

    try:
        module.build_event(
            {"number": 42},
            repository="newicody/projects",
            actor="newicody",
            requested_status="En cours",
            request_mode="initial",
            parent_event_ref="",
        )
    except ValueError as exc:
        assert str(exc) == "unsupported requested_status"
    else:
        raise AssertionError("unsupported status accepted")
