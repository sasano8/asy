from typing import Protocol


class PCancelToken(Protocol):
    @property
    def is_canceled(self) -> bool:
        raise NotImplementedError()

    @is_canceled.setter
    def is_canceled(self, value: bool):
        raise NotImplementedError()


class PAwaitable(Protocol):
    async def __call__(self, token: PCancelToken):
        ...
