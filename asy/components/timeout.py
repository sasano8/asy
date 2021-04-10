import asyncio
from asy.exceptions import AllCancelException


class Timeout:
    def __init__(self, timeout):
        self.timeout = timeout

    async def __call__(self):
        timeout = self.timeout
        await asyncio.sleep(timeout)
        raise AllCancelException()
