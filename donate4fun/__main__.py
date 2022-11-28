import asyncio
import sys

from .app import main


if __name__ == '__main__':
    asyncio.run(main(sys.argv))
