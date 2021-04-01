from typing import Type, TypeVar
from .protocols import PAwaitable
from .supervisor import SupervisorAsync


T = TypeVar("T", bound=PAwaitable)


class Task:
    def __init__(self, type: Type[T]):
        self.type = type

    def __call__(self, *args, **kwargs) -> T:
        return self.type(*args, **kwargs)  # type: ignore

    async def schedule(self, *args, **kwargs):
        func = self(*args, **kwargs)  # type: ignore
        return await SupervisorAsync([func]).to_executor().schedule()

    def run(self, *args, **kwargs):
        func = self(*args, **kwargs)  # type: ignore
        return SupervisorAsync([func]).to_executor().run()
