from typing import Type, TypeVar, Tuple
from .protocols import PAwaitable, PCancelToken, PSchedulable

from functools import partial
from .cancel_token import CancelToken, ForceCancelToken
import asyncio

T = TypeVar("T", bound=PAwaitable)


class TaskBase:
    pass


class Task(TaskBase):
    def __init__(self, type: Type[T]):
        self.factory = type

    def __call__(self, *args, **kwargs) -> T:
        return self.factory(*args, **kwargs)  # type: ignore

    async def schedule(self, *args, **kwargs):
        func = self(*args, **kwargs)  # type: ignore
        return await SupervisorAsync([func]).to_executor().schedule()

    def run(self, *args, **kwargs):
        func = self(*args, **kwargs)  # type: ignore
        return SupervisorAsync([func]).to_executor().run()


class Schedulable(PSchedulable):
    def __init__(self, func):
        self.factory = func


class CancelableAsyncTask(Schedulable):
    """キャンセルトークンを受け入れることができるタスクとしてマークするためのクラス"""

    def schedule(self) -> Tuple[PCancelToken, asyncio.Task]:
        token = CancelToken()
        task = asyncio.create_task(self.factory(token))
        return token, task


class ForceCancelAsyncTask(Schedulable):
    """キャンセルトークンを受け入れできないタスクとしてマークするためのクラス。スーパーバイザーがキャンセルを検知した時、asyncioのcancel()が直接呼ばれる"""

    def schedule(self) -> Tuple[PCancelToken, asyncio.Task]:
        task = asyncio.create_task(self.factory())
        token = ForceCancelToken(task)
        return token, task
