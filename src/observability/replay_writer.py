from __future__ import annotations

import hashlib
from os import PathLike
from pathlib import Path

from contracts.replay import ReplayReportExport, ReplayReportWriteResult


class ReplayReportFileWriter:
    """Écriture contrôlée des exports de replay vers le système de fichiers.

    Le writer reste dans la couche observability. Il ne connaît pas le
    Scheduler, ne publie aucun événement et n'exécute aucun replay. Il persiste
    seulement un ReplayReportExport déjà sérialisé par ReplayReportExporter.
    
    Les chemins sont toujours explicites : aucune extension n'est ajoutée,
    aucun répertoire parent n'est créé sans demande explicite, et un fichier
    existant n'est jamais écrasé sans ``overwrite=True``.
    """

    encoding = "utf-8"

    def write(
        self,
        export: ReplayReportExport,
        path: str | PathLike[str],
        *,
        overwrite: bool = False,
        create_parents: bool = False,
    ) -> ReplayReportWriteResult:
        """Écrit un export texte/JSON vers un fichier explicite.

        Args:
            export: export déjà sérialisé.
            path: chemin exact du fichier cible.
            overwrite: autorise l'écrasement si le fichier existe.
            create_parents: crée les répertoires parents manquants.

        Raises:
            FileExistsError: si la cible existe et ``overwrite`` est faux.
            FileNotFoundError: si le parent est absent et ``create_parents`` est faux.
            IsADirectoryError: si la cible est un répertoire.
            ValueError: si le chemin est vide.
        """

        target = self._normalize_path(path)
        parent = target.parent

        if create_parents:
            parent.mkdir(parents=True, exist_ok=True)
        elif not parent.exists():
            raise FileNotFoundError(f"parent directory does not exist: {parent}")

        if target.exists() and target.is_dir():
            raise IsADirectoryError(str(target))

        if overwrite:
            target.write_text(export.content, encoding=self.encoding)
        else:
            self._write_new(target, export.content)

        data = export.content.encode(self.encoding)
        return ReplayReportWriteResult(
            path=str(target),
            format=export.format,
            media_type=export.media_type,
            bytes_written=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
        )

    def _write_new(self, target: Path, content: str) -> None:
        with target.open("x", encoding=self.encoding) as stream:
            stream.write(content)

    def _normalize_path(self, path: str | PathLike[str]) -> Path:
        if isinstance(path, str) and not path:
            raise ValueError("path must not be empty")
        target = Path(path)
        if target == Path("."):
            raise ValueError("path must point to a file")
        return target
