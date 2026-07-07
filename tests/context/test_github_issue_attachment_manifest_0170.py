from __future__ import annotations

from context.github_issue_attachment_manifest import build_github_issue_attachment_manifest, parse_github_issue_attachment_references


def test_0170_parses_github_issue_attachment_references() -> None:
    body = """
Voici les pièces jointes:

![photo.jpg](https://github.com/user-attachments/assets/photo.jpg)
[plan.pdf](https://github.com/user-attachments/assets/plan.pdf)
[archive.zip](https://github.com/user-attachments/assets/archive.zip)
https://github.com/user-attachments/assets/audio.mp3
"""
    refs = parse_github_issue_attachment_references(body)

    assert [ref.kind for ref in refs] == ["image", "pdf", "archive", "audio"]
    assert refs[0].filename == "photo.jpg"
    assert refs[1].filename == "plan.pdf"
    assert all(ref.processed is False for ref in refs)


def test_0170_builds_manifest_without_remote_access() -> None:
    manifest = build_github_issue_attachment_manifest(
        repository="newicody/autodoc-ideas",
        issue_number=42,
        issue_url="https://github.com/newicody/autodoc-ideas/issues/42",
        body="![image](https://github.com/user-attachments/assets/123456)",
    )
    payload = manifest.to_json_dict()

    assert payload["schema"] == "missipy.github_issue.attachment_manifest.v1"
    assert payload["counts"]["attachment_count"] == 1
    assert payload["attachments"][0]["kind"] == "image"
    assert "no GitHub API call" in payload["boundary"]
    assert "no user artifacts in Autodoc repository" in payload["boundary"]
