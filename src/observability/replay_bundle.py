from __future__ import annotations

import json
from collections.abc import Iterable
from os import PathLike
from pathlib import Path
from typing import Literal

from contracts.replay import ReplayBundleWriteResult, ReplayReport, ReplayReportExport
from observability.replay_exporter import ReplayReportExporter
from observability.replay_writer import ReplayReportFileWriter

ReplayExportFormat = Literal["text", "json"]


class ReplayReportBundleWriter:
    """Écriture contrôlée d'un dossier replay déterministe.

    Le bundle writer reste dans la couche observability. Il ne connaît pas le
    Scheduler, ne publie aucun événement et ne rejoue rien. Il assemble des
    exports déjà déterministes avec un manifeste JSON stable.
    """

    schema = "missipy.replay.bundle.v1"

    def __init__(
        self,
        exporter: ReplayReportExporter | None = None,
        file_writer: ReplayReportFileWriter | None = None,
    ) -> None:
        self._exporter = exporter or ReplayReportExporter()
        self._file_writer = file_writer or ReplayReportFileWriter()

    def write(
        self,
        report: ReplayReport,
        directory: str | PathLike[str],
        *,
        formats: Iterable[ReplayExportFormat] = ("text", "json"),
        overwrite: bool = False,
        create_parents: bool = False,
    ) -> ReplayBundleWriteResult:
        """Écrit un dossier replay contrôlé.

        Le dossier contient les exports demandés et ``manifest.json``. Aucun
        chemin n'est inventé hors de ce dossier, et l'écrasement reste explicite.
        """

        target_dir = self._normalize_directory(directory)
        format_tuple = self._normalize_formats(formats)

        if create_parents:
            target_dir.mkdir(parents=True, exist_ok=True)
        elif not target_dir.exists():
            raise FileNotFoundError(f"replay bundle directory does not exist: {target_dir}")

        if not target_dir.is_dir():
            raise NotADirectoryError(str(target_dir))

        targets = tuple((fmt, target_dir / self._filename_for(fmt)) for fmt in format_tuple)
        manifest_target = target_dir / "manifest.json"
        self._preflight_targets(tuple(path for _, path in targets) + (manifest_target,), overwrite)

        write_results = []
        for fmt, path in targets:
            export = self._export_for(report, fmt)
            write_results.append(
                self._file_writer.write(
                    export,
                    path,
                    overwrite=overwrite,
                    create_parents=False,
                )
            )

        manifest_export = self._manifest_export(write_results)
        manifest_result = self._file_writer.write(
            manifest_export,
            manifest_target,
            overwrite=overwrite,
            create_parents=False,
        )

        return ReplayBundleWriteResult(
            directory=str(target_dir),
            files=tuple(write_results),
            manifest=manifest_result,
        )

    def _normalize_directory(self, directory: str | PathLike[str]) -> Path:
        if isinstance(directory, str) and not directory:
            raise ValueError("directory must not be empty")
        return Path(directory)

    def _normalize_formats(
        self,
        formats: Iterable[ReplayExportFormat],
    ) -> tuple[ReplayExportFormat, ...]:
        result = tuple(formats)
        if not result:
            raise ValueError("at least one replay export format is required")
        duplicates = {fmt for fmt in result if result.count(fmt) > 1}
        if duplicates:
            raise ValueError(f"duplicate replay export formats: {sorted(duplicates)!r}")
        unknown = tuple(fmt for fmt in result if fmt not in {"text", "json"})
        if unknown:
            raise ValueError(f"unsupported replay export formats: {unknown!r}")
        return result

    def _filename_for(self, fmt: ReplayExportFormat) -> str:
        if fmt == "text":
            return "report.txt"
        if fmt == "json":
            return "report.json"
        raise ValueError(f"unsupported replay export format: {fmt!r}")

    def _export_for(self, report: ReplayReport, fmt: ReplayExportFormat) -> ReplayReportExport:
        if fmt == "text":
            return self._exporter.to_text(report)
        if fmt == "json":
            return self._exporter.to_json(report)
        raise ValueError(f"unsupported replay export format: {fmt!r}")

    def _preflight_targets(self, targets: tuple[Path, ...], overwrite: bool) -> None:
        if overwrite:
            return
        existing = tuple(path for path in targets if path.exists())
        if existing:
            raise FileExistsError(str(existing[0]))

    def _manifest_export(self, write_results: list) -> ReplayReportExport:
        data = {
            "schema": self.schema,
            "files": [
                {
                    "path": Path(result.path).name,
                    "format": result.format,
                    "media_type": result.media_type,
                    "bytes_written": result.bytes_written,
                    "sha256": result.sha256,
                }
                for result in write_results
            ],
        }
        content = json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return ReplayReportExport(
            format="manifest",
            media_type="application/json; charset=utf-8",
            content=content,
        )
