#!/usr/bin/env python3
from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import time
from typing import Callable

from context.cell_snapshot_journal_reader import tail_cell_snapshot_jsonl
from context.cell_snapshot_sse import cell_journal_to_sse_text, snapshots_to_sse_text


DEFAULT_BIND_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
CELL_STREAM_PATH = "/cells.sse"
HEALTH_PATH = "/health"


def build_replay_sse_text(journal: Path, *, limit: int | None = None, start_sequence: int = 0) -> str:
    return cell_journal_to_sse_text(journal, limit=limit, start_sequence=start_sequence)


def make_cell_sse_handler(
    *,
    journal: Path,
    tail: bool = False,
    replay_limit: int | None = None,
    poll_seconds: float = 0.50,
    max_tail_lines: int = 512,
) -> type[BaseHTTPRequestHandler]:
    if poll_seconds <= 0:
        raise ValueError("poll_seconds must be > 0")
    if max_tail_lines <= 0:
        raise ValueError("max_tail_lines must be > 0")

    class CellSseHandler(BaseHTTPRequestHandler):
        server_version = "MissiPyCellSse/0.1"

        def do_GET(self) -> None:  # noqa: N802
            if self.path == HEALTH_PATH:
                self._send_text(HTTPStatus.OK, "ok\n")
                return
            if self.path != CELL_STREAM_PATH:
                self._send_text(HTTPStatus.NOT_FOUND, "not found\n")
                return

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            sequence = 0
            replay_text = build_replay_sse_text(journal, limit=replay_limit, start_sequence=sequence)
            if replay_text:
                self.wfile.write(replay_text.encode("utf-8"))
                self.wfile.flush()
                sequence += replay_text.count("\nevent: cell_snapshot\n")

            offset = journal.stat().st_size if journal.exists() else 0
            if not tail:
                return

            while True:
                result = tail_cell_snapshot_jsonl(journal, offset=offset, max_lines=max_tail_lines)
                offset = result.next_offset
                if result.snapshots:
                    text = snapshots_to_sse_text(result.snapshots, start_sequence=sequence)
                    self.wfile.write(text.encode("utf-8"))
                    self.wfile.flush()
                    sequence += len(result.snapshots)
                time.sleep(poll_seconds)

        def do_POST(self) -> None:  # noqa: N802
            self._send_text(HTTPStatus.METHOD_NOT_ALLOWED, "read only\n")

        def do_PUT(self) -> None:  # noqa: N802
            self._send_text(HTTPStatus.METHOD_NOT_ALLOWED, "read only\n")

        def do_DELETE(self) -> None:  # noqa: N802
            self._send_text(HTTPStatus.METHOD_NOT_ALLOWED, "read only\n")

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_text(self, status: HTTPStatus, body: str) -> None:
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return CellSseHandler


def serve_cell_sse(
    *,
    journal: Path,
    host: str = DEFAULT_BIND_HOST,
    port: int = DEFAULT_PORT,
    tail: bool = False,
    replay_limit: int | None = None,
    poll_seconds: float = 0.50,
    max_tail_lines: int = 512,
    server_factory: Callable[..., ThreadingHTTPServer] = ThreadingHTTPServer,
) -> None:
    if host != DEFAULT_BIND_HOST:
        raise ValueError("cell SSE endpoint is local-only; host must be 127.0.0.1")
    if port <= 0:
        raise ValueError("port must be > 0")

    handler = make_cell_sse_handler(
        journal=journal,
        tail=tail,
        replay_limit=replay_limit,
        poll_seconds=poll_seconds,
        max_tail_lines=max_tail_lines,
    )
    server = server_factory((host, port), handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve a read-only local SSE stream from a missipy.cell.v1 journal.")
    parser.add_argument("--journal", required=True)
    parser.add_argument("--host", default=DEFAULT_BIND_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--tail", action="store_true")
    parser.add_argument("--replay-limit", type=int, default=None)
    parser.add_argument("--poll-seconds", type=float, default=0.50)
    parser.add_argument("--max-tail-lines", type=int, default=512)
    args = parser.parse_args()

    serve_cell_sse(
        journal=Path(args.journal),
        host=args.host,
        port=args.port,
        tail=args.tail,
        replay_limit=args.replay_limit,
        poll_seconds=args.poll_seconds,
        max_tail_lines=args.max_tail_lines,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
