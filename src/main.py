#!~/python/bin/ python3.14
import asyncio
from kernel.launcher import Launcher

async def main():
    launcher = Launcher()
    await launcher.boot()

if __name__ == "__main__":
    asyncio.run(main())
