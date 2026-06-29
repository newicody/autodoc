from __future__ import annotations

import asyncio

from kernel.launcher import Launcher


async def main() -> None:
    launcher = Launcher()
    await launcher.boot()


if __name__ == "__main__":
    asyncio.run(main())
