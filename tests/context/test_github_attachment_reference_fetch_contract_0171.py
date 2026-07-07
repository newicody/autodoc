from __future__ import annotations

from context.github_attachment_reference_fetch import (
    attachment_kind_from_filename,
    extract_attachment_references,
    safe_attachment_filename,
)


def test_0171_classifies_attachment_kinds() -> None:
    assert attachment_kind_from_filename("photo.jpg") == "image"
    assert attachment_kind_from_filename("voice.mp3") == "audio"
    assert attachment_kind_from_filename("clip.mp4") == "video"
    assert attachment_kind_from_filename("plan.pdf") == "pdf"
    assert attachment_kind_from_filename("bundle.zip") == "archive"
    assert attachment_kind_from_filename("notes.txt") == "text"
    assert attachment_kind_from_filename("firmware.bin") == "binary"


def test_0171_extracts_reference_only_manifest() -> None:
    manifest = {
        "attachments": [
            {"url": "https://github.com/user-attachments/assets/photo.jpg", "filename": "photo.jpg"},
            {"href": "https://github.com/user-attachments/assets/notes.txt"},
        ]
    }
    refs = extract_attachment_references(manifest)

    assert [ref.filename for ref in refs] == ["photo.jpg", "notes.txt"]
    assert [ref.kind for ref in refs] == ["image", "text"]


def test_0171_sanitizes_attachment_filename() -> None:
    assert safe_attachment_filename("../evil name.jpg") == "evil_name.jpg"
    assert safe_attachment_filename("https://example.invalid/a/b/file.pdf?download=1") == "file.pdf"
