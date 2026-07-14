from __future__ import annotations

import asyncio
import os
from pathlib import Path

from context.event_bus_cell_lens_live_bridge_0284 import EventBusCellLensLiveBridge
from kernel.launcher import Launcher


def _cell_lens_journal_from_env() -> Path | None:
    value = os.environ.get("MISSIPY_CELL_LENS_JOURNAL", "").strip()
    return Path(value).expanduser() if value else None


async def main() -> None:
    launcher = Launcher()
    journal_path = _cell_lens_journal_from_env()
    cell_lens_bridge = (
        EventBusCellLensLiveBridge(launcher.event_bus, journal_path)
        if journal_path is not None
        else None
    )
    if cell_lens_bridge is not None:
        await cell_lens_bridge.start()
    try:
        await launcher.boot()
    finally:
        if cell_lens_bridge is not None:
            await cell_lens_bridge.stop()


if __name__ == "__main__":
    asyncio.run(main())
