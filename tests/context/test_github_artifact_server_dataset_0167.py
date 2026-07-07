from __future__ import annotations

from pathlib import Path

from context.github_artifact_server_dataset import (
    ServerDatasetLayout,
    build_conversion_queue_ref,
    build_raw_dataset_ref,
    infer_attachment_kind,
)
from context.github_artifact_server_fetch_config import load_github_artifact_server_fetch_config


def _config_text(root: Path) -> str:
    return f"""[github]
token_env = GITHUB_TOKEN
api_url = https://api.github.com

[project]
url = https://github.com/users/newicody/projects/2

[artifact_source]
repositories = newicody/autodoc-ideas
workflow_name = autodoc-ticket-artifact.yml
artifact_name_prefix = autodoc-ticket-artifact-

[server_dataset]
root = {root}
raw_dir = raw
index_dir = index
history_dir = history
conversion_queue_dir = conversion_queue
converted_dir = converted
vispy_events_dir = vispy_events
state_file = index/fetch_state.json

[attachments]
allowed_kinds = image, audio, video, pdf, archive, text, binary
max_attachment_bytes = 524288000

[conversion]
queue_after_complete_sync = true
skip_already_processed = true

[safety]
development_repository = newicody/autodoc
allowed_repositories = newicody/autodoc-ideas
"""


def test_0167_config_loads_server_dataset_boundary(tmp_path: Path) -> None:
    path = tmp_path / "fetch.ini"
    path.write_text(_config_text(tmp_path / "dataset"), encoding="utf-8")
    config = load_github_artifact_server_fetch_config(path)

    assert config.external_repository == "newicody/autodoc-ideas"
    assert config.development_repository == "newicody/autodoc"
    assert config.dataset.root == tmp_path / "dataset"
    assert config.queue_after_complete_sync is True
    assert "image" in config.allowed_attachment_kinds


def test_0167_dataset_layout_paths_are_under_root(tmp_path: Path) -> None:
    layout = ServerDatasetLayout(root=tmp_path / "dataset")

    assert layout.raw_path == tmp_path / "dataset" / "raw"
    assert layout.conversion_queue_path == tmp_path / "dataset" / "conversion_queue"
    assert layout.vispy_events_path == tmp_path / "dataset" / "vispy_events"


def test_0167_attachment_kind_detection() -> None:
    assert infer_attachment_kind(Path("photo.jpg")) == "image"
    assert infer_attachment_kind(Path("music.mp3")) == "audio"
    assert infer_attachment_kind(Path("clip.mp4")) == "video"
    assert infer_attachment_kind(Path("document.pdf")) == "pdf"
    assert infer_attachment_kind(Path("archive.zip")) == "archive"
    assert infer_attachment_kind(Path("notes.txt")) == "text"
    assert infer_attachment_kind(Path("blob.bin")) == "binary"


def test_0167_dataset_refs_are_stable() -> None:
    raw_ref = build_raw_dataset_ref("newicody/autodoc-ideas", "run1", "artifact1", "attachments/photo.jpg")
    queue_ref = build_conversion_queue_ref(raw_ref, "abc")

    assert raw_ref.startswith("server-dataset:github-artifacts/raw/newicody__autodoc-ideas/run1/artifact1")
    assert queue_ref.startswith("server-dataset:github-artifacts/conversion-queue/")
