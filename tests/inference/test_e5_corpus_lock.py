from __future__ import annotations

import json

import pytest

from inference.e5_corpus_lock import (
    E5CorpusBuildLock,
    E5CorpusBuildLockError,
    build_e5_corpus_lock_path,
)


def test_build_lock_path_is_neighbor_hidden_file(tmp_path) -> None:
    target = tmp_path / "corpus.json"

    assert build_e5_corpus_lock_path(target) == tmp_path / ".corpus.json.lock"


def test_build_lock_acquire_writes_info_and_release_removes_file(tmp_path) -> None:
    target = tmp_path / "corpus.json"
    lock = E5CorpusBuildLock(target)

    info = lock.acquire()

    assert lock.acquired is True
    assert lock.info == info
    assert lock.path.exists()
    payload = json.loads(lock.path.read_text(encoding="utf-8"))
    assert payload["schema"] == "missipy.e5.corpus.lock.v1"
    assert payload["target"] == str(target)
    assert payload["lock_path"] == str(lock.path)
    assert isinstance(payload["pid"], int)

    lock.release()

    assert lock.acquired is False
    assert lock.info is None
    assert not lock.path.exists()


def test_build_lock_context_releases_on_exception(tmp_path) -> None:
    target = tmp_path / "corpus.json"
    lock_path = build_e5_corpus_lock_path(target)

    with pytest.raises(RuntimeError, match="boom"):
        with E5CorpusBuildLock(target):
            assert lock_path.exists()
            raise RuntimeError("boom")

    assert not lock_path.exists()


def test_build_lock_rejects_existing_lock(tmp_path) -> None:
    target = tmp_path / "corpus.json"
    first = E5CorpusBuildLock(target)
    first.acquire()
    try:
        with pytest.raises(E5CorpusBuildLockError, match="already locked"):
            E5CorpusBuildLock(target).acquire()
    finally:
        first.release()


def test_build_lock_rejects_missing_parent(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        E5CorpusBuildLock(tmp_path / "missing" / "corpus.json").acquire()
