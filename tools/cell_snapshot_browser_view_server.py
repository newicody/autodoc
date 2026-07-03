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
DEFAULT_PORT = 8766
ROOT_VIEW_PATH = "/"
BROWSER_VIEW_PATH = "/view.html"
CELL_STREAM_PATH = "/cells.sse"
HEALTH_PATH = "/health"


BROWSER_VIEW_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>MissiPy Cell Lens</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: #05070b; color: #d8e2f0; font-family: sans-serif; }
  canvas { width: 100vw; height: 100vh; display: block; }
  #panel { position: fixed; left: 12px; top: 12px; padding: 10px 12px; background: rgba(0,0,0,.62); border: 1px solid rgba(255,255,255,.18); border-radius: 8px; font-size: 13px; line-height: 1.35; }
  #state { font-weight: bold; }
</style>
</head>
<body>
<canvas id="cells"></canvas>
<div id="panel">
  <div>MissiPy Cell Lens — read-only</div>
  <div>stream: <code>/cells.sse</code></div>
  <div>state: <span id="state">connecting</span></div>
  <div>cells: <span id="count">0</span></div>
</div>
<script>
(() => {
  const canvas = document.getElementById("cells");
  const ctx = canvas.getContext("2d");
  const state = document.getElementById("state");
  const count = document.getElementById("count");
  const cells = new Map();

  function resize() {
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.floor(window.innerWidth * ratio);
    canvas.height = Math.floor(window.innerHeight * ratio);
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    draw();
  }

  function hashUnit(text, salt) {
    let h = 2166136261 ^ salt;
    for (let i = 0; i < text.length; i++) {
      h ^= text.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return ((h >>> 0) / 4294967295);
  }

  function colorFor(snapshot) {
    if (snapshot.lifecycle_state === "failed" || snapshot.lifecycle_state === "cancelled" || snapshot.lifecycle_state === "dropped") return "#777";
    if (snapshot.source_class === "llm.answer") return "#67a7ff";
    if (snapshot.source_class === "ingest.batch") return "#c184ff";
    if (snapshot.source_class === "recorder.write") return "#65e6a2";
    return "#ffd166";
  }

  function pointFor(snapshot) {
    const key = snapshot.source_class + ":" + snapshot.cell_id;
    const a = hashUnit(key, 1) * Math.PI * 2;
    const r = Math.sqrt(hashUnit(key, 2));
    const w = window.innerWidth;
    const h = window.innerHeight;
    return {
      x: w * 0.5 + Math.cos(a) * r * w * 0.42,
      y: h * 0.5 + Math.sin(a) * r * h * 0.42,
      radius: 4 + Math.min(18, Math.sqrt(Math.max(0, snapshot.cost || 0)) * 1.5),
      color: colorFor(snapshot),
    };
  }

  function draw() {
    if (!ctx) return;
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    ctx.fillStyle = "#05070b";
    ctx.fillRect(0, 0, window.innerWidth, window.innerHeight);

    for (const snapshot of cells.values()) {
      const point = pointFor(snapshot);
      ctx.beginPath();
      ctx.arc(point.x, point.y, point.radius, 0, Math.PI * 2);
      ctx.fillStyle = point.color;
      ctx.globalAlpha = 0.78;
      ctx.fill();
      ctx.globalAlpha = 1.0;
    }

    count.textContent = String(cells.size);
  }

  function connect() {
    const events = new EventSource("/cells.sse");
    events.addEventListener("open", () => { state.textContent = "connected"; });
    events.addEventListener("error", () => { state.textContent = "reconnecting"; });
    events.addEventListener("cell_snapshot", (event) => {
      const payload = JSON.parse(event.data);
      const snapshot = payload.snapshot;
      cells.set(snapshot.cell_id, snapshot);
      draw();
    });
  }

  window.addEventListener("resize", resize);
  resize();
  connect();
})();
</script>
</body>
</html>
"""


def make_browser_view_handler(
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

    class BrowserViewHandler(BaseHTTPRequestHandler):
        server_version = "MissiPyCellBrowserView/0.1"

        def do_GET(self) -> None:  # noqa: N802
            if self.path == HEALTH_PATH:
                self._send_text(HTTPStatus.OK, "ok\n")
                return
            if self.path in {ROOT_VIEW_PATH, BROWSER_VIEW_PATH}:
                self._send_html(HTTPStatus.OK, BROWSER_VIEW_HTML)
                return
            if self.path == CELL_STREAM_PATH:
                self._send_sse()
                return
            self._send_text(HTTPStatus.NOT_FOUND, "not found\n")

        def do_POST(self) -> None:  # noqa: N802
            self._send_text(HTTPStatus.METHOD_NOT_ALLOWED, "read only\n")

        def do_PUT(self) -> None:  # noqa: N802
            self._send_text(HTTPStatus.METHOD_NOT_ALLOWED, "read only\n")

        def do_DELETE(self) -> None:  # noqa: N802
            self._send_text(HTTPStatus.METHOD_NOT_ALLOWED, "read only\n")

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_html(self, status: HTTPStatus, body: str) -> None:
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _send_text(self, status: HTTPStatus, body: str) -> None:
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _send_sse(self) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            sequence = 0
            replay_text = cell_journal_to_sse_text(journal, limit=replay_limit, start_sequence=sequence)
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

    return BrowserViewHandler


def serve_browser_cell_view(
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
        raise ValueError("browser cell view is local-only; host must be 127.0.0.1")
    if port <= 0:
        raise ValueError("port must be > 0")

    handler = make_browser_view_handler(
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
    parser = argparse.ArgumentParser(description="Serve a read-only browser Canvas view of a missipy.cell.v1 journal.")
    parser.add_argument("--journal", required=True)
    parser.add_argument("--host", default=DEFAULT_BIND_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--tail", action="store_true")
    parser.add_argument("--replay-limit", type=int, default=None)
    parser.add_argument("--poll-seconds", type=float, default=0.50)
    parser.add_argument("--max-tail-lines", type=int, default=512)
    args = parser.parse_args()

    serve_browser_cell_view(
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
