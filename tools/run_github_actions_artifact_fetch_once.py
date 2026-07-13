#!/usr/bin/env python3
"""Fetch GitHub Actions artifacts read-only and sync them into the server dataset.

0168 performs the network/download step that 0167 intentionally did not do. It
lists completed workflow runs, lists their artifacts, downloads matching artifact
ZIP archives into server-side staging, then invokes the existing 0167 server
dataset sync tool. Conversion is not executed here; conversion is queued only
after the raw artifact sync is complete by the 0167 sync boundary.
"""

from __future__ import annotations

import argparse
import configparser
from dataclasses import dataclass
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

try:  # Reuse the 0167 config loader when available; keep this tool runnable.
    from context.github_artifact_server_fetch_config import (  # type: ignore
        load_github_artifact_server_fetch_config,
        validate_github_artifact_server_fetch_config,
    )
except Exception:  # pragma: no cover - defensive fallback for partial checkouts
    load_github_artifact_server_fetch_config = None  # type: ignore[assignment]
    validate_github_artifact_server_fetch_config = None  # type: ignore[assignment]


_SCHEMA = "missipy.github_actions.artifact_fetch_once_report.v1"
_STATE_SCHEMA = "missipy.github_actions.artifact_fetch_state.v1"
_DEFAULT_API_URL = "https://api.github.com"
_DEFAULT_SYNC_TOOL = "tools/run_github_artifact_server_sync_once.py"


@dataclass(frozen=True)
class FetchSettings:
    repository: str
    allowed_repositories: tuple[str, ...]
    workflow_name: str
    artifact_name_prefix: str
    api_url: str
    token_env: str
    dataset_root: Path
    staging_root: Path
    state_path: Path
    sync_tool: Path
    max_runs: int
    max_artifacts: int


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only fetch of GitHub Actions artifacts into the configured server dataset."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--repository", default="")
    parser.add_argument("--workflow-name", default="")
    parser.add_argument("--artifact-name-prefix", default="")
    parser.add_argument("--staging-root", type=Path, default=None)
    parser.add_argument("--state-path", type=Path, default=None)
    parser.add_argument("--sync-tool", type=Path, default=Path(_DEFAULT_SYNC_TOOL))
    parser.add_argument("--max-runs", type=int, default=10)
    parser.add_argument("--max-artifacts", type=int, default=20)
    parser.add_argument("--fixture-root", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    settings = _load_settings(args)
    _validate_settings(settings)

    token = ""
    external_call_performed = False
    if args.fixture_root is None:
        token = os.environ.get(settings.token_env, "")
        if not token:
            raise SystemExit(f"missing GitHub token environment variable: {settings.token_env}")
        external_call_performed = True

    state = _read_state(settings.state_path)
    client = FixtureClient(args.fixture_root) if args.fixture_root is not None else GitHubActionsClient(settings.api_url, token)

    workflow_runs = client.list_workflow_runs(settings.repository, settings.workflow_name, settings.max_runs)
    downloaded: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    artifact_seen = 0

    for run in workflow_runs[: settings.max_runs]:
        run_id = str(run.get("id", ""))
        if not run_id:
            continue
        for artifact in client.list_run_artifacts(settings.repository, run_id):
            artifact_seen += 1
            if artifact_seen > settings.max_artifacts:
                break
            artifact_id = str(artifact.get("id", ""))
            artifact_name = str(artifact.get("name", ""))
            if not artifact_id or not artifact_name.startswith(settings.artifact_name_prefix):
                continue
            if artifact.get("expired") is True:
                skipped.append({"run_id": run_id, "artifact_id": artifact_id, "artifact_name": artifact_name, "reason": "expired"})
                continue

            key = _artifact_key(settings.repository, run_id, artifact_id)
            if not args.force and key in state["synced_artifact_keys"]:
                skipped.append({"run_id": run_id, "artifact_id": artifact_id, "artifact_name": artifact_name, "reason": "already_synced"})
                continue

            staging_dir = settings.staging_root / settings.repository.replace("/", "__") / run_id / artifact_id
            archive_bytes = client.download_artifact(settings.repository, artifact)
            try:
                _extract_zip_safe(archive_bytes, staging_dir)
            except BadZipFile as exc:
                errors.append({"run_id": run_id, "artifact_id": artifact_id, "artifact_name": artifact_name, "error": f"bad_zip: {exc}"})
                continue

            sync_report = _run_server_dataset_sync(
                settings.sync_tool,
                args.config,
                staging_dir,
                run_id,
                artifact_id,
            )
            sync_status = str(sync_report.get("status", "unknown"))
            if sync_status == "ok":
                state["synced_artifact_keys"].append(key)
                state["artifacts"][key] = {
                    "repository": settings.repository,
                    "run_id": run_id,
                    "artifact_id": artifact_id,
                    "artifact_name": artifact_name,
                    "staging_dir": str(staging_dir),
                    "sync_status": sync_status,
                    "vispy_event_path": sync_report.get("vispy_event_path"),
                }
            downloaded.append(
                {
                    "repository": settings.repository,
                    "run_id": run_id,
                    "artifact_id": artifact_id,
                    "artifact_name": artifact_name,
                    "staging_dir": str(staging_dir),
                    "sync_status": sync_status,
                    "sync_report": sync_report,
                }
            )

    _write_state(settings.state_path, state)

    report = {
        "schema": _SCHEMA,
        "status": "ok" if not errors else "partial",
        "repository": settings.repository,
        "workflow_name": settings.workflow_name,
        "artifact_name_prefix": settings.artifact_name_prefix,
        "external_call_performed": external_call_performed,
        "counts": {
            "workflow_run_count": len(workflow_runs),
            "artifact_seen_count": artifact_seen,
            "downloaded_count": len(downloaded),
            "synced_count": sum(1 for item in downloaded if item["sync_status"] == "ok"),
            "skipped_count": len(skipped),
            "error_count": len(errors),
        },
        "downloaded_artifacts": downloaded,
        "skipped": skipped,
        "errors": errors,
        "state_path": str(settings.state_path),
        "staging_root": str(settings.staging_root),
        "boundary": [
            "read-only GitHub Actions artifact fetch",
            "uses configured server dataset",
            "calls 0167 server dataset sync",
            "no conversion before complete sync",
            "no remote mutation",
            "no SQL write",
            "no qdrant write",
        ],
    }

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        print(f"downloaded: {report['counts']['downloaded_count']}")
        print(f"synced: {report['counts']['synced_count']}")
        print(f"skipped: {report['counts']['skipped_count']}")
        print(f"state_path: {settings.state_path}")

    return 0 if not errors else 1


class GitHubActionsClient:
    def __init__(self, api_url: str, token: str) -> None:
        self.api_url = api_url.rstrip("/")
        self.token = token

    def list_workflow_runs(self, repository: str, workflow_name: str, max_runs: int) -> list[Mapping[str, Any]]:
        workflow = quote(workflow_name, safe="")
        query = urlencode({"per_page": str(max_runs), "status": "completed"})
        payload = self._get_json(f"/repos/{repository}/actions/workflows/{workflow}/runs?{query}")
        runs = payload.get("workflow_runs", [])
        return runs if isinstance(runs, list) else []

    def list_run_artifacts(self, repository: str, run_id: str) -> list[Mapping[str, Any]]:
        payload = self._get_json(f"/repos/{repository}/actions/runs/{run_id}/artifacts?per_page=100")
        artifacts = payload.get("artifacts", [])
        return artifacts if isinstance(artifacts, list) else []

    def download_artifact(self, repository: str, artifact: Mapping[str, Any]) -> bytes:
        url = str(artifact.get("archive_download_url", ""))
        if not url:
            artifact_id = quote(str(artifact.get("id", "")), safe="")
            url = f"{self.api_url}/repos/{repository}/actions/artifacts/{artifact_id}/zip"
        return self._download_artifact_archive(url)

    def _download_artifact_archive(self, url: str) -> bytes:
        from urllib.error import HTTPError
        from urllib.parse import urlsplit
        from urllib.request import (
            HTTPRedirectHandler,
            Request,
            build_opener,
            urlopen,
        )

        class _NoRedirectHandler(HTTPRedirectHandler):
            def redirect_request(
                self,
                req,
                fp,
                code,
                msg,
                headers,
                newurl,
            ):
                return None

        api_origin = urlsplit(self.api_url)
        download_origin = urlsplit(url)
        if (
            download_origin.scheme.lower()
            != api_origin.scheme.lower()
            or download_origin.netloc.lower()
            != api_origin.netloc.lower()
        ):
            raise ValueError(
                "artifact API download URL must remain on the "
                "configured GitHub API origin"
            )

        api_request = Request(url)
        api_request.add_header(
            "Accept",
            "application/vnd.github+json",
        )
        api_request.add_header(
            "Authorization",
            f"Bearer {self.token}",
        )
        api_request.add_header(
            "X-GitHub-Api-Version",
            "2022-11-28",
        )

        opener = build_opener(_NoRedirectHandler())
        try:
            with opener.open(api_request, timeout=30) as response:
                return response.read()
        except HTTPError as exc:
            try:
                if exc.code not in (301, 302, 303, 307, 308):
                    raise
                location = str(
                    exc.headers.get("Location", "")
                    if exc.headers is not None
                    else ""
                ).strip()
            finally:
                exc.close()

        redirected = urlsplit(location)
        if (
            redirected.scheme.lower() != "https"
            or not redirected.hostname
            or redirected.username is not None
            or redirected.password is not None
        ):
            raise ValueError(
                "artifact redirect URL must be credential-free HTTPS"
            )

        artifact_request = Request(location)
        artifact_request.add_header(
            "Accept",
            "application/zip",
        )
        with urlopen(artifact_request, timeout=30) as response:
            return response.read()


    def _get_json(self, path: str) -> Mapping[str, Any]:
        data = self._get_bytes(f"{self.api_url}{path}", absolute=True)
        payload = json.loads(data.decode("utf-8"))
        return payload if isinstance(payload, Mapping) else {}

    def _get_bytes(self, url: str, *, absolute: bool) -> bytes:
        request = Request(url if absolute else f"{self.api_url}{url}")
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        with urlopen(request, timeout=30) as response:  # noqa: S310 - controlled HTTPS API URL from config
            return response.read()


class FixtureClient:
    def __init__(self, fixture_root: Path | None) -> None:
        if fixture_root is None:
            raise ValueError("fixture_root required")
        self.fixture_root = fixture_root

    def list_workflow_runs(self, repository: str, workflow_name: str, max_runs: int) -> list[Mapping[str, Any]]:
        payload = _read_json(self.fixture_root / "workflow_runs.json")
        runs = payload.get("workflow_runs", [])
        return runs[:max_runs] if isinstance(runs, list) else []

    def list_run_artifacts(self, repository: str, run_id: str) -> list[Mapping[str, Any]]:
        payload = _read_json(self.fixture_root / f"run_{run_id}_artifacts.json")
        artifacts = payload.get("artifacts", [])
        return artifacts if isinstance(artifacts, list) else []

    def download_artifact(self, repository: str, artifact: Mapping[str, Any]) -> bytes:
        artifact_id = str(artifact.get("id", ""))
        return (self.fixture_root / f"artifact_{artifact_id}.zip").read_bytes()


def _load_settings(args: argparse.Namespace) -> FetchSettings:
    if load_github_artifact_server_fetch_config is not None:
        loaded = load_github_artifact_server_fetch_config(args.config)
        if validate_github_artifact_server_fetch_config is not None:
            validation = validate_github_artifact_server_fetch_config(loaded)
            if isinstance(validation, Mapping) and validation.get("status") == "blocked":
                raise SystemExit(f"config validation blocked: {validation}")

    parser = configparser.ConfigParser()
    parser.read(args.config, encoding="utf-8")
    github = parser["github"] if parser.has_section("github") else {}
    source = parser["artifact_source"] if parser.has_section("artifact_source") else {}
    safety = parser["safety"] if parser.has_section("safety") else {}
    dataset = parser["server_dataset"] if parser.has_section("server_dataset") else {}
    if not dataset and parser.has_section("dataset"):
        dataset = parser["dataset"]

    repositories = _list_value(source.get("repositories", ""))
    allowed = tuple(_list_value(safety.get("allowed_repositories", "")) or repositories)
    repository = args.repository or (repositories[0] if repositories else "")
    workflow_name = args.workflow_name or str(source.get("workflow_name", "autodoc-ticket-artifact.yml"))
    artifact_name_prefix = args.artifact_name_prefix or str(source.get("artifact_name_prefix", "autodoc-ticket-artifact-"))
    dataset_root = Path(str(dataset.get("root") or dataset.get("dataset_root") or ".var/server_datasets/github_artifacts")).expanduser()
    staging_root = args.staging_root or dataset_root / "staging" / "github_actions_artifacts"
    state_path = args.state_path or dataset_root / "index" / "github_actions_fetch_state.json"

    return FetchSettings(
        repository=repository,
        allowed_repositories=allowed,
        workflow_name=workflow_name,
        artifact_name_prefix=artifact_name_prefix,
        api_url=str(github.get("api_url", _DEFAULT_API_URL)),
        token_env=str(github.get("token_env", "GITHUB_TOKEN")),
        dataset_root=dataset_root,
        staging_root=staging_root,
        state_path=state_path,
        sync_tool=args.sync_tool,
        max_runs=args.max_runs,
        max_artifacts=args.max_artifacts,
    )


def _validate_settings(settings: FetchSettings) -> None:
    if not settings.repository:
        raise SystemExit("repository missing")
    if settings.repository not in settings.allowed_repositories:
        raise SystemExit(f"repository not allowed by config: {settings.repository}")
    if settings.repository == "newicody/autodoc":
        raise SystemExit("development repository cannot be used as external artifact source")
    if not settings.workflow_name:
        raise SystemExit("workflow_name missing")
    if not settings.artifact_name_prefix:
        raise SystemExit("artifact_name_prefix missing")


def _run_server_dataset_sync(sync_tool: Path, config_path: Path, artifact_dir: Path, run_id: str, artifact_id: str) -> Mapping[str, Any]:
    command = [
        sys.executable,
        str(sync_tool),
        "--config",
        str(config_path),
        "--artifact-dir",
        str(artifact_dir),
        "--run-id",
        run_id,
        "--artifact-id",
        artifact_id,
        "--format",
        "json",
    ]
    completed = subprocess.run(command, cwd=_REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    payload = json.loads(completed.stdout)
    return payload if isinstance(payload, Mapping) else {}


def _extract_zip_safe(archive_bytes: bytes, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    target_root = target_dir.resolve()
    with ZipFile(BytesIO(archive_bytes)) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            destination = (target_dir / member.filename).resolve()
            if not destination.is_relative_to(target_root):
                raise ValueError(f"unsafe artifact member path: {member.filename}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(member))


def _read_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema": _STATE_SCHEMA, "synced_artifact_keys": [], "artifacts": {}}
    payload = _read_json(path)
    keys = payload.get("synced_artifact_keys", [])
    artifacts = payload.get("artifacts", {})
    return {
        "schema": _STATE_SCHEMA,
        "synced_artifact_keys": list(keys) if isinstance(keys, list) else [],
        "artifacts": dict(artifacts) if isinstance(artifacts, Mapping) else {},
    }


def _write_state(path: Path, state: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, Mapping) else {}


def _list_value(value: object) -> list[str]:
    return [item.strip() for item in str(value or "").replace("\n", ",").split(",") if item.strip()]


def _artifact_key(repository: str, run_id: str, artifact_id: str) -> str:
    return f"{repository}:{run_id}:{artifact_id}"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
