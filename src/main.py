#!/usr/bin/env python3.14
from __future__ import annotations

import asyncio

from kernel.launcher import Launcher


async def main() -> None:
    launcher = Launcher()
    await launcher.boot(run_forever=False)


if __name__ == "__main__":
    asyncio.run(main())
