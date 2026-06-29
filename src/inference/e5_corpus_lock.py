from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class E5CorpusBuildLockError(RuntimeError):
    """Erreur de verrouillage du build de corpus E5."""


@dataclass(frozen=True, slots=True)
class E5CorpusBuildLockInfo:
    """Informations stables écrites dans le fichier de verrou.

    Le fichier sert d'indicateur opérationnel, pas de source métier. Il reste
    volontairement simple pour pouvoir être inspecté ou supprimé manuellement si
    un ancien build s'est interrompu brutalement.
    """

    target: str
    lock_path: str
    pid: int

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": "missipy.e5.corpus.lock.v1",
            "target": self.target,
            "lock_path": self.lock_path,
            "pid": self.pid,
        }


class E5CorpusBuildLock:
    """Verrou fichier exclusif pour la construction d'un corpus E5.

    Le verrou est acquis par création atomique ``O_CREAT | O_EXCL``. Il ne fait
    pas de busy-wait et ne prend aucune décision de stale-lock : si le fichier
    existe déjà, le build échoue explicitement pour éviter deux écritures
    concurrentes vers le même corpus.
    """

    def __init__(self, target: str | Path, *, lock_path: str | Path | None = None) -> None:
        self._target = Path(target)
        self._lock_path = Path(lock_path) if lock_path is not None else build_e5_corpus_lock_path(self._target)
        self._acquired = False
        self._info: E5CorpusBuildLockInfo | None = None

    @property
    def target(self) -> Path:
        return self._target

    @property
    def path(self) -> Path:
        return self._lock_path

    @property
    def acquired(self) -> bool:
        return self._acquired

    @property
    def info(self) -> E5CorpusBuildLockInfo | None:
        return self._info

    def acquire(self) -> E5CorpusBuildLockInfo:
        """Acquiert le verrou ou lève une erreur si un build est déjà actif."""

        if self._acquired:
            raise E5CorpusBuildLockError(f"E5 corpus build lock already acquired: {self._lock_path}")
        if not self._lock_path.parent.exists():
            raise FileNotFoundError(self._lock_path.parent)
        info = E5CorpusBuildLockInfo(
            target=str(self._target),
            lock_path=str(self._lock_path),
            pid=os.getpid(),
        )
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(self._lock_path, flags, 0o600)
        except FileExistsError as exc:
            raise E5CorpusBuildLockError(f"E5 corpus build already locked: {self._lock_path}") from exc
        try:
            payload = json.dumps(info.to_json_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            os.write(fd, payload.encode("utf-8"))
        finally:
            os.close(fd)
        self._acquired = True
        self._info = info
        return info

    def release(self) -> None:
        """Libère le verrou si ce processus l'a acquis."""

        if not self._acquired:
            return
        try:
            self._lock_path.unlink()
        except FileNotFoundError:
            pass
        finally:
            self._acquired = False
            self._info = None

    def __enter__(self) -> E5CorpusBuildLock:
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.release()


def build_e5_corpus_lock_path(target: str | Path) -> Path:
    """Retourne le chemin de verrou associé à un fichier de corpus."""

    path = Path(target)
    if not path.name:
        raise ValueError("E5 corpus lock target must have a filename")
    return path.with_name(f".{path.name}.lock")
