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


@runtime_checkable
class PAwaitable(Protocol):
    async def __call__(self, token: PCancelToken):
        ...


@runtime_checkable
class PSchedulable(Protocol):
    def schedule(self) -> Tuple[PCancelToken, asyncio.Task]:
        raise NotImplementedError()