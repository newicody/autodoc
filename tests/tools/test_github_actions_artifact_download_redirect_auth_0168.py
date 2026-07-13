from __future__ import annotations

from email.message import Message
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from urllib.error import HTTPError
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_github_actions_artifact_fetch_once.py"


class _Response:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def _load_tool():
    spec = spec_from_file_location("fetch_redirect_auth_0168", TOOL)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _redirect_error(url: str, location: str) -> HTTPError:
    headers = Message()
    headers["Location"] = location
    return HTTPError(url, 302, "Found", headers, None)


def test_redirect_download_does_not_forward_authorization(
    monkeypatch,
) -> None:
    module = _load_tool()
    initial = []
    redirected = []
    signed_url = (
        "https://results-receiver.actions.githubusercontent.com/"
        "artifact.zip?sig=temporary"
    )

    class _Opener:
        def open(self, request, timeout):
            initial.append(request)
            raise _redirect_error(request.full_url, signed_url)

    monkeypatch.setattr(
        urllib.request,
        "build_opener",
        lambda *handlers: _Opener(),
    )

    def fake_urlopen(request, timeout):
        redirected.append(request)
        return _Response(b"PK\x03\x04artifact")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = module.GitHubActionsClient(
        "https://api.github.com",
        "secret-token",
    )
    payload = client.download_artifact(
        "newicody/projects",
        {
            "id": 123,
            "archive_download_url": (
                "https://api.github.com/repos/newicody/projects/"
                "actions/artifacts/123/zip"
            ),
        },
    )

    assert payload == b"PK\x03\x04artifact"
    assert initial[0].get_header("Authorization") == (
        "Bearer secret-token"
    )
    assert redirected[0].full_url == signed_url
    assert redirected[0].get_header("Authorization") is None


def test_direct_zip_response_remains_supported(monkeypatch) -> None:
    module = _load_tool()
    initial = []

    class _Opener:
        def open(self, request, timeout):
            initial.append(request)
            return _Response(b"PK\x03\x04direct")

    monkeypatch.setattr(
        urllib.request,
        "build_opener",
        lambda *handlers: _Opener(),
    )
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("redirect request must not execute")
        ),
    )

    client = module.GitHubActionsClient(
        "https://api.github.com",
        "secret-token",
    )

    assert client.download_artifact(
        "newicody/projects",
        {"id": 123},
    ) == b"PK\x03\x04direct"
    assert initial[0].get_header("Authorization") == (
        "Bearer secret-token"
    )


def test_http_redirect_is_rejected(monkeypatch) -> None:
    module = _load_tool()

    class _Opener:
        def open(self, request, timeout):
            raise _redirect_error(
                request.full_url,
                "http://storage.example.invalid/artifact.zip",
            )

    monkeypatch.setattr(
        urllib.request,
        "build_opener",
        lambda *handlers: _Opener(),
    )
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("unsafe redirect must not execute")
        ),
    )

    client = module.GitHubActionsClient(
        "https://api.github.com",
        "secret-token",
    )

    try:
        client.download_artifact(
            "newicody/projects",
            {"id": 123},
        )
    except ValueError as exc:
        assert "credential-free HTTPS" in str(exc)
    else:
        raise AssertionError("HTTP redirect must be rejected")


def test_foreign_api_origin_is_rejected(monkeypatch) -> None:
    module = _load_tool()
    monkeypatch.setattr(
        urllib.request,
        "build_opener",
        lambda *handlers: (_ for _ in ()).throw(
            AssertionError("foreign origin must be rejected first")
        ),
    )

    client = module.GitHubActionsClient(
        "https://api.github.com",
        "secret-token",
    )

    try:
        client.download_artifact(
            "newicody/projects",
            {
                "id": 123,
                "archive_download_url": (
                    "https://example.invalid/artifact.zip"
                ),
            },
        )
    except ValueError as exc:
        assert "configured GitHub API origin" in str(exc)
    else:
        raise AssertionError("foreign origin must be rejected")
