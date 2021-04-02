from typing import Protocol, runtime_checkable, Tuple
import asyncio


@runtime_checkable
class PCancelToken(Protocol):
    @property
    def is_cancelled(self) -> bool:
        raise NotImplementedError()

    @is_cancelled.setter
    def is_cancelled(self, value: bool):
        raise NotImplementedError()


class PAwaitable(Protocol):
    async def __call__(self, token: PCancelToken):
        ...


class PSchedulable(Protocol):
    def schedule(self) -> Tuple[PCancelToken, asyncio.Task]:
        raise NotImplementedError()